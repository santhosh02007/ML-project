import pytest
from app.services.rule_engine import RuleEngine


def test_rule_registration_fee():
    text = "To start your employment, please pay a registration fee of $150 to activate your employee ID."
    res = RuleEngine.evaluate(text)
    
    assert res["rule_score"] >= 35
    assert any(r["rule_id"] == "PAY_001" for r in res["triggered_rules"])
    assert len(res["matched_snippets"]) > 0


def test_rule_equipment_deposit():
    text = "A refundable security deposit for laptop and home office supplies is required."
    res = RuleEngine.evaluate(text)
    
    assert res["rule_score"] >= 35
    assert any(r["rule_id"] == "PAY_002" for r in res["triggered_rules"])


def test_rule_cashier_check_wire():
    text = "We will send you a cashier check. Deposit the check in your account and send excess funds via wire transfer."
    res = RuleEngine.evaluate(text)
    
    assert res["rule_score"] >= 40
    assert any(r["rule_id"] == "PAY_003" for r in res["triggered_rules"])


def test_rule_telegram_interview():
    text = "Connect immediately with our hiring manager on Telegram: @GlobalRecruitmentHub."
    res = RuleEngine.evaluate(text)
    
    assert res["rule_score"] >= 25
    assert any(r["rule_id"] == "COMM_001" for r in res["triggered_rules"])


def test_rule_otp_sensitive_info():
    text = "Candidate verification step: send your OTP and Aadhaar card copy to confirm offer letter."
    res = RuleEngine.evaluate(text)
    
    assert res["rule_score"] >= 30
    assert any(r["rule_id"] == "PII_002" for r in res["triggered_rules"])


def test_rule_tamil_english_scam():
    text = "Veettil irundhe sambalam peruga. Daily 3000 rupees direct payment. Joining fee kattavum and send OTP."
    res = RuleEngine.evaluate(text)
    
    assert res["rule_score"] >= 30
    assert any(r["rule_id"] == "MULTI_001" for r in res["triggered_rules"])
