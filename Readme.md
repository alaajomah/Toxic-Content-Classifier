# 🛡️ Toxic Content Classifier

A Streamlit app that classifies text and images for unsafe/toxic content using **Llama Guard 3** (via Ollama) and **BLIP** image captioning. Every submission and its classification result is logged to a CSV-backed database that can be browsed, filtered, and exported directly from the app.

## Features

- **Text classification** : paste any text and classify it as `safe`, `unsafe`, or `unknown`, with detected hazard categories (e.g. Violent Crimes, Hate, Sexual Content) based on the MLCommons taxonomy.
- **Image classification** : upload an image, generate a caption with BLIP, then classify that caption for safety.
- **Persistent database** : every submission is appended to `data/classifications.csv` with a timestamp, input type, content, classification label, and category.
- **Database browser** : view, filter (by classification or category), and download stored entries as CSV directly in the app.


## Project structure

```
Toxic-Content-Classifier/
├── app.py                    # Streamlit UI
├── classifier.py             # sends text to the `llama-guard3:8b` model via [Ollama](https://ollama.com) and parses the `safe`/`unsafe` verdict plus hazard category codes.
├── imagecaption.py           # upload an image, generate a caption with BLIP
├── database.py               # reads/writes classification results to `data/classifications.csv` using pandas.
├── data/
│   └── classifications.csv   # Logged submissions & results
└── requirements.txt
```

## Project flow 

                    ┌────────────────────────┐        ┌────────────────────────┐    
                    │      User image        │        │       User Text        │
                    └───────────┬────────────┘        └───────────┬────────────┘ 
                                │                                 |
                                ▼                                 |
                    ┌────────────────────────┐                    |
                    │          BLIP          │                    |
                    │    Image Captioning    │                    |
                    └───────────┬────────────┘                    |
                                │                                 |
                                ▼                                 |
                    ┌────────────────────────┐                    |
                    │   Generated Caption    │                    |
                    └───────────┬────────────┘                    |
                                │                                 |
                                |                                 | 
                                │                                 |
                                ▼                                 |
                ┌──────────────────────────────────┐              |
                │      Toxic Text Classifier       |───────────────
                │     (Llama Guard 3 / Ollama)     │
                └────────────────┬─────────────────┘
                                 │
                                 ▼
                ┌────────────────────────────────┐
                │  Hazard Category Prediction      │
                │   (S1–S14, MLCommons taxonomy)   │
                └────────────────┬─────────────────┘
                                 │
                                 ▼
                    ┌──────────────────────┐
                    │  database.csv (CSV)  │
                    └──────────────────────┘
     
## Requirements

- Python 3.9+
- [Ollama](https://ollama.com) installed and running locally, with the Llama Guard 3 model pulled:
  ```bash
  ollama pull llama-guard3:8b
  ```

## Installation

```bash
git clone https://github.com/alaajomah/Toxic-Content-Classifier.git
cd Toxic-Content-Classifier
pip install -r requirements.txt
```

## Usage

1. Make sure Ollama is running and the `llama-guard3:8b` model is available:
   ```bash
   ollama serve
   ```
2. Launch the app:
   ```bash
   streamlit run app.py
   ```
3. Open the URL Streamlit prints (usually `http://localhost:8501`) in your browser.
4. In the **Submit** tab, either:
   - Enter text and click **Classify Text**, or
   - Upload an image and click **Caption & Classify Image**.
5. Switch to the **View Database** tab to browse, filter, and download all past classifications.

## Hazard categories

Classifications use the Llama Guard 3 / MLCommons hazard taxonomy:

| Code | Category | Code | Category |
|------|----------|------|----------|
| S1 | Violent Crimes | S8 | Intellectual Property |
| S2 | Non-Violent Crimes | S9 | Indiscriminate Weapons |
| S3 | Sex Crimes | S10 | Hate |
| S4 | Child Sexual Exploitation | S11 | Suicide & Self-Harm |
| S5 | Defamation | S12 | Sexual Content |
| S6 | Specialized Advice | S13 | Elections |
| S7 | Privacy | S14 | Code Interpreter Abuse |



## Notes

- The first run will download the BLIP model weights (~1.9 GB) from Hugging Face, which may take a few minutes.
- All classification data is stored locally in `data/classifications.csv`; no data is sent anywhere besides your local Ollama instance and, for image captioning, the Hugging Face model runs locally as well.
