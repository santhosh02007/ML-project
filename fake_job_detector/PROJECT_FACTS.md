# Facts for the next ML report

Use this as a source checklist when writing the report; it is not the formatted PBL report. The ML poster and all Java files were left unchanged.

- Project: Fake Job Posting and Recruitment Scam Detection Using Machine Learning and Natural Language Processing.
- Team: V Santhosh (210425205179), Ramsankar A (210425205129), from the supplied ML poster.
- Interface brand: Veritas. Five screens: Job Inspector, Batch Analysis, History & Review, Model Lab, Demo Lab.
- Runtime: Python + FastAPI with a local HTML/CSS/JavaScript frontend. No React build or separate Flask server is needed in this edition.
- Storage: SQLite local analysis/review history. Trained models are stored separately in joblib. JSON metrics and CSV split membership are included.
- ML input: title, company profile, description, requirements, benefits and location, joined and normalized using shared training/inference code.
- Features: TF-IDF unigrams/bigrams, max 20,000 features, sublinear term frequency, minimum document frequency 2, no stop-word removal.
- Models: Logistic Regression with balanced class weights (C=2, liblinear) and Random Forest (180 trees, balanced class weights), fixed seed 42.
- Source: fresh Kaggle / EMSCAD dataset, 17,880 rows. Usable after preprocessing/deduplication: 17,369. See provenance for file hash.
- Split: grouped by normalized description, approximately 60% train / 20% validation / 20% test. Actual counts: 10,421 / 3,474 / 3,474. No exact normalized description group crosses these splits. No claim that all near-duplicates or company overlap were removed.
- Model/threshold selection: validation F1. Logistic Regression threshold 0.55; Random Forest 0.25. Primary: Logistic Regression.
- LR test results: precision 0.77966, recall 0.80702, F1 0.79310, accuracy 0.97927; true negatives 3264, false positives 39, false negatives 33, true positives 138.
- RF test results: precision 0.78808, recall 0.69591, F1 0.73913, accuracy 0.97582; true negatives 3271, false positives 32, false negatives 52, true positives 119.
- Rules: payment demands, sensitive-information demands, check/transfer arrangements, pressure and messaging-only contact; limited clause-based negation; supplied email/website domain mismatch; narrow illustrative salary thresholds.
- Concern index: round(0.65 × primary model score + 0.25 × wording score + 0.10 × domain score + 0.20 × salary score), then rule-based floors and cap at 100. All component scores here use a 0–100 scale. A primary-model flag floors it at 61; credential/check signals or wording score ≥70 floor it at 80; payment floors it at 65; another wording signal or domain score ≥30 floors it at 35. Low <31, Medium 31–60, High ≥61. This is an uncalibrated heuristic, not a probability. Its weights/floors were not benchmarked as a third ML model.
- Explainability: signed TF-IDF × LR coefficient word/phrase contributions. No claims of RF feature explanation, LIME, SHAP or SBERT.
- Privacy: inference is local; limited pattern-based secret redaction before saving. No comprehensive anonymization claim.
- Reviews: one human review per saved record; original prediction preserved. No automatic retraining, identity verification or role-based authentication.
- Demo scenarios: handwritten teaching examples evaluated by the actual engine, separate from held-out evaluation. They are not evidence of general-world accuracy.
- Future work: broader language support, stronger generalization evaluation, authenticated hosting, calibrated scores, company verification API and browser extension.

Do not claim 100% accuracy, all-company verification, full Tamil-language support, deep learning or commercial superiority. Do not reuse any Java attendance descriptions or team members in this ML report.
