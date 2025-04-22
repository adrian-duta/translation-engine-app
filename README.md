
# Translation Engine App

## Summary

The **Translation Engine App** is a powerful, web-based tool built with Streamlit that enables users to translate text or web content into multiple languages using advanced language models (LLMs) such as OpenAI's GPT-4o, DeepSeek's deepseek-reasoner, and Anthropic's Claude 3.5 Sonnet. It supports translations into Spanish, French, German, Japanese, Arabic, Hindi, and Portuguese. 

The app also includes a robust evaluation feature, allowing users to compare translations against Google Translate using metrics like BLEU, METEOR, Fluency Score, and Word Matching Percentage. Whether you're translating user-input text or scraping content from websites (e.g., BrokerChooser), this app provides a flexible and efficient solution for multilingual needs.

![App Screenshot](assets/translation_app_image.png)

**Additional Attachments and Documentation:**
- **Brief Report**: A file titled `brief_report.pdf` is provided that contains a detailed summary of the app’s performance analysis. This report is based on two complete test runs:
  1. A run using the text provided in a CSV (which includes Hungarian translation).
  2. A run using content scraped from the website.
  
  Both runs include full translations for all supported languages and models as well as evaluation metrics. The CSV files generated from these two runs are stored in the `translation_runs` folder to help you better understand the app's performance.

- **Quick Tutorial Video**: A video file named `quick_tutorial` is included to offer a visual guide on how the app looks and works, demonstrating key functionalities and user interactions.

- **App Source Files**: The repository includes all app-related Python files (e.g., `app.py`, `translation.py`, and `requirements.txt`), offering full insight into the implementation.

## Key Features

- **Text Translation**: Translate manually entered text or scraped web content into multiple languages.
- **Web Scraping**: Extract text from webpages using `undetected-chromedriver` with a fallback to `cloudscraper`.
- **Multi-Model Support**: Utilize OpenAI, DeepSeek, and Anthropic models to generate high-quality translations.
- **Evaluation Metrics**: Automatically evaluate translation quality using BLEU, METEOR, Fluency Score, and Word Matching Percentage.  
  *Note:* You must upload a CSV to use the evaluation feature. You can upload the CSV generated from the translation step or another compatible CSV created externally.
- **Cost Optimization**: Implements a language prioritization strategy based on market demand and user base.

## How It Works

The Translation Engine App operates through two primary workflows: **Translation** and **Evaluation**.

### Translation Workflow

1. **Input Selection**:  
   - **Text Input**: Enter text directly in the provided text area (e.g., "Best forex brokers in [country]").  
   - **Webpage URL**: Input a URL (default: `https://brokerchooser.com`). The app scrapes the main content using `undetected-chromedriver`. If blocked (e.g., by Cloudflare), it automatically falls back to `cloudscraper`.

2. **Model and Language Selection**:  
   Choose one or more LLMs (OpenAI, DeepSeek, Anthropic) and target languages (Spanish, French, etc.).

3. **Translation Process**:  
   The app sends the input text to the selected models via their APIs, preserving any placeholders (e.g., `[dataPoints]`, `[brokerName]`), and returns the translated text.

4. **Output and CSV Generation**:  
   The translations are displayed in a table. You can download the CSV file manually after translation is complete. This downloaded CSV can then be used for the evaluation step.

### Evaluation Workflow

1. **CSV Upload (Optional)**:  
   After downloading the CSV file from the translation step, you must upload it here for evaluation.

   Alternatively, you may upload any custom CSV if you wish to analyze translations generated outside of our app, provided the format matches.

2. **Baseline Comparison with Google Translate**:  
   The app uses Google Translate as a baseline to translate the original English text into the selected target languages.

3. **Metrics Calculation**:  
   For each translation, the app computes:
   - **BLEU Score**: Measures n-gram overlap with the baseline.
   - **METEOR Score**: Evaluates word alignment and synonym usage.
   - **Fluency Score**: Assesses length similarity between translations.
   - **Word Matching Percentage**: Calculates the percentage of shared unique words.

4. **Results**:  
   The evaluation results are presented in a table and can be downloaded as a CSV file.

## Setup and Installation

### Prerequisites
- **Python**: Version 3.8 or higher.
- **Virtual Environment**: It is recommended to use a virtual environment for dependency isolation.
- **API Keys**: Obtain API keys for OpenAI, DeepSeek, and Anthropic. Add these in a `.env` file as shown below.

### Installation Steps

### Installation Steps

1. **Clone the Repository**
   ```bash
   git clone https://github.com/yourusername/translation-engine-app.git
   cd translation-engine-app
   ```

2. **Create a Virtual Environment**
   ```bash
   python -m venv venv
   ```

3. **Activate the Virtual Environment**

   **On Windows:**
   ```bash
   .\venv\Scripts\activate
   ```

   **On macOS/Linux:**
   ```bash
   source venv/bin/activate
   ```

4. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```


5. **Configure Environment Variables**:  
   Create a `.env` file in the root directory with the following content:
   ```env
   OPENAI_API_KEY=your_openai_api_key
   DEEPSEEK_API_KEY=your_deepseek_api_key
   ANTHROPIC_API_KEY=your_anthropic_api_key
   ```

6. **Run the Application**:
   ```bash
   streamlit run app.py
   ```

7. **Access the App**:  
   Open your browser and navigate to [http://localhost:8501](http://localhost:8501).


## Using the App

### Translation Feature

1. **Choose Translation Mode**:
   - **Text Input**: For manual text entry.
   - **Webpage URL**: For scraping content from a given URL.

2. **Enter Your Input**:
   - **Text Input Mode**: Type or paste your text in the provided text area.
   - **Webpage URL Mode**: Enter the URL and click "Scrape and Preview" to extract and review the content. You can also download the scraped text if needed.

3. **Select Models and Languages**:  
   Choose one or more translation models (default: OpenAI) and target languages (default: Spanish).

4. **Translate and Download**:  
   Click "Translate" to process your input. The translations are displayed in a table. `
   
   You can manually download the CSV file after translation using the "Download Translations CSV" button. This file can be used later for visualization or evaluation steps.

### Evaluation Feature

1. **Evaluate Translations**:  
   Upload a CSV file using the upload button. 
   
   You can upload the CSV file generated during the translation step or any other CSV with the same format. The evaluation will run on the uploaded file.

2. **View and Download Metrics**:  
   The app compares the translations against Google Translate’s output and calculates evaluation metrics. Results are displayed on-screen and can be downloaded as a CSV.

## Additional Documentation

### Brief Report (`brief_report.pdf`)
- **Content**:  
  - **App Performance Analysis**: Detailed summary based on two complete runs (one with CSV text input including Hungarian translation and one with scraped content).
  - **Generated CSVs**: The CSV files from these two runs can be found in the `translation_runs` folder.
  - **Extended Discussions**: In-depth details on *Language Prioritization for Cost Optimization* and *Future Improvements for the Translation Engine*.
  - **Evaluation Methodologies**:
    - Explanation of the evaluation techniques used (BLEU, METEOR, Fluency, and Word Matching).
    - Detailed comparison of these methodologies with the Google Translate baseline.

### Quick Tutorial Video (`quick_tutorial`)
- **Content**:  
  This video demonstrates how the app looks and functions, providing a practical walkthrough of the translation and evaluation workflows.

### Generated CSVs (results) (`translation_runs folder`)
- **Content**:  
   The CSV files from the two full test runs (CSV text input and webpage scrape) can be found in the 'translation_runs' folder.
