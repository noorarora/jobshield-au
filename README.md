# JobShield AU

**Explainable job-scam screening for job seekers.**

[![Live Demo](https://img.shields.io/badge/Live%20Demo-Streamlit-FF4B4B?logo=streamlit&logoColor=white)](https://jobshield-au.streamlit.app)
[![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)](https://www.python.org/)

**Try the live app:** https://jobshield-au.streamlit.app

![JobShield AU live app](docs/images/jobshield-au-live-demo.jpg)

JobShield AU analyses pasted job ads and recruiter messages using a hybrid of transparent fraud rules and an NLP classifier. Instead of returning only a label, it shows the warning signals it found, the model signal, and practical verification steps.

> **Prototype disclaimer:** JobShield AU is decision support. A high score does not prove fraud and a low score does not prove legitimacy.

## What it does

- Analyses job ads, recruiter emails, SMS and direct messages
- Flags upfront payments, cryptocurrency, urgency, private messaging apps, sensitive-ID requests and other warning signs
- Checks recruiter/company-domain context when provided
- Uses TF-IDF + Logistic Regression for an independent NLP signal
- Shows influential terms for explainability
- Combines ML and rule evidence into a screening score
- Provides clear next-step guidance instead of an accusation
- Falls back safely to rules if the ML model cannot load

## Live demo

The public prototype is deployed on Streamlit Community Cloud:

**https://jobshield-au.streamlit.app**

For a quick test, select **Load example** and then **Analyse for risk**. You can also paste your own job advertisement, recruiter email, SMS, or direct message.

No account is required to use the current prototype.

## Model result

The baseline dataset contained **17,880 labelled job postings**. Before splitting, **1,679 exact duplicate combined-text rows** were removed, leaving 16,201 unique examples. A stratified 70/15/15 train/validation/test split was used, and the decision threshold was selected on validation data only.

| Held-out test metric | Result |
|---|---:|
| Fraud precision | **87.38%** |
| Fraud recall | **81.08%** |
| Fraud F1 | **84.11%** |
| PR-AUC | **0.8971** |
| ROC-AUC | **0.9886** |
| Accuracy | **98.60%** |

Confusion matrix: `[[2307, 13], [21, 90]]`.

These results are specific to the historical public dataset and split. They are not a guarantee of performance on current real-world scams. See [MODEL_CARD.md](MODEL_CARD.md) for methodology and limitations.

## Run locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Then open the local URL printed by Streamlit (normally `http://localhost:8501`). The trained portable model is included, so no retraining is required to use the prototype.

## Quick demo

Use **Load example** in the app, or paste the example in [`examples/suspicious_recruiter_message.txt`](examples/suspicious_recruiter_message.txt), then select **Analyse for risk**.

## Retrain

The full public training CSV is not redistributed in this repository. Place a compatible file at:

```text
data/fake_job_postings.csv
```

Then run:

```bash
python scripts/train_model.py
```

The training pipeline removes exact duplicate combined-text rows before splitting, tunes the threshold on validation data, evaluates on an untouched test split, and exports the portable model used by the app.

## Project structure

```text
jobshield-au/
├── app.py
├── hybrid_engine.py
├── risk_engine.py
├── ml_model.py
├── MODEL_CARD.md
├── LICENSE
├── requirements.txt
├── VERSION
├── .streamlit/
│   └── config.toml
├── .github/workflows/
│   └── tests.yml
├── data/
│   └── README.md
├── docs/
│   └── ARCHITECTURE.md
├── examples/
│   ├── legitimate_job_posting.txt
│   └── suspicious_recruiter_message.txt
├── models/
│   ├── portable_tfidf_logreg.joblib
│   └── metrics.json
├── scripts/
│   ├── generate_demo_data.py
│   └── train_model.py
└── tests/
```

## Detection architecture

```text
Pasted job/recruiter text
        |                 \
        v                  v
 Explainable rules     TF-IDF + Logistic Regression
        |                  |
        +--------+---------+
                 v
        Hybrid screening score
                 |
                 v
   Risk signals + explanation + next steps
```

More detail: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Tests

```bash
pytest -q
```

GitHub Actions is included and runs the test suite on Python 3.11 and 3.12.

## Tech stack

Python · Streamlit · pandas · NumPy · scikit-learn · TF-IDF · Logistic Regression · joblib

## Deployment

The current public prototype is deployed on **Streamlit Community Cloud** from the `main` branch. Updates pushed to the repository can be redeployed to the live app.

## Current scope

JobShield currently analyses **text supplied by the user**. It does not automatically scrape SEEK/LinkedIn, prove recruiter identity, or independently verify a company. Those are intentionally presented as future work rather than existing functionality.

## Roadmap

- Australian-specific evaluation set
- Job URL ingestion where permitted
- Recruiter/company verification workflow
- Official careers-page checks
- Screenshot/message analysis
- Sensitive-information warnings
- Modern embedding-model benchmark
- Improved public-demo monitoring and feedback collection

## License

MIT — see [LICENSE](LICENSE).
