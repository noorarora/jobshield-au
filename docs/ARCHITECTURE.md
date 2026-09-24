# JobShield AU architecture

```text
User text + optional verification context
                |
                v
      +--------------------+
      | Rule-based signals |
      +--------------------+
                |
                +-------------------+
                                    |
User text                           v
   |                    +------------------------+
   v                    | Hybrid screening score |
+------------------+    +------------------------+
| TF-IDF features  |                |
+------------------+                v
   |                          Risk level +
   v                          explanations +
+------------------+          next-step guidance
| Logistic model   |
+------------------+
   |
   v
Fraud probability + influential terms
```

## Why hybrid?
The ML model captures statistical language patterns from labelled job postings, while the rule engine keeps high-value warning signs visible and auditable (for example, upfront payments, cryptocurrency, private messaging apps, identity-document requests and domain mismatches).

The combined score is a **screening indicator**, not a calibrated probability of fraud and not proof that a person or listing is fraudulent.

## Model lifecycle
1. Load labelled data.
2. Combine supported text fields.
3. Remove exact duplicate combined-text rows before splitting.
4. Create stratified train/validation/test splits.
5. Fit TF-IDF + class-balanced Logistic Regression.
6. Select the decision threshold on validation data only.
7. Evaluate once on the held-out test set.
8. Export a portable inference bundle for the Streamlit app.
