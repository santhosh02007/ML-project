import sys
import traceback
from pathlib import Path

# Add backend to sys.path
backend_dir = Path(__file__).resolve().parent / "backend"
sys.path.insert(0, str(backend_dir))

def run_tests():
    from tests import (
        test_ml_models,
        test_rule_engine,
        test_negation_disclaimer,
        test_url_email_verifier,
        test_salary_analyzer,
        test_scenarios,
        test_api
    )
    from app.services.risk_engine import RiskEngine
    engine_fixture = RiskEngine.get_instance()

    test_modules = [
        ("ML Models", test_ml_models, [
            test_ml_models.test_text_cleaner_preserves_fraud_tokens,
            test_ml_models.test_text_cleaner_strips_html_and_standard_stopwords,
            test_ml_models.test_ml_inference_engine_prediction,
            test_ml_models.test_ml_predict_job,
        ]),
        ("Rule Engine", test_rule_engine, [
            test_rule_engine.test_rule_registration_fee,
            test_rule_engine.test_rule_equipment_deposit,
            test_rule_engine.test_rule_cashier_check_wire,
            test_rule_engine.test_rule_telegram_interview,
            test_rule_engine.test_rule_otp_sensitive_info,
            test_rule_engine.test_rule_tamil_english_scam,
        ]),
        ("Negation & Disclaimers", test_negation_disclaimer, [
            test_negation_disclaimer.test_anti_scam_disclaimer_not_falsely_flagged,
            test_negation_disclaimer.test_anti_scam_disclaimer_in_full_job_analysis,
        ]),
        ("URL & Email Verifier", test_url_email_verifier, [
            test_url_email_verifier.test_url_analyzer_flags_insecure_and_suspicious_tld,
            test_url_email_verifier.test_url_analyzer_flags_ip_address_host,
            test_url_email_verifier.test_url_analyzer_flags_shortener,
            test_url_email_verifier.test_company_verifier_detects_brand_impersonation_with_free_email,
            test_url_email_verifier.test_company_verifier_verifies_matching_corporate_domain,
        ]),
        ("Salary Analyzer", test_salary_analyzer, [
            test_salary_analyzer.test_salary_standard_within_range,
            test_salary_analyzer.test_salary_exorbitant_entry_level_anomaly,
            test_salary_analyzer.test_salary_hourly_anomaly_for_typing,
        ]),
        ("7 Real-World Scenarios", test_scenarios, [
            lambda: test_scenarios.test_scenario_1_genuine_job(engine_fixture),
            lambda: test_scenarios.test_scenario_2_registration_fee_scam(engine_fixture),
            lambda: test_scenarios.test_scenario_3_unrealistic_salary_no_experience(engine_fixture),
            lambda: test_scenarios.test_scenario_4_company_impersonation(engine_fixture),
            lambda: test_scenarios.test_scenario_5_rephrased_scam_wording(engine_fixture),
            lambda: test_scenarios.test_scenario_6_legitimate_anti_scam_disclaimer(engine_fixture),
            lambda: test_scenarios.test_scenario_7_tamil_english_code_mixed(engine_fixture),
        ]),
        ("FastAPI Endpoints", test_api, [
            test_api.test_api_health,
            test_api.test_api_samples,
            test_api.test_api_analyze_job,
            test_api.test_api_report_job_and_verify,
            test_api.test_api_model_info_and_dashboard,
        ])
    ]

    total_passed = 0
    total_failed = 0
    print("\n" + "="*80, flush=True)
    print("STARTING TEST RUNNER - FAKE JOB POSTING & RECRUITMENT SCAM DETECTOR", flush=True)
    print("="*80, flush=True)

    for suite_name, module, tests in test_modules:
        print(f"\n[SUITE] {suite_name}:", flush=True)
        for fn in tests:
            test_name = getattr(fn, "__name__", str(fn))
            try:
                fn()
                print(f"  [PASS] {test_name}", flush=True)
                total_passed += 1
            except Exception as e:
                print(f"  [FAIL] {test_name}: {e}", flush=True)
                traceback.print_exc()
                total_failed += 1

    print("\n" + "="*80, flush=True)
    print(f"SUMMARY: {total_passed} PASSED, {total_failed} FAILED (TOTAL: {total_passed + total_failed})", flush=True)
    print("="*80 + "\n", flush=True)
    return total_failed == 0

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
