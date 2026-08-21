import React from 'react';
import { ShieldCheck, AlertTriangle, AlertOctagon, Info } from 'lucide-react';

export default function RiskGauge({ score = 0, riskLevel = 'Low', verdictBadge = 'Low Risk (Likely Genuine)' }) {
  // SVG circle calculation
  const radius = 70;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (score / 100) * circumference;

  let color = '#22C55E';
  let Icon = ShieldCheck;
  let badgeClass = 'bg-green-100 text-green-600 font-bold rounded-full px-4 py-1 text-sm inline-flex items-center gap-1.5 shadow-2xs';

  if (riskLevel === 'High' || score > 60) {
    color = '#F43F5E';
    Icon = AlertOctagon;
    badgeClass = 'bg-rose-100 text-rose-600 font-bold rounded-full px-4 py-1 text-sm inline-flex items-center gap-1.5 shadow-2xs';
  } else if (riskLevel === 'Medium' || score > 30) {
    color = '#F59E0B';
    Icon = AlertTriangle;
    badgeClass = 'bg-amber-100 text-amber-600 font-bold rounded-full px-4 py-1 text-sm inline-flex items-center gap-1.5 shadow-2xs';
  }

  return (
    <div className="flex flex-col items-center justify-center p-4">
      {/* Gauge Container */}
      <div className="relative w-44 h-44 flex items-center justify-center">
        <svg width="180" height="180" viewBox="0 0 180 180" className="-rotate-90">
          {/* Background circle */}
          <circle
            cx="90"
            cy="90"
            r={radius}
            stroke="#E5E7EB"
            strokeWidth="14"
            fill="transparent"
          />
          {/* Active progress circle */}
          <circle
            cx="90"
            cy="90"
            r={radius}
            stroke={color}
            strokeWidth="14"
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
            fill="transparent"
            style={{
              transition: 'stroke-dashoffset 0.8s cubic-bezier(0.4, 0, 0.2, 1)'
            }}
          />
        </svg>

        {/* Center content */}
        <div className="absolute flex flex-col items-center justify-center">
          <span className="text-4xl font-extrabold text-gray-900 tracking-tight leading-none">
            {score}
          </span>
          <span className="text-[11px] font-semibold text-gray-400 uppercase tracking-wider mt-1">
            Risk Index / 100
          </span>
        </div>
      </div>

      {/* Verdict Badge */}
      <div className="mt-4">
        <span className={badgeClass}>
          <Icon className="w-4 h-4" />
          <span>{verdictBadge}</span>
        </span>
      </div>

      {/* Claims Policy Notice */}
      <div className="mt-3 text-xs text-gray-500 text-center max-w-xs flex items-center justify-center gap-1.5">
        <Info className="w-3.5 h-3.5 text-gray-400 flex-shrink-0" />
        <span>Probabilistic decision-support indicator. Always cross-verify employer legitimacy independently.</span>
      </div>
    </div>
  );
}
