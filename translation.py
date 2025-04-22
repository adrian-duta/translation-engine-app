import re
import pandas as pd
import nltk
import logging
import time
from functools import wraps
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.translate.bleu_score import sentence_bleu
from nltk.translate.meteor_score import meteor_score
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import openai
import anthropic
import streamlit as st
import os
import undetected_chromedriver as uc
from deep_translator import GoogleTranslator
import cloudscraper

# download required nltk resources silently
nltk.download("punkt", quiet=True)
nltk.download("punkt_tab", quiet=True)
nltk.download("wordnet", quiet=True)
nltk.download("omw-1.4", quiet=True)

# configure logging for debugging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("translation_debug.log"),
        logging.StreamHandler()
    ]
)

# define retry decorator for robust api calls
def retry(retries=3, delay=5):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            attempt = 0
            while attempt < retries:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    attempt += 1
                    if attempt == retries:
                        logging.error(f"Failed after {retries} attempts in {func.__name__}: {e}")
                        raise Exception(f"Failed after {retries} attempts: {e}")
                    logging.warning(f"Attempt {attempt} failed for {func.__name__}: {e}. Retrying in {delay * (2 ** attempt)}s...")
                    time.sleep(delay * (2 ** attempt))
        return wrapper
    return decorator

# initialize api clients with environment variables
openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
deepseek_client = openai.OpenAI(api_key=os.getenv("DEEPSEEK_API_KEY"), base_url="https://api.deepseek.com/v1")
anthropic_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# translator class to handle translations using different models
class Translator:
    MODELS = {
        "OpenAI": {"client": openai_client, "model": "gpt-4o"},
        "DeepSeek": {"client": deepseek_client, "model": "deepseek-reasoner"},
        "Anthropic": {"client": anthropic_client, "model": "claude-3-5-sonnet-20240620"}
    }

    # translate text to the specified language using the given model
    def translate(self, text, lang, model_name):
        """Translate text to the specified language using the given model."""
        if model_name not in self.MODELS:
            logging.error(f"Invalid model name: {model_name}")
            return f"Error: Invalid model name {model_name}"

        client = self.MODELS[model_name]["client"]
        model = self.MODELS[model_name]["model"]

        # preserve placeholders before translation
        text_no_ph, placeholders = self._preserve_placeholders(text)
        prompt = f"Translate the following text to {lang}, preserving all placeholders (e.g., [dataPoints], [brokerName]) exactly as they appear: '{text_no_ph}'"

        logging.info(f"Translating with {model_name} to {lang}: '{text_no_ph}'")

        try:
            translation = self._call_api(client, model, prompt, model_name)
            # ensure proper encoding of translation
            translation = translation.encode().decode('utf-8', errors='replace')
            restored_translation = self._restore_placeholders(translation, placeholders)
            logging.info(f"Translation successful: '{restored_translation}'")
            return restored_translation
        except Exception as e:
            logging.error(f"Translation failed for {model_name} to {lang}: {e}")
            return f"Error: {str(e)}"

    # helper method to make api calls with retry logic
    @retry()
    def _call_api(self, client, model, prompt, model_name):
        """Helper method to make API calls with retry logic."""
        if model_name in ["OpenAI", "DeepSeek"]:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}]
            )
            response_text = response.choices[0].message.content
        elif model_name == "Anthropic":
            response = client.messages.create(
                model=model,
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}]
            )
            response_text = response.content[0].text if isinstance(response.content, list) else response.content
        
        # remove any notes section from response
        translation = re.sub(r'### Notes:.*$', '', response_text, flags=re.DOTALL).strip()
        return translation

    # replace placeholders with temporary markers
    def _preserve_placeholders(self, text):
        """Replace placeholders with temporary markers."""
        placeholders = re.findall(r"\[.*?\]", text)
        for i, ph in enumerate(placeholders):
            text = text.replace(ph, f"__PH{i}__")
        return text, placeholders

    # restore original placeholders in translated text
    def _restore_placeholders(self, text, placeholders):
        """Restore original placeholders in the translated text."""
        for i, ph in enumerate(placeholders):
            text = text.replace(f"__PH{i}__", ph)
        return text

    # scrape text content from a webpage url, focusing on main content
    def scrape_text(self, url):
        """Scrape text content from a webpage URL, focusing on main content."""
        # attempt scraping with undetected-chromedriver first
        logging.info(f"Attempting to scrape {url} with undetected-chromedriver")
        options = Options()
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1920,1080")

        try:
            driver = uc.Chrome(options=options)
            driver.set_page_load_timeout(60)
            driver.get(url)
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            time.sleep(5)  # allow time for cloudflare verification
            html = driver.page_source
            if "Verify you are human" in html:
                logging.warning(f"Cloudflare verification detected with undetected-chromedriver at {url}")
                raise WebDriverException("Cloudflare verification detected")
            soup = BeautifulSoup(html, "html.parser")
            main_content = soup.find('main') or soup.find('article') or soup.find('body')
            text = main_content.get_text(separator=' ', strip=True) if main_content else soup.get_text(separator=' ', strip=True)
            text = ' '.join(text.split())
            if not text:
                logging.warning(f"No content found with undetected-chromedriver at {url}")
                raise ValueError("No content found")
            logging.info(f"Successfully scraped content with undetected-chromedriver from {url}")
            return text
        except Exception as e:
            logging.error(f"undetected-chromedriver failed for {url}: {e}")
        finally:
            if 'driver' in locals():
                driver.quit()

        # fallback to cloudscraper if chromedriver fails
        logging.info(f"Falling back to cloudscraper for {url}")
        try:
            scraper = cloudscraper.create_scraper()
            response = scraper.get(url)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                main_content = soup.find('main') or soup.find('article') or soup.find('body')
                text = main_content.get_text(separator=' ', strip=True) if main_content else soup.get_text(separator=' ', strip=True)
                text = ' '.join(text.split())
                if not text:
                    logging.warning(f"No content found with cloudscraper at {url}")
                    return "Error: No content found."
                logging.info(f"Successfully scraped content with cloudscraper from {url}")
                return text
            else:
                logging.error(f"cloudscraper failed with status code {response.status_code} for {url}")
                return f"Error: HTTP {response.status_code}"
        except Exception as e:
            logging.error(f"cloudscraper failed for {url}: {e}")
            return f"Error: {str(e)}"

