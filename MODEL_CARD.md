# JobShield AU — Baseline Model Card

## Purpose
JobShield AU uses a text classifier as one component of an explainable job-scam screening system. The model is intended to surface risk signals for further verification, not to make a definitive fraud determination.

## Dataset
The baseline was trained from the public EMSCAD/Kaggle-compatible fake-job-posting dataset supplied by the project owner.

- Raw rows: 17,880
- Raw legitimate rows: 17,014
- Raw fraudulent rows: 866
- Exact duplicate combined-text rows removed before splitting: 1,679
- Unique rows used for modelling: 16,201
- Unique legitimate rows: 15,465
- Unique fraudulent rows: 736

Exact duplicate text groups had consistent labels. Deduplication was performed before data splitting to reduce leakage from repeated postings.

## Split strategy
A stratified 70/15/15 train/validation/test split was used with random seed 42.

- Train: 11,340 rows (515 fraudulent)
- Validation: 2,430 rows (110 fraudulent)
- Test: 2,431 rows (111 fraudulent)

The probability threshold was selected only on the validation split by maximising fraud-class F1. The test split was not used for threshold selection.

## Model
- TF-IDF word features
- Unigrams + bigrams
- Up to 30,000 features
- Logistic Regression
- Balanced class weights

## Locked test-set result
Decision threshold: **0.62**

| Metric | Result |
|---|---:|
| Fraud precision | 0.8738 |
| Fraud recall | 0.8108 |
| Fraud F1 | 0.8411 |
| Fraud F2 | 0.8227 |
| PR-AUC | 0.8971 |
| ROC-AUC | 0.9886 |
| Accuracy | 0.9860 |

Confusion matrix `[[TN, FP], [FN, TP]]`:

```text
[[2307, 13],
 [  21, 90]]
```

These figures are held-out results for this historical dataset and split. They are not a guarantee of current real-world scam-detection performance.

## Explainability
For each analysed text, the app can show the highest positive TF-IDF feature contributions to the Logistic Regression fraud score. These contributions are useful for transparency but are not causal explanations.

## Known limitations
- Dataset language and scam patterns may be dated.
- Dataset is not Australia-specific.
- The model only sees pasted text; it does not independently verify people or organisations.
- The classifier may produce false positives and false negatives.
- The probability score should not be interpreted as proof of fraud.

## Planned improvements
- Australian-specific evaluation set
- URL/domain reputation checks
- Company/recruiter verification workflow
- Modern embedding-model benchmark
- Calibration analysis
- Browser extension and hosted deployment
