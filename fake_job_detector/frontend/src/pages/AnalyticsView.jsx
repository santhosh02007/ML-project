import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { BarChart3, ShieldAlert, Cpu, Activity, TrendingUp, AlertTriangle, Flame, Hash } from 'lucide-react';
import { fetchDashboardStats, fetchThreatInsights } from '../services/api';

// Animated Count-Up Component
function AnimatedNumber({ value, suffix = '' }) {
  const [display, setDisplay] = useState(0);

  useEffect(() => {
    let start = 0;
    const end = typeof value === 'number' ? value : parseInt(value, 10) || 0;
    if (end === 0) {
      setDisplay(0);
      return;
    }
    const duration = 800;
    const stepTime = 20;
    const steps = duration / stepTime;
    const increment = end / steps;
    const timer = setInterval(() => {
      start += increment;
      if (start >= end) {
        setDisplay(end);
        clearInterval(timer);
      } else {
        setDisplay(Math.floor(start));
      }
    }, stepTime);
    return () => clearInterval(timer);
  }, [value]);

  return <span>{display}{suffix}</span>;
}

export default function AnalyticsView() {
  const [stats, setStats] = useState(null);
  const [insights, setInsights] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([fetchDashboardStats(), fetchThreatInsights()])
      .then(([statsData, insightsData]) => {
        setStats(statsData);
        setInsights(insightsData);
        setLoading(false);
      })
      .catch(err => {
        console.error(err);
        setLoading(false);
      });
  }, []);

  if (loading) {
    return (
      <div className="bg-[#FAFAFA] min-h-screen p-8 flex items-center justify-center">
        <div className="text-center space-y-3">
          <div className="flex justify-center items-center gap-1.5 py-2">
            {[0, 1, 2].map(i => (
              <motion.div
                key={i}
                className="w-2.5 h-2.5 rounded-full bg-orange-500"
                animate={{ y: [0, -8, 0] }}
                transition={{ duration: 0.6, repeat: Infinity, delay: i * 0.15 }}
              />
            ))}
          </div>
          <p className="text-gray-500 text-sm">Loading threat telemetry and model metrics...</p>
        </div>
      </div>
    );
  }

  const dist = stats?.risk_distribution || { High: 0, Medium: 0, Low: 0 };
  const total = (dist.High + dist.Medium + dist.Low) || 1;

  const highPct = Math.round((dist.High / total) * 100);
  const medPct = Math.round((dist.Medium / total) * 100);
  const lowPct = Math.round((dist.Low / total) * 100);

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.4 }}
      className="page-enter bg-[#FAFAFA] min-h-screen p-6 sm:p-8"
    >

      <div className="max-w-7xl mx-auto space-y-6">
        
        {/* Header Banner */}
        <div className="flex items-center gap-3">
          <motion.div
            whileHover={{ scale: 1.08, rotate: 6 }}
            className="w-10 h-10 rounded-xl bg-orange-50 border border-orange-100 flex items-center justify-center text-orange-500 shadow-2xs"
          >
            <BarChart3 className="w-5 h-5" />
          </motion.div>
          <div>
            <h1 className="text-gray-900 font-bold text-3xl tracking-tight">
              <span className="gradient-text">Threat Intelligence & Telemetry</span>
            </h1>
            <p className="text-gray-500 text-sm mt-0.5">
              Real-time analytics on scanned job postings, high-risk syndicate indicators, and ML model performance.
            </p>
          </div>
        </div>

        {/* KPI Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          
          {/* Postings Analyzed */}
          <motion.div
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm flex items-center justify-between card-hover"
          >
            <div>
              <div className="text-xs text-gray-500 font-semibold uppercase tracking-wider">
                Postings Analyzed
              </div>
              <div className="text-orange-500 font-bold text-2xl tracking-tight mt-1">
                <AnimatedNumber value={stats?.total_analyzed || 0} />
              </div>
              <div className="text-xs text-gray-400 mt-0.5">Scanned records</div>
            </div>
            <div className="w-10 h-10 rounded-xl bg-orange-50 text-orange-500 border border-orange-100 flex items-center justify-center">
              <Activity className="w-5 h-5" />
            </div>
          </motion.div>

          {/* High Risk Flags */}
          <motion.div
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.15 }}
            className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm flex items-center justify-between card-hover"
          >
            <div>
              <div className="text-xs text-gray-500 font-semibold uppercase tracking-wider">
                High Risk Flags
              </div>
              <div className="text-rose-500 font-bold text-2xl tracking-tight mt-1">
                <AnimatedNumber value={dist.High} />
              </div>
              <div className="text-xs text-rose-600 font-medium mt-0.5">{highPct}% of total</div>
            </div>
            <div className="w-10 h-10 rounded-xl bg-rose-50 text-rose-500 border border-rose-100 flex items-center justify-center">
              <Flame className="w-5 h-5" />
            </div>
          </motion.div>

          {/* Active Champion F1 */}
          <motion.div
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm flex items-center justify-between card-hover"
          >
            <div>
              <div className="text-xs text-gray-500 font-semibold uppercase tracking-wider">
                Active Champion F1
              </div>
              <div className="text-gray-900 font-bold text-2xl tracking-tight mt-1">
                {stats?.active_model?.fraud_f1 ? `${(stats.active_model.fraud_f1 * 100).toFixed(1)}%` : '100%'}
              </div>
              <div className="text-xs text-green-600 font-medium mt-0.5">Evaluated on test set</div>
            </div>
            <div className="w-10 h-10 rounded-xl bg-green-50 text-green-600 border border-green-100 flex items-center justify-center">
              <Cpu className="w-5 h-5" />
            </div>
          </motion.div>

          {/* User Reports Logged */}
          <motion.div
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.25 }}
            className="bg-white border border-gray-200 rounded-xl p-5 shadow-sm flex items-center justify-between card-hover"
          >
            <div>
              <div className="text-xs text-gray-500 font-semibold uppercase tracking-wider">
                User Reports Logged
              </div>
              <div className="text-gray-900 font-bold text-2xl tracking-tight mt-1">
                <AnimatedNumber value={stats?.total_reports || 0} />
              </div>
              <div className="text-xs text-amber-600 font-medium mt-0.5">Crowdsourced reports</div>
            </div>
            <div className="w-10 h-10 rounded-xl bg-amber-50 text-amber-600 border border-amber-100 flex items-center justify-center">
              <ShieldAlert className="w-5 h-5" />
            </div>
          </motion.div>

        </div>

        {/* Middle Grid: Risk Distribution Bar & Scam Categories */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          
          {/* Risk Distribution Card */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="bg-white rounded-2xl border border-gray-200 shadow-sm p-6 space-y-4 card-hover"
          >
            <div className="flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-orange-500" />
              <h3 className="text-base font-bold text-gray-900">
                Scanned Risk Distribution
              </h3>
            </div>

            {/* Bar indicator */}
            <div className="w-full h-4 rounded-full overflow-hidden flex bg-gray-100">
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${highPct}%` }}
                transition={{ duration: 0.8, ease: 'easeOut' }}
                className="bg-rose-500 h-full"
                title={`High Risk: ${highPct}%`}
              />
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${medPct}%` }}
                transition={{ duration: 0.8, ease: 'easeOut', delay: 0.1 }}
                className="bg-amber-500 h-full"
                title={`Medium Risk: ${medPct}%`}
              />
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${lowPct}%` }}
                transition={{ duration: 0.8, ease: 'easeOut', delay: 0.2 }}
                className="bg-green-500 h-full"
                title={`Low Risk: ${lowPct}%`}
              />
            </div>

            {/* Legend */}
            <div className="space-y-3 pt-2">
              <div className="flex items-center justify-between text-xs">
                <div className="flex items-center gap-2 text-gray-700">
                  <span className="w-2.5 h-2.5 rounded-full bg-rose-500"></span>
                  <span>High Risk (Likely Fraudulent)</span>
                </div>
                <strong className="text-rose-600">{dist.High} ({highPct}%)</strong>
              </div>

              <div className="flex items-center justify-between text-xs">
                <div className="flex items-center gap-2 text-gray-700">
                  <span className="w-2.5 h-2.5 rounded-full bg-amber-500"></span>
                  <span>Medium Risk (Suspicious / Under Review)</span>
                </div>
                <strong className="text-amber-600">{dist.Medium} ({medPct}%)</strong>
              </div>

              <div className="flex items-center justify-between text-xs">
                <div className="flex items-center gap-2 text-gray-700">
                  <span className="w-2.5 h-2.5 rounded-full bg-green-500"></span>
                  <span>Low Risk (Likely Genuine)</span>
                </div>
                <strong className="text-green-600">{dist.Low} ({lowPct}%)</strong>
              </div>
            </div>
          </motion.div>

          {/* Top Threat Categories */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.35 }}
            className="bg-white rounded-2xl border border-gray-200 shadow-sm p-6 space-y-4 card-hover"
          >
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-rose-500" />
              <h3 className="text-base font-bold text-gray-900">
                Top Fraud Typologies Detected
              </h3>
            </div>

            <div className="space-y-3">
              {(insights?.top_scam_categories || []).map((cat, idx) => (
                <div key={idx} className="space-y-1">
                  <div className="flex justify-between text-xs">
                    <span className="text-gray-800 font-medium">{cat.category}</span>
                    <span className="text-gray-500 font-semibold">{cat.share_pct}%</span>
                  </div>
                  <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                    <motion.div
                      className="h-full bg-gradient-to-r from-orange-500 to-rose-500 rounded-full"
                      initial={{ width: 0 }}
                      animate={{ width: `${cat.share_pct}%` }}
                      transition={{ duration: 0.7, ease: 'easeOut', delay: idx * 0.08 }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </motion.div>

        </div>

        {/* Bottom Grid: Top Threat Trigger Keywords */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="bg-white rounded-2xl border border-gray-200 shadow-sm p-6 space-y-4 card-hover"
        >
          <div className="flex items-center gap-2">
            <Hash className="w-5 h-5 text-orange-500" />
            <h3 className="text-base font-bold text-gray-900">
              High-Confidence Scam Trigger Keywords & Risk Weights
            </h3>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
            {(insights?.top_threat_keywords || []).map((kw, i) => (
              <motion.div
                key={i}
                whileHover={{ scale: 1.02, y: -1 }}
                className="bg-gray-50 border border-gray-200 rounded-xl p-3 flex items-center justify-between hover:border-orange-300 hover:bg-orange-50/30 transition-colors shadow-2xs"
              >
                <div>
                  <div className="text-xs font-bold text-gray-900 font-mono">
                    "{kw.keyword}"
                  </div>
                  <div className="text-[11px] text-gray-500 mt-0.5">
                    Freq: {kw.frequency}
                  </div>
                </div>
                <span className="bg-rose-100 text-rose-600 border border-rose-200 px-2 py-0.5 rounded text-xs font-bold font-mono">
                  +{kw.threat_weight} Pts
                </span>
              </motion.div>
            ))}
          </div>
        </motion.div>

      </div>
    </motion.div>
  );
}
