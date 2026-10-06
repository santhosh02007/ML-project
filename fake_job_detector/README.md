# Veritas · Fake Job Detector

**ML PBL project:** Fake Job Posting and Recruitment Scam Detection Using Machine Learning and Natural Language Processing.

A local Python web application that checks job-posting text using TF-IDF, Logistic Regression, Random Forest and clearly labelled scam-warning rules. It helps a person decide what to investigate; it does not prove whether a job is genuine.

**ML team from the supplied poster:** V Santhosh (210425205179), Ramsankar A (210425205129). CIT Chennai · 2026–27.

## Start on Windows

1. Install **64-bit Python 3.12** and select **Add Python to PATH**. Python 3.11–3.13 is supported by the setup script; this release was tested on Python 3.12.
2. Extract the entire ZIP. Open the `FakeJobDetector` folder. Do not run inside the ZIP.
3. Double-click **SETUP_WINDOWS.bat** once. Internet is required to download the Python packages.
4. Double-click **START_WINDOWS.bat**. Keep the terminal open.
5. After the server says `Application startup complete`, open **http://127.0.0.1:8000** in Chrome, Edge or Firefox. Start with **Demo Lab**.
6. Press Ctrl+C in the terminal to stop the server.

The trained models are included. **No dataset download, retraining, Node.js, account or API key is needed to demonstrate the project.** Once dependencies are installed, the application works offline. A browser refresh does not erase saved history.

If several Python versions are installed and the setup script selects an unsupported version, run the following commands in this project folder using Python 3.12:

```bat
py -3.12 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe run.py
```

## macOS / Linux

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python run.py
```

Open http://127.0.0.1:8000. Later, `sh start.sh` starts the same environment.

## Five screens

- **Job inspector:** enter a title and description, optionally add company, email, URL, salary and extra job details. See the concern index, both model scores, direct warning phrases, domain checks and LR word contributions. Save locally or analyze without saving. Download JSON or use Print / save PDF.
- **Batch analysis:** download the sample CSV, upload up to 100 rows, see valid and invalid rows separately, then export results. Valid analyses are saved to history. Limit: 2 MB, UTF-8; `title` and `description` columns are required. Quote fields containing commas or line breaks.
- **History & review:** search and filter saved analyses, reopen complete results, export the filtered list, and add one human review with a reason. A review never changes the original model output and does not retrain a model.
- **Model lab:** compare precision, recall, F1, accuracy, average precision and confusion matrices on validation or test data. See the actual split sizes and evaluation limitations.
- **Demo Lab:** run five prepared examples through the real models and rules. They cover ordinary wording, upfront fees, OTP/PIN requests, protective warnings and a mixed warning/payment demand. Demo runs do not fill history.

## Measured ML results

The raw Kaggle / EMSCAD file has 17,880 rows. After removing short/unusable and repeated full-text inputs, 17,369 rows remain. Identical normalized description groups stay together, giving 10,421 training, 3,474 validation and 3,474 test rows. The vocabulary is fitted only on training data. Balanced class weights address class imbalance. Thresholds and the primary model are chosen using validation F1, not test results.

| Model | Test fraud precision | Test fraud recall | Test fraud F1 | Decision threshold |
| --- | ---: | ---: | ---: | ---: |
| Logistic Regression (primary) | 77.97% | 80.70% | 79.31% | 0.55 |
| Random Forest | 78.81% | 69.59% | 73.91% | 0.25 |

The test set has 3,303 genuine postings and 171 frauds. LR correctly detects 138 frauds, misses 33 and flags 39 genuine postings. **Do not present this project as 100% accurate.** Metrics above measure the two ML models, not the combined heuristic concern index. See `models/metrics.json` and `reports/split_membership.csv`.

The original project's repeated-template dataset and inconsistent model bundles were replaced by a fresh copy of the referenced public dataset and reproducibly trained models. Do not combine old model files or old accuracy claims with this release.

## Retrain (optional)

```sh
python train.py
```

Use the project environment's Python. The script reads the included `data/fake_job_postings.csv`, rebuilds `models/bundle.joblib`, `models/metrics.json`, and `reports/split_membership.csv`. Stop the application before training; restart afterwards. Training uses a fixed random seed and 20,000 TF-IDF features. Timings may differ by computer. Only load trusted local joblib models: that format can execute code when loaded.

## Tests

```sh
python -m pip install -r requirements-dev.txt
python -m pytest tests -q
```

Run from the project folder with the project environment active, or replace `python` with `.venv\Scripts\python.exe` on Windows / `.venv/bin/python` on Linux. Tests use temporary databases and the actual models. See `TEST_REPORT.md` for checks performed on this release.

## Storage and privacy

Analyses and review notes are stored in `runtime/history.sqlite3`, created at first start. Treat that file as personal data. Text is processed locally; no external AI, company registry or URL-fetch service is called. Some numeric ID/OTP/password patterns are masked before saving, but redaction is incomplete. Do not enter real secrets. Job text, contact email and company details may remain in stored records. Exported files contain the selected analysis information.

This is a **single-user local demonstration** bound to `127.0.0.1`. It has no user accounts, authentication, institutional roles or tamper-proof audit system. Do not expose the server to a public network. Completed reviews are locked in the UI/API to preserve the initial decision; the local database owner still controls the data. To start with empty demo history, stop the application and move `runtime/history.sqlite3` to a backup location.

## Limitations

- Historical, mainly English job-posting data cannot guarantee performance on current postings. Exact description duplicates are separated by group; near-duplicates and company overlap may remain.
- Rules can miss indirect requests, sarcasm, negation and new scams. A small number of romanized Tamil payment phrases are recognised by rules; this is **not** a Tamil-language ML model.
- Matching email/website domains do not prove ownership. No company existence, live reputation or company registry verification is performed.
- Salary checks use narrow illustrative thresholds, not a live salary database. The index is not a calibrated fraud probability.
- Word contributions explain Logistic Regression only. No SBERT, BERT, LIME, SHAP, browser extension or automatic retraining is implemented.

## Troubleshooting

- **Server cannot be reached:** keep the terminal open, wait for startup, and use `http://127.0.0.1:8000` (not a local HTML file).
- **Port 8000 in use:** close the other server, or Windows `set PORT=8001` / Linux `PORT=8001 .venv/bin/python run.py`. Open the matching port.
- **Missing packages:** rerun setup in the extracted project folder. Do not mix global Python with the project environment.
- **Model version warning:** reinstall the pinned requirements; bundled models use scikit-learn 1.8.0.
- **Missing models:** restore the complete ZIP or run `train.py` in the configured environment.
- **History save error:** ensure the extracted folder is writable and the disk has space. Do not launch from a read-only archive.

## Project layout

`run.py` starts the server; `veritas/server.py` defines API routes; `veritas/engine.py` runs models and rules; `veritas/storage.py` manages SQLite; `veritas/text.py` shares preprocessing with training; `veritas/samples.py` contains demo inputs; `static/` contains the responsive interface; `models/` contains fitted models and measured results; `data/` contains the training data and provenance; `tests/` contains integration checks.

## Data attribution

Source: [Real / Fake Job Posting Prediction, shivamb, Kaggle](https://www.kaggle.com/datasets/shivamb/real-or-fake-fake-jobposting-prediction), commonly described as the EMSCAD job-posting corpus. Source URL and SHA-256 are recorded in `data/provenance.json`. The dataset contains historical, user-submitted postings; labels are used for academic evaluation, not a current employer blacklist. Original dataset rights and terms remain with their respective owners.
