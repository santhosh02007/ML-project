import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Shield, RotateCcw, Flag, ArrowRight, Sparkles } from 'lucide-react';
import { analyzeJob, fetchSamples } from '../services/api';
import RiskGauge from '../components/RiskGauge';
import SignalCards from '../components/SignalCards';
import EvidenceHighlighter from '../components/EvidenceHighlighter';
import SampleSelector from '../components/SampleSelector';
import ReportModal from '../components/ReportModal';
import MagneticButton from '../components/MagneticButton';

export default function InspectorView() {
  const [samples, setSamples] = useState([]);
  const [formData, setFormData] = useState({
    title: '',
    company: '',
    description: '',
    requirements: '',
    salary: '',
    contact_email: '',
    application_url: '',
    location: '',
    experience: '',
    model_type: 'champion'
  });

  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [reportModalOpen, setReportModalOpen] = useState(false);

  useEffect(() => {
    fetchSamples()
      .then(data => {
        if (data.samples) {
          setSamples(data.samples);
          // Preload sample 2 (Fee scam) for instant demonstration
          if (data.samples.length > 1) {
            handleSelectSample(data.samples[1]);
          }
        }
      })
      .catch(console.error);
  }, []);

  const handleSelectSample = (sample) => {
    setFormData({
      title: sample.title || '',
      company: sample.company || '',
      description: sample.description || '',
      requirements: sample.requirements || '',
      salary: sample.salary || '',
      contact_email: sample.contact_email || '',
      application_url: sample.application_url || '',
      location: sample.location || '',
      experience: sample.experience || '',
      model_type: 'champion'
    });
    setResult(null);
    setError(null);
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleAnalyze = async (e) => {
    if (e) e.preventDefault();
    if (!formData.title || !formData.description) {
      setError('Please provide at least a Job Title and Description to analyze.');
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const data = await analyzeJob(formData);
      setResult(data);
    } catch (err) {
      setError(err.message || 'Analysis failed. Please ensure the backend is running.');
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setFormData({
      title: '',
      company: '',
      description: '',
      requirements: '',
      salary: '',
      contact_email: '',
      application_url: '',
      location: '',
      experience: '',
      model_type: 'champion'
    });
    setResult(null);
    setError(null);
  };

  const isHighRisk = result && (result.risk_level === 'High' || result.risk_score > 60);
  const isMedRisk = result && (result.risk_level === 'Medium' || result.risk_score > 30);
  const resultBorderClass = isHighRisk 
    ? 'border-l-4 border-l-rose-500' 
    : isMedRisk 
    ? 'border-l-4 border-l-amber-500' 
    : 'border-l-4 border-l-green-500';

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.4 }}
      className="page-enter bg-[#FAFAFA] min-h-screen p-6 sm:p-8"
    >

      <div className="max-w-7xl mx-auto">
        
        {/* Sample Selector Chips */}
        <SampleSelector samples={samples} onSelectSample={handleSelectSample} />

        {/* Main Analysis Form & Live Result Grid */}
        <div className={`grid gap-6 transition-all duration-300 ${result ? 'grid-cols-1 lg:grid-cols-2' : 'grid-cols-1'}`}>
          
          {/* Left / Input Form */}
          <motion.div
            initial={{ y: 30, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: 0.2, duration: 0.5, ease: 'easeOut' }}
            className="bg-white rounded-2xl border border-gray-200 shadow-sm p-6 sm:p-8 card-hover"
          >
            <div className="flex items-center justify-between gap-4 mb-6">
              <div className="flex items-center gap-3">
                <motion.div
                  whileHover={{ rotate: 10, scale: 1.05 }}
                  className="w-10 h-10 rounded-xl bg-orange-50 border border-orange-100 flex items-center justify-center text-orange-500 shadow-2xs"
                >
                  <Shield className="w-5 h-5" />
                </motion.div>
                <motion.h2
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.3 }}
                  className="text-gray-900 font-bold text-2xl tracking-tight"
                >
                  <span className="gradient-text">Recruitment Fraud Inspector</span>
                </motion.h2>
              </div>
              <motion.button
                type="button"
                onClick={handleReset}
                whileHover={{ scale: 1.03 }}
                whileTap={{ scale: 0.96 }}
                className="bg-white border border-gray-300 text-gray-600 hover:bg-gray-50 rounded-lg px-4 py-2 text-sm font-medium transition cursor-pointer flex items-center gap-1.5 shadow-2xs"
              >
                <RotateCcw className="w-3.5 h-3.5" />
                <span>Clear Form</span>
              </motion.button>
            </div>

            {error && (
              <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                className="bg-rose-50 border border-rose-200 p-4 rounded-xl text-rose-700 text-sm mb-5 shadow-2xs"
              >
                {error}
              </motion.div>
            )}

            <form onSubmit={handleAnalyze} className="space-y-4">
              {/* Title & Company */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-gray-600 text-sm font-medium mb-1.5">
                    Job Title *
                  </label>
                  <input
                    type="text"
                    name="title"
                    value={formData.title}
                    onChange={handleInputChange}
                    placeholder="e.g. Senior Software Engineer"
                    required
                    className="bg-white border border-gray-300 text-gray-900 rounded-lg px-4 py-2.5 w-full text-sm transition"
                  />
                </div>

                <div>
                  <label className="block text-gray-600 text-sm font-medium mb-1.5">
                    Company Name
                  </label>
                  <input
                    type="text"
                    name="company"
                    value={formData.company}
                    onChange={handleInputChange}
                    placeholder="e.g. Amazon, Google, Startup"
                    className="bg-white border border-gray-300 text-gray-900 rounded-lg px-4 py-2.5 w-full text-sm transition"
                  />
                </div>
              </div>

              {/* Email & Application URL */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-gray-600 text-sm font-medium mb-1.5">
                    Recruiter Contact Email
                  </label>
                  <input
                    type="text"
                    name="contact_email"
                    value={formData.contact_email}
                    onChange={handleInputChange}
                    placeholder="e.g. hr@company.com or recruiter@gmail.com"
                    className="bg-white border border-gray-300 text-gray-900 rounded-lg px-4 py-2.5 w-full text-sm transition"
                  />
                </div>

                <div>
                  <label className="block text-gray-600 text-sm font-medium mb-1.5">
                    Application / Website URL
                  </label>
                  <input
                    type="text"
                    name="application_url"
                    value={formData.application_url}
                    onChange={handleInputChange}
                    placeholder="e.g. https://company.jobs or bit.ly/..."
                    className="bg-white border border-gray-300 text-gray-900 rounded-lg px-4 py-2.5 w-full text-sm transition"
                  />
                </div>
              </div>

              {/* Salary & Experience */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-gray-600 text-sm font-medium mb-1.5">
                    Advertised Salary / Compensation
                  </label>
                  <input
                    type="text"
                    name="salary"
                    value={formData.salary}
                    onChange={handleInputChange}
                    placeholder="e.g. $60k-$80k or $45/hr or $500/day"
                    className="bg-white border border-gray-300 text-gray-900 rounded-lg px-4 py-2.5 w-full text-sm transition"
                  />
                </div>

                <div>
                  <label className="block text-gray-600 text-sm font-medium mb-1.5">
                    Experience Level / Location
                  </label>
                  <input
                    type="text"
                    name="experience"
                    value={formData.experience}
                    onChange={handleInputChange}
                    placeholder="e.g. Entry Level, 3+ years, Remote"
                    className="bg-white border border-gray-300 text-gray-900 rounded-lg px-4 py-2.5 w-full text-sm transition"
                  />
                </div>
              </div>

              {/* Description */}
              <div>
                <label className="block text-gray-600 text-sm font-medium mb-1.5">
                  Full Job Posting Description *
                </label>
                <textarea
                  name="description"
                  value={formData.description}
                  onChange={handleInputChange}
                  placeholder="Paste the full job description or recruiter communication here..."
                  rows={5}
                  required
                  className="bg-white border border-gray-300 text-gray-900 rounded-lg px-4 py-2.5 w-full text-sm transition resize-y"
                />
              </div>

              {/* Requirements */}
              <div>
                <label className="block text-gray-600 text-sm font-medium mb-1.5">
                  Requirements & Qualifications (Optional)
                </label>
                <textarea
                  name="requirements"
                  value={formData.requirements}
                  onChange={handleInputChange}
                  placeholder="Qualifications, skills, or interview steps..."
                  rows={2}
                  className="bg-white border border-gray-300 text-gray-900 rounded-lg px-4 py-2.5 w-full text-sm transition resize-y"
                />
              </div>

              {/* Loading animated progress bar */}
              {loading && (
                <div className="space-y-2 py-1">
                  <div className="flex items-center justify-between text-xs text-orange-600 font-semibold">
                    <div className="flex items-center gap-1.5">
                      <span>Evaluating 7 Defense Layers</span>
                      <div className="flex gap-1 items-center">
                        {[0, 1, 2].map(i => (
                          <motion.div
                            key={i}
                            className="w-1.5 h-1.5 rounded-full bg-orange-500"
                            animate={{ y: [0, -4, 0] }}
                            transition={{ duration: 0.6, repeat: Infinity, delay: i * 0.15 }}
                          />
                        ))}
                      </div>
                    </div>
                    <span>ML Inference & Analysis</span>
                  </div>
                  <div className="h-1.5 w-full bg-orange-100 rounded-full overflow-hidden">
                    <motion.div
                      className="h-full bg-gradient-to-r from-orange-500 to-rose-500 rounded-full"
                      initial={{ width: '0%' }}
                      animate={{ width: '100%' }}
                      transition={{ duration: 1.5, ease: 'easeInOut', repeat: Infinity }}
                    />
                  </div>
                </div>
              )}

              {/* Action Bar */}
              <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-4 pt-2">
                <div className="flex items-center gap-2">
                  <span className="text-xs text-gray-500 font-medium">Model:</span>
                  <select
                    name="model_type"
                    value={formData.model_type}
                    onChange={handleInputChange}
                    className="px-3 py-1.5 rounded-lg bg-white border border-gray-300 text-gray-800 text-xs font-medium"
                  >
                    <option value="champion">Champion (Ensemble / Best F1)</option>
                    <option value="logistic_regression">TF-IDF + Logistic Regression</option>
                    <option value="random_forest">TF-IDF + Random Forest</option>
                  </select>
                </div>

                <MagneticButton
                  type="submit"
                  disabled={loading}
                  className="btn-glow bg-gradient-to-r from-orange-500 to-rose-500 text-white font-semibold rounded-xl px-8 py-3 transition shadow-lg shadow-orange-500/25 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 text-sm cursor-pointer"
                >
                  <span>{loading ? 'Evaluating...' : 'Run Fraud Analysis'}</span>
                  <ArrowRight className="w-4 h-4" />
                </MagneticButton>

              </div>
            </form>
          </motion.div>

          {/* Right / Live Analysis Result with AnimatePresence */}
          <AnimatePresence>
            {result && (
              <motion.div
                initial={{ opacity: 0, scale: 0.95, y: 20 }}
                animate={{ opacity: 1, scale: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.95 }}
                transition={{ duration: 0.4, ease: 'easeOut' }}
                className={`bg-white rounded-2xl border border-gray-200 shadow-sm p-6 sm:p-8 flex flex-col gap-4 card-hover ${resultBorderClass}`}
              >
                <div className="flex items-center justify-between gap-3 pb-3 border-b border-gray-100">
                  <div>
                    <h3 className="text-xl font-bold text-gray-900">Explainable Threat Assessment</h3>
                    <span className="text-xs text-gray-400 font-mono">Evaluated in {result.analysis_time_ms}ms</span>
                  </div>
                  <motion.button
                    onClick={() => setReportModalOpen(true)}
                    whileHover={{ scale: 1.04 }}
                    whileTap={{ scale: 0.96 }}
                    className="bg-rose-50 border border-rose-200 text-rose-600 hover:bg-rose-100 rounded-lg px-3 py-1.5 text-xs font-semibold transition cursor-pointer flex items-center gap-1.5"
                  >
                    <Flag className="w-3.5 h-3.5" />
                    <span>Report This Job</span>
                  </motion.button>
                </div>

                {/* Gauge */}
                <RiskGauge
                  score={result.risk_score}
                  riskLevel={result.risk_level}
                  verdictBadge={result.verdict_badge}
                />

                {/* Signal Breakdown Cards */}
                <SignalCards breakdown={result.breakdown} signals={result.signals} />

                {/* Evidence Highlighter & Recommendations */}
                <EvidenceHighlighter
                  text={formData.description}
                  matchedSnippets={result.matched_snippets}
                  recommendation={result.recommendation}
                  riskFactors={result.risk_factors}
                />
              </motion.div>
            )}
          </AnimatePresence>

        </div>

        {/* Report Modal */}
        <ReportModal
          isOpen={reportModalOpen}
          onClose={() => setReportModalOpen(false)}
          jobData={{ ...formData, job_id: result?.job_id }}
        />

      </div>
    </motion.div>
  );
}
