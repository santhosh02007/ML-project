import pytest
from app.ml.preprocessor import TextCleaner, FRAUD_PRESERVED_TOKENS, build_combined_text_from_dict
from app.ml.inference import MLInferenceEngine


def test_text_cleaner_preserves_fraud_tokens():
    text = "Please pay a small registration fee and security deposit via wire transfer or telegram."
    cleaned = TextCleaner.clean(text)
    
    # Assert fraud keywords are preserved
    assert "pay" in cleaned
    assert "fee" in cleaned
    assert "deposit" in cleaned
    assert "wire" in cleaned
    assert "telegram" in cleaned


def test_text_cleaner_strips_html_and_standard_stopwords():
    text = "<p>This is a job with <b>the</b> company about something.</p>"
    cleaned = TextCleaner.clean(text)
    
    assert "<p>" not in cleaned
    assert "<b>" not in cleaned
    # 'this', 'is', 'with', 'the', 'about' are standard stopwords
    assert "company" in cleaned
    assert "something" in cleaned


def test_ml_inference_engine_prediction():
    engine = MLInferenceEngine.get_instance()
    assert engine.is_loaded is True
    
    # Test scam-like text
    scam_text = "Urgent data entry typist needed. Daily wire transfer $500 payout via telegram cashier check."
    res = engine.predict_text(scam_text)
    
    assert "fraud_probability" in res
    assert 0.0 <= res["fraud_probability"] <= 1.0
    assert "is_fraud" in res
    assert "top_features" in res
    assert isinstance(res["top_features"], list)


def test_ml_predict_job():
    engine = MLInferenceEngine.get_instance()
    job_dict = {
        "title": "Software Engineer",
        "company": "Tech Corp",
        "description": "Develop high-scale backend services using Python and Kubernetes.",
        "requirements": "3+ years Python experience.",
        "benefits": "Health, 401k."
    }
    res = engine.predict_job(job_dict)
    assert res["fraud_probability"] <= 0.5
