# A simple invigilator demonstration

Allow about five minutes. Start the server before the demonstration, open the browser and confirm **Models ready**. Use Demo Lab first so examples do not fill the history table.

## 1. Explain the project

“Our project helps people notice suspicious job offers. We give it the job title and description. Machine learning checks patterns in the text, and extra rules look for fees, secret-information requests and contact mismatches. It shows the reasons so a person can check the offer carefully.”

## 2. Demo Lab — show the difference

Select each example and click **Run analysis**. The models really run each time; these are not hard-coded model outputs.

- **Ordinary posting:** explain that fewer signals means lower concern, not confirmed genuine.
- **Upfront fee:** point out the payment wording, messaging channel, public email/domain mismatch and salary rule. The rule can raise concern even when an ML score is low.
- **OTP / PIN request:** point out the request for sensitive information. Explain why it deserves a high concern result.
- **Protective warning:** show that “never pay” and “do not share” should be treated as warnings rather than demands. The model may still react to some scam-related words; this shows why context and human review matter.
- **Mixed wording:** a reassuring sentence does not cancel a later instruction to pay. Show both the protective wording and the payment signal.

## 3. Job Inspector — explain the result

Paste a sample job description of at least 40 characters and enter a job title. Optional contact fields help the local rules. Click **Analyze posting**.

“The concern index combines different signals. It is not a percentage guarantee of fraud. These two bars are separate model scores. Logistic Regression is the primary model because it had the better validation F1. The word explanation shows which matching words pushed that model toward fraud or genuine. It does not explain Random Forest.”

Expand the explanations. Demonstrate JSON download or Print / save PDF. Check Save to history if you want a review record.

## 4. Batch Analysis — demonstrate a practical feature

Click **Download sample CSV**, then upload that file and click **Analyze file**. Show individual results and CSV export. Explain that a damaged row is reported while valid rows are processed. All valid batch rows are saved to history.

## 5. History & Review — add a human decision

Open a saved result, choose a decision, type a reason and save the review. Show that the original concern index and model scores stay the same. Search by title or filter by High concern. Explain that this is local history, not a faculty login system.

## 6. Model Lab — explain the real evaluation

“The dataset contains far more genuine jobs than frauds. A model could look accurate while missing scams, so we show fraud precision, recall and F1 together. Precision tells us how many flags are correct. Recall tells us how many frauds we catch. F1 balances those two.”

On the test set, the primary model has about **79.3% fraud F1** and **80.7% fraud recall**. It found 138 of 171 frauds, missed 33 and raised 39 false alarms. Show those numbers in the confusion matrix. Validation data selected the thresholds and primary model; test data measured the final result. Identical normalized descriptions do not cross the split boundaries.

## What makes this version useful?

It combines text-based ML with understandable warnings, compares two models, supports bulk files and persistent review, runs locally without an AI subscription, and shows its measured limitations. These are implemented features; we have not performed a head-to-head benchmark proving superiority over commercial tools.

## Likely questions

**Is this Java?** No. This is our separate ML project using Python, FastAPI, scikit-learn, SQLite, HTML, CSS and JavaScript.

**Is TF-IDF an AI model?** It converts words and short phrases into numeric features. Logistic Regression and Random Forest learn from those features.

**Why two models?** They give a useful comparison. The system does not simply average them: Logistic Regression is primary and Random Forest is displayed alongside it.

**What does balanced class weight do?** It makes mistakes on the smaller fraud class matter more during training.

**Does the tool browse the employer's website?** No. It compares supplied domain text locally. It cannot prove that a company exists or owns a domain.

**Does a review retrain it?** No. Reviews are notes only. Retraining is an explicit developer step using `train.py`.

**What remains future work?** Stronger multilingual evaluation, a verified company API, calibrated probabilities, external test data, near-duplicate removal and authenticated deployment. BERT and a browser extension are not present features.

**Does the old poster/report automatically match now?** No. The supplied poster was left unchanged. Update report claims against `PROJECT_FACTS.md`, the source code and measured results when preparing the ML report.
