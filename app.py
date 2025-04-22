import streamlit as st
import pandas as pd
from translation import Translator, evaluate_dataset
from dotenv import load_dotenv
import os

# load environment variables from .env file
load_dotenv()

# validate required api keys
required_keys = ["OPENAI_API_KEY", "DEEPSEEK_API_KEY", "ANTHROPIC_API_KEY"]
missing_keys = [key for key in required_keys if not os.getenv(key)]
if missing_keys:
    st.error(f"Missing API keys: {', '.join(missing_keys)}. Please check your .env file.")
    st.stop()

# initialize translator instance
translator = Translator()

# set up streamlit app title
st.title("Translation Engine App - Version 1 (API Models)")

# select translation mode: direct text input or scrape from webpage
st.header("Translation Modes")
mode = st.radio("Select Mode", ["Text Input", "Webpage URL"])

# initialize session state for scraped text
if "scraped_text" not in st.session_state:
    st.session_state.scraped_text = ""

# handle text input mode
if mode == "Text Input":
    text = st.text_area("Enter Text to Translate", "Best forex brokers in [country]")
    st.session_state.scraped_text = ""  # clear scraped text if switching to text input
else:
    # handle webpage url mode
    url = st.text_input("Enter Webpage URL to Translate", "https://brokerchooser.com")
    if st.button("Scrape and Preview"):
        # scrape text from the provided url
        with st.spinner("Scraping website..."):
            scraped_text = translator.scrape_text(url)
            if not scraped_text.startswith("Error"):
                st.session_state.scraped_text = scraped_text
                st.text_area("Preview Scraped Content", scraped_text, height=300)
                st.download_button(
                    label="Download Scraped Text",
                    data=scraped_text,
                    file_name="scraped_text.txt",
                    mime="text/plain"
                )
            else:
                st.error(scraped_text)
    text = st.session_state.scraped_text

# define available options for models and languages
available_models = ["OpenAI", "DeepSeek", "Anthropic"]
available_languages = ["Spanish", "French", "German", "Japanese", "Arabic", "Hindi", "Portuguese"]

# choose models and languages for translation
selected_models = st.multiselect("Select Models", available_models, default=["OpenAI"])
selected_languages = st.multiselect("Select Languages", available_languages, default=["Spanish"])

# perform translations and display results
if st.button("Translate"):
    if not text or text.startswith("Error"):
        st.error("Please enter valid text or scrape a webpage first.")
    else:
        results = {}
        with st.spinner("Translating..."):
            for model in selected_models:
                for lang in selected_languages:
                    translation = translator.translate(text, lang, model)
                    results[f"{model} - {lang}"] = translation
        data = {"Original Text": [text]}
        data.update(results)
        df = pd.DataFrame(data)
        st.dataframe(df)

        # offer csv download of translations
        csv = df.to_csv(index=False, encoding="utf-8-sig")
        st.download_button(
            "Download Translations CSV",
            data=csv,
            file_name="translations.csv",
            mime="text/csv"
        )

# upload translated csv and evaluate against google translate
st.header("Evaluate with Dataset")
st.markdown("""
The translations will be evaluated using the following metrics:

- BLEU
- METEOR
- Fluency
- Word Matching Percentage
""")
st.markdown("<h2>Upload your translated CSV file</h2>", unsafe_allow_html=True)

uploaded_file = st.file_uploader("", type="csv")

if uploaded_file and st.button("Evaluate Dataset"):
    with st.spinner("Evaluating translations..."):
        evaluate_dataset(uploaded_file)

# display language prioritization strategy
st.header("Language Prioritization for Cost Optimization")
st.write("Below is a brief analysis on how to prioritize languages to optimize costs. For a more detailed explanation, see *brief_report.pdf*.")
st.text_area(
    "Prioritization Strategy",
    "To optimize costs, prioritize languages based on market demand and user base. Spanish and French should be prioritized for Europe due to their widespread use and BrokerChooser's potential user base in these regions. Japanese and Hindi are key for Asia, targeting large markets in Japan and India. Portuguese can target Brazil, a significant market in South America. Arabic should be considered for the Middle East, but its complexity may increase costs. German can be deprioritized if the user base in Germany is smaller, as English often suffices there.",
    height=150
)

# list future improvements for the app
st.header("Future Improvements for the Translation Engine")
st.write("These are a few initial ideas for improving the translation engine. For a deeper discussion, refer to *brief_report.pdf*.")
st.text_area(
    "Improvement Ideas",
    "1. Implement language-specific tokenizers (e.g., MeCab for Japanese, camel-tools for Arabic) to improve evaluation accuracy.\n"
    "2. Switch to Google Cloud Translation API for more reliable baseline translations, despite higher costs.\n"
    "3. Enhance web scraping with cloudscraper to bypass anti-bot measures like Cloudflare.\n"
    "4. Add support for more languages based on user feedback.\n"
    "5. Integrate a caching mechanism to reduce API calls and costs.",
    height=150
)
