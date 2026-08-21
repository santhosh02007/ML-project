import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  UploadCloud,
  FileSpreadsheet,
  Download,
  AlertOctagon,
  AlertTriangle,
  ShieldCheck,
  Search,
  Filter,
  CheckCircle2,
  XCircle,
  Sparkles,
  Layers,
  ArrowRight,
  RefreshCw,
  Table,
  LayoutGrid,
  Building2,
  HelpCircle,
  FileCheck
} from 'lucide-react';
import { uploadBatchCSV, getBatchDownloadUrl } from '../services/api';
import MagneticButton from '../components/MagneticButton';


// Animated Count-Up Component
function AnimatedNumber({ value }) {
  const [display, setDisplay] = useState(0);

  useEffect(() => {
    let start = 0;
    const end = typeof value === 'number' ? value : parseInt(value, 10) || 0;
    if (end === 0) {
      setDisplay(0);
      return;
    }
    const duration = 800; // ms
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

  return <span>{display}</span>;
}

export default function BatchView() {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [batchResult, setBatchResult] = useState(null);
  const [error, setError] = useState(null);
  const [filterLevel, setFilterLevel] = useState('ALL');
  const [searchQuery, setSearchQuery] = useState('');
  const [isDragging, setIsDragging] = useState(false);
  const [viewMode, setViewMode] = useState('table'); // 'table' | 'grid'

  const handleFileChange = (e) => {
    const selected = e.target.files ? e.target.files[0] : null;
    if (selected) {
      if (!selected.name.endsWith('.csv')) {
        setError('Please select a valid .csv file.');
        return;
      }
      setFile(selected);
      setError(null);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const droppedFile = e.dataTransfer.files[0];
      if (!droppedFile.name.endsWith('.csv')) {
        setError('Please select a valid .csv file.');
        return;
      }
      setFile(droppedFile);
      setError(null);
    }
  };

  const handleUpload = async () => {
    if (!file) {
      setError('Please choose a CSV file to scan.');
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const data = await uploadBatchCSV(file);
      setBatchResult(data);
    } catch (err) {
      setError(err.message || 'Batch scanning failed.');
    } finally {
      setLoading(false);
    }
  };

  // Filter results
  const filteredResults = (batchResult?.results || []).filter(item => {
    const matchesLevel = filterLevel === 'ALL' || item.risk_level.toUpperCase() === filterLevel;
    const matchesQuery = item.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         (item.company || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
                         item.top_reason.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesLevel && matchesQuery;
  });

  // Derived KPI metrics
  const totalCount = batchResult?.total_processed || 0;
  const highCount = batchResult?.high_risk_count || 0;
  const medCount = batchResult?.medium_risk_count || 0;
  const lowCount = batchResult?.low_risk_count || 0;

  const highPct = totalCount > 0 ? Math.round((highCount / totalCount) * 100) : 0;
  const medPct = totalCount > 0 ? Math.round((medCount / totalCount) * 100) : 0;
  const lowPct = totalCount > 0 ? Math.round((lowCount / totalCount) * 100) : 0;
  const accuracyPct = totalCount > 0 ? Math.round(((lowCount + highCount) / totalCount) * 100) : 100;

  // Prediction badge renderer matching minimal aesthetic
  const renderPredictionBadge = (riskLevel, verdict) => {
    const level = (riskLevel || '').toUpperCase();
    if (level === 'HIGH') {
      return (
        <span className="bg-rose-100 text-rose-600 font-bold rounded-full px-3 py-0.5 text-xs inline-flex items-center gap-1">
          <span className="w-1.5 h-1.5 rounded-full bg-rose-500"></span>
          {verdict || 'Fake Job'}
        </span>
      );
    }
    if (level === 'MEDIUM') {
      return (
        <span className="bg-amber-100 text-amber-600 font-bold rounded-full px-3 py-0.5 text-xs inline-flex items-center gap-1">
          <span className="w-1.5 h-1.5 rounded-full bg-amber-500"></span>
          {verdict || 'Suspicious'}
        </span>
      );
    }
    return (
      <span className="bg-green-100 text-green-600 font-bold rounded-full px-3 py-0.5 text-xs inline-flex items-center gap-1">
        <span className="w-1.5 h-1.5 rounded-full bg-green-500"></span>
        {verdict || 'Real / Genuine'}
      </span>
    );
  };

  // Score bar helper
  const renderScoreBar = (score, riskLevel) => {
    const level = (riskLevel || '').toUpperCase();
    const textColor = level === 'HIGH' ? 'text-rose-600' : level === 'MEDIUM' ? 'text-amber-600' : 'text-green-600';
    const barColor = level === 'HIGH' ? 'bg-rose-500' : level === 'MEDIUM' ? 'bg-amber-500' : 'bg-green-500';

    return (
      <div className="flex flex-col gap-1 min-w-[85px]">
        <div className="flex items-center justify-between text-xs">
          <span className={`font-mono font-bold ${textColor}`}>{score}</span>
          <span className="text-[10px] text-gray-400">/ 100</span>
        </div>
        <div className="w-full bg-gray-100 rounded-full h-1.5 overflow-hidden">
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${Math.min(Math.max(score, 5), 100)}%` }}
            transition={{ duration: 0.6, ease: 'easeOut' }}
            className={`h-full rounded-full ${barColor}`}
          />
        </div>
      </div>
    );
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.4 }}
      className="page-enter bg-[#FAFAFA] min-h-screen p-6 sm:p-8"
    >

      <div className="max-w-7xl mx-auto space-y-6">

        {/* 1. Header Section */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div className="flex items-center gap-3">
            <motion.div
              whileHover={{ scale: 1.08, rotate: 6 }}
              className="w-10 h-10 rounded-xl bg-orange-50 border border-orange-100 flex items-center justify-center text-orange-500 shadow-2xs"
            >
              <FileSpreadsheet className="w-5 h-5" />
            </motion.div>
            <div>
              <h1 className="text-gray-900 font-bold text-3xl tracking-tight">
                <span className="gradient-text">Batch Scanner</span>
              </h1>
              <p className="text-gray-500 text-sm mt-0.5">
                Upload and scan multiple job postings for fraud, compensation anomalies, and deceptive recruitment campaigns.
              </p>
            </div>
          </div>

          {batchResult && (
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              className="flex items-center gap-3 self-start md:self-auto"
            >
              <a
                href={getBatchDownloadUrl(batchResult.download_id)}
                download
                className="bg-orange-500 hover:bg-orange-600 text-white rounded-lg px-4 py-2.5 text-sm font-medium shadow-sm transition-colors flex items-center gap-2"
              >
                <Download className="w-4 h-4" />
                <span>Download Scored CSV</span>
              </a>
            </motion.div>
          )}
        </div>

        {/* 2. Upload Card */}
        <motion.div
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ duration: 0.4 }}
          className="bg-white rounded-2xl border border-gray-200 shadow-sm p-6 sm:p-8 card-hover"
        >
          {/* Breathing Upload Zone */}
          <motion.div
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            animate={{ 
              borderColor: isDragging ? '#f97316' : ['#fed7aa', '#f97316', '#fed7aa'],
              backgroundColor: isDragging ? '#ffedd5' : ['#fff7ed', '#fef3c7', '#fff7ed']
            }}
            transition={{ duration: 3.5, repeat: Infinity, ease: 'easeInOut' }}
            className={`border-2 border-dashed rounded-2xl p-10 text-center transition-all flex flex-col items-center justify-center ${
              isDragging ? 'ring-4 ring-orange-200 scale-[1.01]' : ''
            }`}
          >
            {/* Upload Icon with bouncing motion */}
            <motion.div
              animate={{ y: [0, -8, 0] }}
              transition={{ duration: 2.2, repeat: Infinity, ease: 'easeInOut' }}
              className="w-14 h-14 rounded-2xl bg-white border border-orange-200 flex items-center justify-center text-orange-400 shadow-sm mb-4"
            >
              <UploadCloud className="w-7 h-7" />
            </motion.div>

            {/* Title & File Info */}
            <h3 className="text-gray-900 font-bold text-lg mb-1">
              {file ? file.name : 'Choose a CSV file or drag and drop here'}
            </h3>

            {file ? (
              <div className="flex items-center gap-3 text-xs text-gray-500 mt-1 mb-5">
                <span className="bg-white px-2.5 py-1 rounded-md text-gray-700 font-mono border border-gray-200 shadow-2xs">
                  {(file.size / 1024).toFixed(1)} KB
                </span>
                <span>•</span>
                <span className="text-green-600 font-semibold flex items-center gap-1">
                  <CheckCircle2 className="w-3.5 h-3.5" /> Ready to scan
                </span>
              </div>
            ) : (
              <p className="text-gray-500 text-sm max-w-md mb-6">
                Upload your CSV dataset containing job titles, descriptions, salaries, and company URLs.
              </p>
            )}

            {/* Hidden Input */}
            <input
              type="file"
              id="csv-upload-input"
              accept=".csv"
              onChange={handleFileChange}
              className="hidden"
            />

            {/* Action Buttons */}
            <div className="flex flex-wrap items-center justify-center gap-3">
              <motion.label
                htmlFor="csv-upload-input"
                whileHover={{ scale: 1.03 }}
                whileTap={{ scale: 0.97 }}
                className="bg-white hover:bg-gray-50 text-gray-700 border border-gray-300 rounded-lg px-5 py-2.5 text-sm font-medium shadow-2xs transition-colors cursor-pointer inline-flex items-center gap-2"
              >
                <FileSpreadsheet className="w-4 h-4 text-orange-500" />
                <span>{file ? 'Change CSV File' : 'Browse CSV File'}</span>
              </motion.label>

              {file && (
                <MagneticButton
                  onClick={handleUpload}
                  disabled={loading}
                  className="btn-glow bg-gradient-to-r from-orange-500 to-rose-500 text-white rounded-lg px-6 py-2.5 font-medium text-sm shadow-lg shadow-orange-500/25 transition-colors disabled:opacity-50 disabled:cursor-not-allowed inline-flex items-center gap-2 cursor-pointer"
                >
                  {loading ? (
                    <>
                      <RefreshCw className="w-4 h-4 animate-spin text-white" />
                      <span>Processing Batch Scan...</span>
                    </>
                  ) : (
                    <>
                      <span>Run Batch Scan</span>
                      <ArrowRight className="w-4 h-4" />
                    </>
                  )}
                </MagneticButton>
              )}

            </div>

            {/* Schema guidance */}
            <div className="mt-8 pt-5 border-t border-orange-200/60 w-full max-w-xl flex flex-col items-center gap-2">
              <div className="flex items-center gap-1.5 text-xs text-gray-500 font-medium">
                <HelpCircle className="w-3.5 h-3.5 text-orange-400" />
                <span>Supported CSV Column Headers:</span>
              </div>
              <div className="flex flex-wrap items-center justify-center gap-1.5">
                {['title', 'company', 'description', 'requirements', 'salary', 'contact_email', 'application_url'].map(col => (
                  <span key={col} className="bg-white text-gray-600 border border-orange-200 px-2 py-0.5 rounded-md text-[11px] font-mono shadow-2xs">
                    {col}
                  </span>
                ))}
              </div>
            </div>
          </motion.div>

          {/* Error message */}
          {error && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="mt-4 p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-sm flex items-start gap-3 shadow-2xs"
            >
              <AlertOctagon className="w-5 h-5 flex-shrink-0 mt-0.5 text-rose-500" />
              <div className="flex-1">
                <strong className="font-semibold block mb-0.5">Upload Error</strong>
                <span>{error}</span>
              </div>
            </motion.div>
          )}
        </motion.div>

        {/* Loading State with animated dots */}
        {loading && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-white rounded-2xl border border-gray-200 p-8 shadow-sm text-center space-y-4"
          >
            <div className="flex justify-center items-center gap-1.5 py-2">
              {[0, 1, 2].map(i => (
                <motion.div
                  key={i}
                  className="w-3 h-3 rounded-full bg-orange-500"
                  animate={{ y: [0, -10, 0] }}
                  transition={{ duration: 0.6, repeat: Infinity, delay: i * 0.15 }}
                />
              ))}
            </div>
            <h4 className="text-gray-900 font-bold text-base">Processing Batch Postings...</h4>
            <p className="text-xs text-gray-500 max-w-md mx-auto">
              Running multi-layer ML fraud classifier, detecting compensation anomalies, and inspecting contact credentials across batch rows.
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 pt-4">
              {[1, 2, 3, 4].map(i => (
                <div key={i} className="h-24 bg-gray-50 rounded-xl border border-gray-200 p-4 animate-pulse">
                  <div className="h-3 bg-gray-200 rounded w-1/2 mb-3"></div>
                  <div className="h-6 bg-gray-200 rounded w-3/4"></div>
                </div>
              ))}
            </div>
          </motion.div>
        )}

        {/* 3. Results Section */}
        {batchResult && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4 }}
            className="space-y-6"
          >
            
            {/* Stats Bar (4 mini stat cards with count-up animations) */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              
              {/* Total Card */}
              <motion.div
                whileHover={{ y: -2 }}
                className="bg-white border border-gray-200 rounded-xl p-4 shadow-sm flex items-center justify-between card-hover"
              >
                <div>
                  <span className="text-gray-500 text-xs font-semibold uppercase tracking-wider block">
                    Total Scanned
                  </span>
                  <div className="text-orange-500 font-bold text-2xl tracking-tight mt-1">
                    <AnimatedNumber value={totalCount} />
                  </div>
                  <div className="text-gray-500 text-xs mt-1">
                    100% processed
                  </div>
                </div>
                <div className="p-3 rounded-xl bg-orange-50 text-orange-500 border border-orange-100">
                  <FileSpreadsheet className="w-5 h-5" />
                </div>
              </motion.div>

              {/* Fake Card */}
              <motion.div
                whileHover={{ y: -2 }}
                className="bg-white border border-gray-200 rounded-xl p-4 shadow-sm flex items-center justify-between card-hover"
              >
                <div>
                  <span className="text-gray-500 text-xs font-semibold uppercase tracking-wider block">
                    Fake Detected
                  </span>
                  <div className="text-rose-500 font-bold text-2xl tracking-tight mt-1">
                    <AnimatedNumber value={highCount} />
                  </div>
                  <div className="text-rose-600 text-xs font-medium mt-1">
                    {highPct}% of batch
                  </div>
                </div>
                <div className="p-3 rounded-xl bg-rose-50 text-rose-500 border border-rose-100">
                  <AlertOctagon className="w-5 h-5" />
                </div>
              </motion.div>

              {/* Real Card */}
              <motion.div
                whileHover={{ y: -2 }}
                className="bg-white border border-gray-200 rounded-xl p-4 shadow-sm flex items-center justify-between card-hover"
              >
                <div>
                  <span className="text-gray-500 text-xs font-semibold uppercase tracking-wider block">
                    Real (Genuine)
                  </span>
                  <div className="text-green-500 font-bold text-2xl tracking-tight mt-1">
                    <AnimatedNumber value={lowCount} />
                  </div>
                  <div className="text-green-600 text-xs font-medium mt-1">
                    {lowPct}% of batch
                  </div>
                </div>
                <div className="p-3 rounded-xl bg-green-50 text-green-600 border border-green-100">
                  <ShieldCheck className="w-5 h-5" />
                </div>
              </motion.div>

              {/* Accuracy / Legitimacy Card */}
              <motion.div
                whileHover={{ y: -2 }}
                className="bg-white border border-gray-200 rounded-xl p-4 shadow-sm flex items-center justify-between card-hover"
              >
                <div>
                  <span className="text-gray-500 text-xs font-semibold uppercase tracking-wider block">
                    Accuracy & Clean Rate
                  </span>
                  <div className="text-gray-900 font-bold text-2xl tracking-tight mt-1">
                    <AnimatedNumber value={accuracyPct} />%
                  </div>
                  <div className="text-gray-500 text-xs mt-1">
                    {medCount} suspicious items
                  </div>
                </div>
                <div className="p-3 rounded-xl bg-gray-50 text-gray-700 border border-gray-200">
                  <FileCheck className="w-5 h-5" />
                </div>
              </motion.div>

            </div>

            {/* Results Table & Toolbar */}
            <div className="bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden p-6 space-y-5 card-hover">
              
              {/* Toolbar */}
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-gray-200">
                
                {/* Search & Filters */}
                <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
                  <div className="relative min-w-[260px]">
                    <Search className="w-4 h-4 text-gray-400 absolute left-3 top-1/2 -translate-y-1/2" />
                    <input
                      type="text"
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      placeholder="Search titles, companies, reasons..."
                      className="w-full pl-9 pr-8 py-2 rounded-lg bg-gray-50 border border-gray-200 text-gray-900 text-xs placeholder-gray-400 transition-all"
                    />
                    {searchQuery && (
                      <button
                        onClick={() => setSearchQuery('')}
                        className="absolute right-2.5 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                      >
                        <XCircle className="w-4 h-4" />
                      </button>
                    )}
                  </div>

                  {/* Filter Pills */}
                  <div className="flex items-center gap-1.5 overflow-x-auto pb-1 sm:pb-0">
                    <div className="hidden lg:flex items-center text-gray-500 mr-1 text-xs">
                      <Filter className="w-3.5 h-3.5 mr-1 text-orange-500" />
                      <span>Filter:</span>
                    </div>
                    {[
                      { id: 'ALL', label: 'All', count: totalCount },
                      { id: 'HIGH', label: '🔴 Fake', count: highCount },
                      { id: 'MEDIUM', label: '🟡 Suspicious', count: medCount },
                      { id: 'LOW', label: '🟢 Real', count: lowCount }
                    ].map(tab => (
                      <motion.button
                        key={tab.id}
                        onClick={() => setFilterLevel(tab.id)}
                        whileHover={{ scale: 1.04 }}
                        whileTap={{ scale: 0.96 }}
                        className={`px-3 py-1.5 rounded-lg text-xs font-semibold whitespace-nowrap transition-all flex items-center gap-1.5 cursor-pointer ${
                          filterLevel === tab.id
                            ? 'bg-orange-500 text-white shadow-2xs'
                            : 'bg-gray-100 text-gray-600 hover:bg-gray-200 border border-gray-200'
                        }`}
                      >
                        <span>{tab.label}</span>
                        <span className={`px-1.5 py-0.2 rounded-full text-[10px] ${
                          filterLevel === tab.id ? 'bg-orange-600 text-white' : 'bg-white text-gray-500 border border-gray-200'
                        }`}>
                          {tab.count}
                        </span>
                      </motion.button>
                    ))}
                  </div>
                </div>

                {/* View Mode Toggle */}
                <div className="flex items-center gap-2 self-end sm:self-auto">
                  <div className="flex items-center p-1 rounded-lg bg-gray-100 border border-gray-200">
                    <button
                      onClick={() => setViewMode('table')}
                      title="Table View"
                      className={`p-1.5 rounded-md text-xs font-medium transition-all flex items-center gap-1 cursor-pointer ${
                        viewMode === 'table' ? 'bg-white text-gray-900 shadow-2xs font-semibold' : 'text-gray-500 hover:text-gray-800'
                      }`}
                    >
                      <Table className="w-4 h-4" />
                      <span className="hidden sm:inline">Table</span>
                    </button>
                    <button
                      onClick={() => setViewMode('grid')}
                      title="Card Grid View"
                      className={`p-1.5 rounded-md text-xs font-medium transition-all flex items-center gap-1 cursor-pointer ${
                        viewMode === 'grid' ? 'bg-white text-gray-900 shadow-2xs font-semibold' : 'text-gray-500 hover:text-gray-800'
                      }`}
                    >
                      <LayoutGrid className="w-4 h-4" />
                      <span className="hidden sm:inline">Cards</span>
                    </button>
                  </div>
                </div>

              </div>

              {/* No Results Fallback */}
              {filteredResults.length === 0 ? (
                <div className="text-center py-16 px-4">
                  <div className="w-12 h-12 rounded-2xl bg-orange-50 text-orange-500 flex items-center justify-center mx-auto mb-3">
                    <Search className="w-6 h-6" />
                  </div>
                  <h4 className="text-gray-900 font-bold text-base">No Matching Job Postings</h4>
                  <p className="text-xs text-gray-500 max-w-sm mx-auto mt-1 mb-4">
                    No records match your active search query or filter.
                  </p>
                  <button
                    onClick={() => {
                      setFilterLevel('ALL');
                      setSearchQuery('');
                    }}
                    className="px-4 py-2 rounded-lg bg-white border border-gray-300 text-xs font-medium text-gray-700 hover:bg-gray-50 shadow-2xs cursor-pointer"
                  >
                    Clear All Filters
                  </button>
                </div>
              ) : viewMode === 'table' ? (
                
                /* Results Table with Framer Motion Staggered Rows */
                <div className="overflow-x-auto rounded-xl border border-gray-200">
                  <table className="w-full text-left border-collapse text-xs">
                    <thead>
                      <tr className="bg-gray-50 text-gray-400 text-xs uppercase tracking-wider border-b border-gray-200 font-semibold">
                        <th className="py-3 px-4">#</th>
                        <th className="py-3 px-4">Job Title</th>
                        <th className="py-3 px-4">Company</th>
                        <th className="py-3 px-4">Risk Score</th>
                        <th className="py-3 px-4">Prediction</th>
                        <th className="py-3 px-4">Primary Risk Signal</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-200">
                      {filteredResults.map((row, idx) => (
                        <motion.tr
                          key={row.row_index}
                          initial={{ opacity: 0, x: -15 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ delay: Math.min(idx * 0.025, 0.4), duration: 0.25 }}
                          whileHover={{ backgroundColor: '#FFF7ED' }}
                          className={`${
                            idx % 2 === 1 ? 'bg-gray-50/70' : 'bg-white'
                          } transition-colors`}
                        >
                          <td className="py-3 px-4 font-mono text-gray-400">
                            {row.row_index + 1}
                          </td>
                          <td className="py-3 px-4 font-semibold text-gray-900 max-w-[240px] truncate" title={row.title}>
                            {row.title}
                          </td>
                          <td className="py-3 px-4 text-gray-600">
                            <div className="flex items-center gap-1.5 max-w-[180px] truncate" title={row.company}>
                              <Building2 className="w-3.5 h-3.5 text-gray-400 flex-shrink-0" />
                              <span>{row.company || 'Unspecified'}</span>
                            </div>
                          </td>
                          <td className="py-3 px-4">
                            {renderScoreBar(row.risk_score, row.risk_level)}
                          </td>
                          <td className="py-3 px-4 whitespace-nowrap">
                            {renderPredictionBadge(row.risk_level, row.verdict)}
                          </td>
                          <td className="py-3 px-4 text-gray-600 text-xs max-w-[320px]">
                            <div className="flex items-start gap-1.5">
                              {row.risk_level === 'High' ? (
                                <AlertOctagon className="w-3.5 h-3.5 text-rose-500 mt-0.5 flex-shrink-0" />
                              ) : row.risk_level === 'Medium' ? (
                                <AlertTriangle className="w-3.5 h-3.5 text-amber-500 mt-0.5 flex-shrink-0" />
                              ) : (
                                <ShieldCheck className="w-3.5 h-3.5 text-green-500 mt-0.5 flex-shrink-0" />
                              )}
                              <span className="line-clamp-2" title={row.top_reason}>
                                {row.top_reason}
                              </span>
                            </div>
                          </td>
                        </motion.tr>
                      ))}
                    </tbody>
                  </table>
                </div>

              ) : (
                
                /* Results Cards Grid */
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {filteredResults.map((row, idx) => (
                    <motion.div
                      key={row.row_index}
                      initial={{ opacity: 0, y: 15 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: Math.min(idx * 0.03, 0.4), duration: 0.3 }}
                      className="rounded-xl bg-white border border-gray-200 p-5 shadow-2xs card-hover flex flex-col justify-between gap-4"
                    >
                      <div>
                        {/* Card Header */}
                        <div className="flex items-center justify-between gap-2 mb-3">
                          <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-gray-100 text-gray-600 border border-gray-200">
                            #{row.row_index + 1}
                          </span>
                          <div>
                            {renderPredictionBadge(row.risk_level, row.verdict)}
                          </div>
                        </div>

                        {/* Title & Company */}
                        <h4 className="text-sm font-bold text-gray-900 mb-1 line-clamp-2" title={row.title}>
                          {row.title}
                        </h4>
                        <div className="flex items-center gap-1.5 text-xs text-gray-500 mb-3">
                          <Building2 className="w-3.5 h-3.5 text-gray-400" />
                          <span className="truncate">{row.company || 'Unspecified Company'}</span>
                        </div>

                        {/* Key Signal */}
                        <div className="p-3 rounded-lg text-xs leading-relaxed bg-gray-50 border border-gray-200 text-gray-600">
                          <strong className="block text-[10px] uppercase font-bold tracking-wider text-gray-400 mb-0.5">
                            Key Signal
                          </strong>
                          <span>{row.top_reason}</span>
                        </div>
                      </div>

                      {/* Footer Score */}
                      <div className="pt-3 border-t border-gray-100">
                        {renderScoreBar(row.risk_score, row.risk_level)}
                      </div>
                    </motion.div>
                  ))}
                </div>
              )}

              {/* Count Footer */}
              <div className="flex items-center justify-between text-xs text-gray-500 pt-2">
                <span>Showing <strong>{filteredResults.length}</strong> of <strong>{batchResult.results?.length || 0}</strong> job postings</span>
                <span>Dataset Token: <code className="font-mono text-orange-600 font-semibold">{batchResult.download_id?.slice(0, 8)}</code></span>
              </div>

            </div>

          </motion.div>
        )}

        {/* 5. Initial Empty State (Before Any Upload) */}
        {!batchResult && !loading && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.3 }}
            className="space-y-6"
          >
            <div className="text-center py-12 px-4 rounded-2xl bg-white border border-gray-200 shadow-sm card-hover">
              <div className="w-14 h-14 rounded-2xl bg-orange-50 text-orange-500 flex items-center justify-center mx-auto mb-3 shadow-2xs">
                <UploadCloud className="w-7 h-7" />
              </div>
              <p className="text-gray-500 font-medium text-sm">
                No results yet. Upload a batch to begin.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              
              <motion.div whileHover={{ y: -3 }} className="p-5 rounded-xl bg-white border border-gray-200 shadow-sm card-hover">
                <div className="w-10 h-10 rounded-lg bg-orange-50 text-orange-500 flex items-center justify-center mb-3">
                  <Layers className="w-5 h-5" />
                </div>
                <h4 className="text-sm font-bold text-gray-900 mb-1">High-Throughput ML</h4>
                <p className="text-xs text-gray-500 leading-relaxed">
                  Process hundreds of job listings simultaneously with fast TF-IDF and calibrated multi-layer decision trees.
                </p>
              </motion.div>

              <motion.div whileHover={{ y: -3 }} className="p-5 rounded-xl bg-white border border-gray-200 shadow-sm card-hover">
                <div className="w-10 h-10 rounded-lg bg-rose-50 text-rose-500 flex items-center justify-center mb-3">
                  <AlertOctagon className="w-5 h-5" />
                </div>
                <h4 className="text-sm font-bold text-gray-900 mb-1">Syndicate Risk Scoring</h4>
                <p className="text-xs text-gray-500 leading-relaxed">
                  Pinpoints Telegram recruiting, registration fee check scams, brand impersonation, and unrealistic salary anomalies.
                </p>
              </motion.div>

              <motion.div whileHover={{ y: -3 }} className="p-5 rounded-xl bg-white border border-gray-200 shadow-sm card-hover">
                <div className="w-10 h-10 rounded-lg bg-gray-100 text-gray-700 flex items-center justify-center mb-3">
                  <Download className="w-5 h-5" />
                </div>
                <h4 className="text-sm font-bold text-gray-900 mb-1">Scored Export & Audit</h4>
                <p className="text-xs text-gray-500 leading-relaxed">
                  Export scored CSVs with detailed threat breakdowns, confidence ratings, and primary risk evidence snippets.
                </p>
              </motion.div>

            </div>
          </motion.div>
        )}

      </div>
    </motion.div>
  );
}
