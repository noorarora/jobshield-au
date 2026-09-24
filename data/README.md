# Data

The repository does **not** redistribute the full public job-posting dataset.

## Training dataset
The baseline model was trained from the public EMSCAD-derived **Real / Fake Job Posting Prediction** dataset. It contains a `fraudulent` target (`0 = legitimate`, `1 = fraudulent`) and job text fields such as `title`, `company_profile`, `description`, `requirements`, and `benefits`.

To reproduce training, place the CSV here as:

```text
data/fake_job_postings.csv
```

Then run:

```bash
python scripts/train_model.py
```

The trainer also accepts a simple CSV with:

```text
text,fraudulent
"job text...",0
"job text...",1
```

## Synthetic smoke-test data
The repository includes `scripts/generate_demo_data.py` for local pipeline smoke tests. Generated synthetic data is not used for the published model metrics and should not be presented as real-world evidence.
