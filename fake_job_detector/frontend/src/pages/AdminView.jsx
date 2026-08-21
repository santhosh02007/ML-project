import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Cpu, CheckCircle2, XCircle, RotateCw, Layers, ShieldAlert, AlertOctagon } from 'lucide-react';
import { fetchReports, verifyReport, triggerRetrain, fetchModelComparison, fetchModelVersions } from '../services/api';
import MagneticButton from '../components/MagneticButton';



export default function AdminView() {
  const [reports, setReports] = useState([]);
  const [comparison, setComparison] = useState(null);
  const [versions, setVersions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [retrainResult, setRetrainResult] = useState(null);
  const [retrainNotes, setRetrainNotes] = useState('');
  const [error, setError] = useState(null);

  const loadData = async () => {
    setLoading(true);
    try {
      const [reps, comp, vers] = await Promise.all([
        fetchReports(),
        fetchModelComparison().catch(() => null),
        fetchModelVersions().catch(() => [])
      ]);
      setReports(reps);
      setComparison(comp);
      setVersions(vers);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleVerify = async (reportId, decision) => {
    setActionLoading(true);
    try {
      await verifyReport(reportId, decision, 'Verified by administrator.');
      await loadData();
    } catch (err) {
      alert(`Error verifying report: ${err.message}`);
    } finally {
      setActionLoading(false);
    }
  };

  const handleRetrain = async () => {
    if (!window.confirm('Trigger automated model retraining and benchmark comparison?')) return;
    setActionLoading(true);
    setError(null);
    try {
      const res = await triggerRetrain(retrainNotes || 'Continuous retraining with verified feedback samples.');
      setRetrainResult(res);
      await loadData();
    } catch (err) {
      setError(err.message || 'Retraining failed.');
    } finally {
      setActionLoading(false);
    }
  };

  const pendingReports = reports.filter(r => r.status === 'pending');

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
          <p className="text-gray-500 text-sm">Loading MLOps & verification data...</p>
        </div>
      </div>
    );
  }

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
            <Cpu className="w-5 h-5" />
          </motion.div>
          <div>
            <h1 className="text-gray-900 font-bold text-3xl tracking-tight">
              <span className="gradient-text">MLOps & Admin Verification Portal</span>
            </h1>
            <p className="text-gray-500 text-sm mt-0.5">
              Review candidate fraud reports, designate verified ground-truth labels, and trigger continuous retraining.
            </p>
          </div>
        </div>

        {error && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-rose-50 border border-rose-200 p-4 rounded-xl text-rose-700 text-sm shadow-2xs"
          >
            {error}
          </motion.div>
        )}

        {/* Grid: Retrain Trigger + Model Benchmark */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          
          {/* Continuous Retraining Trigger */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="bg-white rounded-2xl border border-gray-200 shadow-sm p-6 sm:p-8 flex flex-col justify-between gap-5 card-hover"
          >
            <div className="space-y-3">
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-xl bg-orange-50 text-orange-500 border border-orange-100 flex items-center justify-center">
                  <Cpu className="w-5 h-5" />
                </div>
                <h3 className="text-lg font-bold text-gray-900">
                  Continuous Retraining Pipeline
                </h3>
              </div>

              <p className="text-xs text-gray-500 leading-relaxed">
                Combines verified candidate reports with base training corpus, resamples training distribution to 70/30, trains candidate models, and promotes only if headline Fraud F1 improves.
              </p>

              <div>
                <label className="block text-xs font-semibold text-gray-700 mb-1.5">
                  Retraining Version Notes (Optional)
                </label>
                <input
                  type="text"
                  value={retrainNotes}
                  onChange={(e) => setRetrainNotes(e.target.value)}
                  placeholder="e.g. Added 15 verified Telegram fee scam samples"
                  className="w-full px-3.5 py-2.5 rounded-lg bg-white border border-gray-300 text-gray-900 text-xs transition"
                />
              </div>
            </div>

            <div className="space-y-3">
              <MagneticButton
                onClick={handleRetrain}
                disabled={actionLoading}
                className="btn-glow bg-gradient-to-r from-orange-500 to-rose-500 text-white rounded-lg px-5 py-2.5 text-sm font-medium shadow-lg shadow-orange-500/25 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 cursor-pointer"
              >
                <RotateCw className={`w-4 h-4 ${actionLoading ? 'animate-spin' : ''}`} />
                <span>{actionLoading ? 'Retraining & Evaluating...' : 'Trigger Automated Retraining'}</span>
              </MagneticButton>


              {retrainResult && (
                <motion.div
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  className="bg-green-50 border border-green-200 rounded-xl p-4 text-xs text-green-800 space-y-1 shadow-2xs"
                >
                  <div className="font-bold flex items-center gap-1.5 text-green-900">
                    <CheckCircle2 className="w-4 h-4 text-green-600" />
                    <span>{retrainResult.message}</span>
                  </div>
                  <div>Champion Model: <strong>{retrainResult.metrics_comparison?.champion_model}</strong></div>
                  <div>
                    Fraud F1: <strong>{(retrainResult.metrics_comparison?.fraud_f1 * 100).toFixed(2)}%</strong> | Recall: <strong>{(retrainResult.metrics_comparison?.fraud_recall * 100).toFixed(2)}%</strong>
                  </div>
                </motion.div>
              )}
            </div>
          </motion.div>

          {/* Objective Model Comparison Benchmark */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.15 }}
            className="bg-white rounded-2xl border border-gray-200 shadow-sm p-6 sm:p-8 flex flex-col justify-between gap-4 card-hover"
          >
            <div>
              <div className="flex items-center justify-between gap-3 mb-4">
                <div className="flex items-center gap-3">
                  <div className="w-9 h-9 rounded-xl bg-orange-50 text-orange-500 border border-orange-100 flex items-center justify-center">
                    <Layers className="w-5 h-5" />
                  </div>
                  <h3 className="text-lg font-bold text-gray-900">
                    Model Benchmark Comparison
                  </h3>
                </div>
                <span className="text-xs text-green-700 bg-green-50 border border-green-200 px-3 py-1 rounded-full font-semibold">
                  Champion: {comparison?.champion || 'Logistic Regression'}
                </span>
              </div>

              <div className="overflow-x-auto rounded-xl border border-gray-200">
                <table className="w-full text-left border-collapse text-xs">
                  <thead>
                    <tr className="bg-gray-50 text-gray-400 text-xs uppercase tracking-wider border-b border-gray-200 font-semibold">
                      <th className="py-2.5 px-3">Metric</th>
                      <th className="py-2.5 px-3">Logistic Regression</th>
                      <th className="py-2.5 px-3">Random Forest</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200 bg-white">
                    {(comparison?.metrics_table || []).map((row, i) => (
                      <tr key={i} className="hover:bg-gray-50">
                        <td className="py-2.5 px-3 text-gray-900 font-medium">
                          {row.metric}
                        </td>
                        <td className="py-2.5 px-3 text-orange-600 font-bold font-mono">
                          {row.logistic_regression != null ? `${(row.logistic_regression * 100).toFixed(2)}%` : 'N/A'}
                        </td>
                        <td className="py-2.5 px-3 text-gray-700 font-bold font-mono">
                          {row.random_forest != null ? `${(row.random_forest * 100).toFixed(2)}%` : 'N/A'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            <div className="text-[11px] text-gray-400">
              Evaluated strictly on the held-out untouched test set (~4.8% baseline distribution).
            </div>
          </motion.div>

        </div>

        {/* User Reports Verification Queue */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="bg-white rounded-2xl border border-gray-200 shadow-sm p-6 sm:p-8 space-y-4 card-hover"
        >
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-2 border-b border-gray-100">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-xl bg-rose-50 text-rose-500 border border-rose-100 flex items-center justify-center">
                <ShieldAlert className="w-5 h-5" />
              </div>
              <h3 className="text-lg font-bold text-gray-900">
                Pending User Scam Reports Queue ({pendingReports.length})
              </h3>
            </div>
            <span className="text-xs text-gray-500">
              Designate verified labels to retrain fraud classifiers
            </span>
          </div>

          {pendingReports.length === 0 ? (
            <div className="text-center py-12 text-gray-400 text-xs">
              No pending user reports awaiting review.
            </div>
          ) : (
            <div className="space-y-3">
              {pendingReports.map(rep => (
                <div
                  key={rep.id}
                  className="bg-gray-50 border border-gray-200 rounded-xl p-4 flex flex-col md:flex-row md:items-center justify-between gap-4 shadow-2xs hover:border-orange-300 transition-colors"
                >
                  <div className="space-y-1 max-w-2xl">
                    <div className="flex items-center gap-2 flex-wrap">
                      <strong className="text-gray-900 text-sm font-bold">{rep.job_title}</strong>
                      <span className="text-xs text-gray-500">at {rep.company || 'Unspecified'}</span>
                      <span className="text-[11px] bg-rose-100 text-rose-600 border border-rose-200 px-2 py-0.5 rounded font-semibold">
                        Reason: {rep.report_reason}
                      </span>
                    </div>
                    {rep.description && (
                      <div className="text-xs text-gray-600 italic">
                        "{rep.description}"
                      </div>
                    )}
                    {rep.job_description && (
                      <div className="text-xs text-gray-400 line-clamp-2">
                        {rep.job_description}
                      </div>
                    )}
                  </div>

                  {/* Admin Actions */}
                  <div className="flex items-center gap-2 flex-shrink-0">
                    <motion.button
                      onClick={() => handleVerify(rep.id, 'verified_fraud')}
                      disabled={actionLoading}
                      whileHover={{ scale: 1.04 }}
                      whileTap={{ scale: 0.96 }}
                      className="bg-rose-50 border border-rose-200 text-rose-600 hover:bg-rose-100 px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition cursor-pointer"
                    >
                      <AlertOctagon className="w-3.5 h-3.5" />
                      <span>Verify as Fraud</span>
                    </motion.button>

                    <motion.button
                      onClick={() => handleVerify(rep.id, 'verified_genuine')}
                      disabled={actionLoading}
                      whileHover={{ scale: 1.04 }}
                      whileTap={{ scale: 0.96 }}
                      className="bg-green-50 border border-green-200 text-green-700 hover:bg-green-100 px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition cursor-pointer"
                    >
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      <span>Mark Genuine</span>
                    </motion.button>

                    <motion.button
                      onClick={() => handleVerify(rep.id, 'rejected')}
                      disabled={actionLoading}
                      whileHover={{ scale: 1.04 }}
                      whileTap={{ scale: 0.96 }}
                      className="bg-gray-100 border border-gray-300 text-gray-700 hover:bg-gray-200 px-3 py-1.5 rounded-lg text-xs font-medium flex items-center gap-1.5 transition cursor-pointer"
                    >
                      <XCircle className="w-3.5 h-3.5" />
                      <span>Reject</span>
                    </motion.button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </motion.div>

      </div>
    </motion.div>
  );
}
