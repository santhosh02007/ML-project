import React from 'react';
import { AlertCircle, FileSearch, ShieldAlert } from 'lucide-react';

export default function EvidenceHighlighter({ text = '', matchedSnippets = [], recommendation = '', riskFactors = [] }) {
  if (!text) return null;

  // Highlight matched snippets in text
  const renderHighlightedText = () => {
    if (!matchedSnippets || matchedSnippets.length === 0) {
      return <span>{text}</span>;
    }

    // Escape regex special chars
    const escapeRegex = (s) => s.replace(/[-/\\^$*+?.()|[\]{}]/g, '\\$&');
    const pattern = new RegExp(`(${matchedSnippets.map(escapeRegex).join('|')})`, 'gi');

    const parts = text.split(pattern);
    return parts.map((part, index) => {
      const isMatch = matchedSnippets.some(s => s.toLowerCase() === part.toLowerCase());
      if (isMatch) {
        return (
          <mark
            key={index}
            className="bg-rose-100 text-rose-700 border border-rose-200 px-1.5 py-0.5 rounded font-bold"
          >
            {part}
          </mark>
        );
      }
      return <span key={index}>{part}</span>;
    });
  };

  return (
    <div className="flex flex-col gap-4 mt-5">
      
      {/* 1. Actionable Recommendation Banner */}
      {recommendation && (
        <div className="bg-orange-50 border border-orange-200 rounded-xl p-4 flex items-start gap-3 text-orange-950">
          <ShieldAlert className="w-5 h-5 text-orange-500 flex-shrink-0 mt-0.5" />
          <div>
            <div className="text-xs font-bold text-orange-700 uppercase tracking-wider">
              Actionable Guidance & Safety Recommendation
            </div>
            <div className="text-sm text-gray-800 mt-1 leading-relaxed">
              {recommendation}
            </div>
          </div>
        </div>
      )}

      {/* 2. Detected Risk Factors & Evidence List */}
      {riskFactors.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-2xs">
          <div className="flex items-center gap-2 font-bold text-sm text-gray-900 mb-3">
            <AlertCircle className="w-4 h-4 text-rose-500" />
            <span>Detected Risk Factors ({riskFactors.length})</span>
          </div>
          <div className="flex flex-col gap-2.5">
            {riskFactors.map((rf, idx) => (
              <div
                key={idx}
                className={`p-3 rounded-r-lg border ${
                  rf.severity === 'High'
                    ? 'bg-rose-50/40 border-l-4 border-l-rose-500 border-rose-100'
                    : 'bg-amber-50/40 border-l-4 border-l-amber-500 border-amber-100'
                }`}
              >
                <div className="flex items-center justify-between gap-2 mb-1">
                  <span className="text-[11px] font-bold text-gray-400 uppercase tracking-wider">
                    Layer: {rf.layer}
                  </span>
                  <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                    rf.severity === 'High' ? 'bg-rose-100 text-rose-700' : 'bg-amber-100 text-amber-700'
                  }`}>
                    {rf.severity} Severity
                  </span>
                </div>
                <div className="text-xs text-gray-900 font-medium">
                  {rf.description}
                </div>
                {rf.evidence && rf.evidence.length > 0 && (
                  <div className="flex flex-wrap gap-1.5 mt-2">
                    {rf.evidence.map((ev, i) => (
                      <span key={i} className="text-[11px] bg-white border border-gray-200 text-rose-600 px-2 py-0.5 rounded font-mono shadow-2xs">
                        "{ev}"
                      </span>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 3. Highlighted Job Posting Transcript */}
      <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-2xs">
        <div className="flex items-center gap-2 font-bold text-sm text-gray-900 mb-2.5">
          <FileSearch className="w-4 h-4 text-orange-500" />
          <span>Job Description Transcript (Evidence Annotated)</span>
        </div>
        <div className="max-h-56 overflow-y-auto bg-gray-50 p-4 rounded-lg text-xs text-gray-800 leading-relaxed font-sans whitespace-pre-wrap border border-gray-200">
          {renderHighlightedText()}
        </div>
      </div>

    </div>
  );
}
