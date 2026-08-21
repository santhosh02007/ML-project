import React from 'react';
import { BrainCircuit, BookCheck, Building2, Globe2, DollarSign, CheckCircle2 } from 'lucide-react';

export default function SignalCards({ breakdown = {}, signals = {} }) {
  const mlSignal = signals.ml_model || {};
  const ruleSignal = signals.rules || {};
  const companySignal = signals.company || {};
  const urlSignal = signals.url || {};
  const salarySignal = signals.salary || {};

  const getStatusBadge = (score) => {
    if (score >= 60) {
      return {
        className: 'bg-rose-50 text-rose-600 border border-rose-200 font-semibold',
        text: 'High Risk'
      };
    }
    if (score >= 30) {
      return {
        className: 'bg-amber-50 text-amber-600 border border-amber-200 font-semibold',
        text: 'Medium Risk'
      };
    }
    return {
      className: 'bg-green-50 text-green-600 border border-green-200 font-semibold',
      text: 'Low Risk'
    };
  };

  const mlScore = breakdown.ml_score || 0;
  const ruleScore = breakdown.rule_score || 0;
  const urlScore = breakdown.url_risk_score || 0;

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3.5 mt-4">
      
      {/* 1. Machine Learning Signal */}
      <div className="bg-white rounded-xl border border-gray-200 p-4 shadow-2xs hover:border-orange-300 transition-all flex flex-col justify-between gap-2.5">
        <div>
          <div className="flex items-center justify-between gap-2 mb-2">
            <div className="flex items-center gap-2 font-bold text-sm text-gray-900">
              <BrainCircuit className="w-4 h-4 text-orange-500" />
              <span>Text ML Model</span>
            </div>
            <span className={`text-[11px] px-2 py-0.5 rounded-full ${getStatusBadge(mlScore).className}`}>
              {mlScore}% Fraud Prob
            </span>
          </div>
          <div className="text-xs text-gray-500">
            Model: <strong className="text-gray-800">{mlSignal.model_used || 'TF-IDF Champion'}</strong> ({mlSignal.inference_time_ms || 4}ms)
          </div>
        </div>

        {mlSignal.top_features && mlSignal.top_features.length > 0 ? (
          <div>
            <div className="text-[10px] text-gray-400 font-bold uppercase tracking-wider mb-1">Top Features:</div>
            <div className="flex flex-wrap gap-1">
              {mlSignal.top_features.slice(0, 4).map((f, i) => (
                <span key={i} className="text-[10px] bg-orange-50 text-orange-700 border border-orange-200 px-1.5 py-0.5 rounded font-mono font-medium">
                  {f.term} ({f.weight > 0 ? `+${f.weight}` : f.weight})
                </span>
              ))}
            </div>
          </div>
        ) : (
          <div className="text-xs text-gray-400">No strong scam vocabulary weights.</div>
        )}
      </div>

      {/* 2. Domain Rule Engine Signal */}
      <div className="bg-white rounded-xl border border-gray-200 p-4 shadow-2xs hover:border-orange-300 transition-all flex flex-col justify-between gap-2.5">
        <div>
          <div className="flex items-center justify-between gap-2 mb-2">
            <div className="flex items-center gap-2 font-bold text-sm text-gray-900">
              <BookCheck className="w-4 h-4 text-orange-500" />
              <span>Domain Rule Engine</span>
            </div>
            <span className={`text-[11px] px-2 py-0.5 rounded-full ${getStatusBadge(ruleScore).className}`}>
              Score: {ruleScore}/100
            </span>
          </div>
          <div className="text-xs text-gray-500">
            {ruleSignal.triggered_rules?.length > 0 ? (
              <span className="text-rose-600 font-semibold">{ruleSignal.triggered_rules.length} High-Risk Trigger(s) Fired</span>
            ) : (
              <span className="text-green-600 font-semibold">No scam rule violations found</span>
            )}
          </div>
        </div>

        {ruleSignal.disclaimer_found && (
          <div className="flex items-center gap-1.5 text-xs text-green-700 bg-green-50 border border-green-200 p-1.5 rounded-lg">
            <CheckCircle2 className="w-3.5 h-3.5 text-green-600" />
            <span>Anti-Scam Disclaimer Negation Active</span>
          </div>
        )}

        {ruleSignal.triggered_rules && ruleSignal.triggered_rules.length > 0 && (
          <div className="flex flex-wrap gap-1">
            {ruleSignal.triggered_rules.map((r, i) => (
              <span key={i} className="text-[10px] bg-rose-50 text-rose-600 border border-rose-200 px-1.5 py-0.5 rounded font-medium">
                {r.rule_name} (+{r.weight})
              </span>
            ))}
          </div>
        )}
      </div>

      {/* 3. Company & Domain Verification Signal */}
      <div className="bg-white rounded-xl border border-gray-200 p-4 shadow-2xs hover:border-orange-300 transition-all flex flex-col justify-between gap-2.5">
        <div>
          <div className="flex items-center justify-between gap-2 mb-2">
            <div className="flex items-center gap-2 font-bold text-sm text-gray-900">
              <Building2 className="w-4 h-4 text-orange-500" />
              <span>Company & Email</span>
            </div>
            <span className={`text-[11px] px-2 py-0.5 rounded-full font-semibold ${
              companySignal.status === 'Verified'
                ? 'bg-green-50 text-green-600 border border-green-200'
                : companySignal.status === 'Suspicious'
                ? 'bg-rose-50 text-rose-600 border border-rose-200'
                : 'bg-gray-100 text-gray-600 border border-gray-200'
            }`}>
              {companySignal.status || 'Unknown'}
            </span>
          </div>
          <div className="text-xs text-gray-500 space-y-0.5">
            <div>Claimed: <strong className="text-gray-900">{companySignal.claimed_company || 'Unspecified'}</strong></div>
            <div>Recruiter: <strong className="text-gray-900">{companySignal.email_domain ? `@${companySignal.email_domain}` : 'Not provided'}</strong></div>
          </div>
        </div>

        {companySignal.reasons && companySignal.reasons.length > 0 && (
          <div className={`text-xs p-1.5 rounded-lg border ${
            companySignal.status === 'Suspicious'
              ? 'bg-rose-50 text-rose-600 border-rose-200'
              : 'bg-gray-50 text-gray-500 border-gray-200'
          }`}>
            {companySignal.reasons[0]}
          </div>
        )}
      </div>

      {/* 4. URL & Security Signal */}
      <div className="bg-white rounded-xl border border-gray-200 p-4 shadow-2xs hover:border-orange-300 transition-all flex flex-col justify-between gap-2.5">
        <div>
          <div className="flex items-center justify-between gap-2 mb-2">
            <div className="flex items-center gap-2 font-bold text-sm text-gray-900">
              <Globe2 className="w-4 h-4 text-orange-500" />
              <span>URL & Domain Security</span>
            </div>
            <span className={`text-[11px] px-2 py-0.5 rounded-full ${getStatusBadge(urlScore).className}`}>
              {urlSignal.url_risk_level || 'None'}
            </span>
          </div>
          <div className="text-xs text-gray-500">
            Provider: <strong className="text-gray-800">{urlSignal.provider || 'Local Heuristics'}</strong>
          </div>
        </div>

        {urlSignal.signals && urlSignal.signals.length > 0 ? (
          <ul className="text-xs text-rose-600 space-y-0.5 list-disc list-inside">
            {urlSignal.signals.slice(0, 2).map((s, i) => (
              <li key={i}>{s}</li>
            ))}
          </ul>
        ) : (
          <div className="text-xs text-gray-400">No high-risk URL shorteners or suspicious TLDs detected.</div>
        )}
      </div>

      {/* 5. Salary Anomaly Signal */}
      <div className="bg-white rounded-xl border border-gray-200 p-4 shadow-2xs hover:border-orange-300 transition-all flex flex-col justify-between gap-2.5">
        <div>
          <div className="flex items-center justify-between gap-2 mb-2">
            <div className="flex items-center gap-2 font-bold text-sm text-gray-900">
              <DollarSign className="w-4 h-4 text-orange-500" />
              <span>Salary Anomaly</span>
            </div>
            <span className={`text-[11px] px-2 py-0.5 rounded-full font-semibold ${
              salarySignal.anomaly_level === 'High'
                ? 'bg-rose-50 text-rose-600 border border-rose-200'
                : salarySignal.anomaly_level === 'Medium'
                ? 'bg-amber-50 text-amber-600 border border-amber-200'
                : 'bg-green-50 text-green-600 border border-green-200'
            }`}>
              {salarySignal.anomaly_level || 'Low'} Anomaly
            </span>
          </div>
          <div className="text-xs text-gray-500">
            Extracted: <strong className="text-gray-900">{salarySignal.extracted_salary || 'Not Disclosed'}</strong>
          </div>
        </div>

        <div className="text-xs text-gray-500">
          {salarySignal.reason || 'Salary fits standard market distribution for this role.'}
        </div>
      </div>

    </div>
  );
}