# evaluate translations in csv against google translate
def evaluate_dataset(uploaded_file):
    """Evaluate translations in the uploaded CSV against Google Translate."""
    # load csv file
    try:
        df = pd.read_csv(uploaded_file)
        logging.info("Successfully loaded CSV for evaluation")
    except Exception as e:
        logging.error(f"Error reading CSV file: {e}")
        st.error(f"Error reading CSV file: {str(e)}")
        return

    # validate first column name
    english_column = df.columns[0]
    if english_column not in ["Original Text", "English"]:
        logging.error(f"Invalid first column: {english_column}")
        st.error("The first column should be 'Original Text' or 'English'.")
        return

    translation_columns = df.columns[1:]
    evaluation_data = []
    # map language names to google translate codes
    language_codes = {
        "Spanish": "es", "French": "fr", "German": "de", "Japanese": "ja",
        "Arabic": "ar", "Hindi": "hi", "Portuguese": "pt"
    }
    total_rows = len(df)
    progress_bar = st.progress(0)

    # iterate over each row and column for evaluation
    for index, row in df.iterrows():
        english_text = row[english_column]
        logging.debug(f"Evaluating row {index + 1}/{total_rows}: '{english_text}'")
        for col in translation_columns:
            parts = col.split(" - ")
            if len(parts) != 2:
                logging.warning(f"Invalid column name format: {col}")
                st.warning(f"Invalid column name format: {col}. Skipping.")
                continue
            model, lang_name = parts
            if lang_name not in language_codes:
                logging.warning(f"Unknown language: {lang_name}")
                st.warning(f"Unknown language: {lang_name}. Skipping.")
                continue
            lang_code = language_codes[lang_name]
            app_translation = str(row[col])

            if app_translation.startswith("Error"):
                logging.warning(f"Skipping evaluation for {col} due to translation error: {app_translation}")
                continue

            # get google translate baseline
            try:
                translator = GoogleTranslator(source='en', target=lang_code)
                sentences = sent_tokenize(english_text)
                translated_sentences = [translator.translate(sentence) for sentence in sentences]
                google_translation = ' '.join(translated_sentences)
                logging.debug(f"Google Translate for {lang_name}: '{google_translation}'")
            except Exception as e:
                logging.error(f"Google Translate error for {lang_name}: {e}")
                st.error(f"Error translating with Google Translate for {lang_name}: {str(e)}")
                continue

            # tokenize translations for scoring
            try:
                app_tokens = word_tokenize(app_translation.lower())
                google_tokens = word_tokenize(google_translation.lower())
            except Exception as e:
                logging.error(f"Tokenization failed for {col}: {e}")
                st.warning(f"Tokenization failed for {col}: {str(e)}. Skipping.")
                continue

            # compute bleu score
            try:
                bleu = sentence_bleu([google_tokens], app_tokens)
                logging.debug(f"BLEU score for {col}: {bleu}")
            except Exception as e:
                logging.error(f"BLEU computation failed for {col}: {e}")
                bleu = f"Error: {str(e)}"

            # compute meteor score
            try:
                meteor = meteor_score([google_tokens], app_tokens)
                logging.debug(f"METEOR score for {col}: {meteor}")
            except Exception as e:
                logging.error(f"METEOR computation failed for {col}: {e}")
                meteor = f"Error: {str(e)}"

            # calculate fluency score based on word count ratio
            wc_app = len(app_tokens)
            wc_google = len(google_tokens)
            fluency_score = min(wc_app / wc_google, wc_google / wc_app) if wc_app > 0 and wc_google > 0 else 0
            logging.debug(f"Fluency score for {col}: {fluency_score}")

            # calculate word matching percentage
            app_words = set(app_tokens)
            google_words = set(google_tokens)
            intersection = app_words.intersection(google_words)
            word_matching = len(intersection) / len(app_words) if len(app_words) > 0 else 0
            logging.debug(f"Word Matching for {col}: {word_matching}")

            evaluation_data.append({
                "English Text": english_text,
                "Model": model,
                "Language": lang_name,
                "Application Translation": app_translation,
                "Google Translate Translation": google_translation,
                "BLEU Score": bleu,
                "METEOR Score": meteor,
                "Fluency Score": fluency_score,
                "Word Matching Percentage": word_matching
            })

        # update progress bar
        progress_bar.progress((index + 1) / total_rows)

    # display and offer download of evaluation results
    if evaluation_data:
        evaluation_df = pd.DataFrame(evaluation_data)
        st.dataframe(evaluation_df)
        csv = evaluation_df.to_csv(index=False, encoding="utf-8-sig")
        st.download_button(
            "Download Evaluation CSV",
            data=csv,
            file_name="evaluation.csv",
            mime="text/csv"
        )
        logging.info("Evaluation completed and results saved")
    else:
        logging.warning("No evaluation data generated")
        st.warning("No evaluation data generated.")