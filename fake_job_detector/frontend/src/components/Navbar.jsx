import React from 'react';
import { motion } from 'framer-motion';
import { Shield, ShieldAlert, Cpu, FileSpreadsheet, BarChart3, Sparkles } from 'lucide-react';

export default function Navbar({ activeTab, setActiveTab, modelInfo }) {
  const navItems = [
    { id: 'inspector', label: 'Job Inspector', icon: ShieldAlert },
    { id: 'batch', label: 'Batch Scanner', icon: FileSpreadsheet },
    { id: 'analytics', label: 'Threat Intelligence', icon: BarChart3 },
    { id: 'admin', label: 'MLOps & Admin', icon: Cpu }
  ];

  return (
    <motion.header
      initial={{ y: -20, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.4, ease: 'easeOut' }}
      className="bg-white/95 backdrop-blur-md border-b border-gray-200 shadow-sm sticky top-0 z-50"
    >
      <div className="max-w-7xl mx-auto px-6 sm:px-8 py-3.5 flex items-center justify-between flex-wrap gap-4">
        
        {/* Brand */}
        <div 
          className="flex items-center gap-3 cursor-pointer select-none group" 
          onClick={() => setActiveTab('inspector')}
        >
          <motion.div
            animate={{ scale: [1, 1.06, 1] }}
            transition={{ repeat: Infinity, duration: 3, ease: 'easeInOut' }}
            className="w-10 h-10 rounded-xl bg-gradient-to-br from-orange-400 to-rose-500 flex items-center justify-center text-white shadow-md shadow-orange-500/20"
          >
            <Shield className="w-5 h-5" />
          </motion.div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-gray-900 font-extrabold text-xl tracking-tight">
                <span className="gradient-text-animated">VERITAS SHIELD</span>
              </span>
              <span className="bg-orange-50 border border-orange-200/80 px-2 py-0.5 rounded-full text-xs font-bold font-mono">
                <span className="badge-shimmer">AI ML 2.0</span>
              </span>
            </div>
            <div className="text-gray-500 text-xs flex items-center gap-1.5">
              <span>Recruitment Fraud & Scam Detection</span>
            </div>
          </div>

        </div>

        {/* Navigation Tabs with Framer Motion */}
        <nav className="flex items-center gap-1.5 bg-gray-100/90 p-1 rounded-xl border border-gray-200/80">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;

            return (
              <motion.button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                whileHover={{ y: -1, scale: 1.02 }}
                whileTap={{ scale: 0.97 }}
                className={`relative flex items-center gap-2 px-3.5 py-2 rounded-lg text-xs sm:text-sm font-semibold transition-all cursor-pointer ${
                  isActive
                    ? 'text-white'
                    : 'text-gray-600 hover:text-orange-500'
                }`}
              >
                {isActive && (
                  <motion.div
                    layoutId="activeTabPill"
                    className="absolute inset-0 bg-gradient-to-r from-orange-500 to-rose-500 rounded-lg shadow-sm shadow-orange-500/25"
                    transition={{ type: 'spring', stiffness: 450, damping: 35 }}
                  />
                )}
                <span className="relative z-10 flex items-center gap-2">
                  <Icon className="w-4 h-4" />
                  <span>{item.label}</span>
                </span>
              </motion.button>
            );
          })}
        </nav>

        {/* Model Status Pill */}
        <div className="flex items-center gap-3">
          <motion.div
            whileHover={{ scale: 1.03 }}
            className="bg-rose-50 text-rose-600 border border-rose-200 text-xs px-3 py-1 rounded-full font-semibold flex items-center gap-1.5 shadow-2xs"
          >
            <motion.span
              animate={{ opacity: [1, 0.4, 1] }}
              transition={{ repeat: Infinity, duration: 2, ease: 'easeInOut' }}
              className="w-2 h-2 rounded-full bg-rose-500"
            />
            <span>{modelInfo?.active_version || 'v1.0.0'} Champion: {modelInfo?.champion_model || 'Logistic Regression'}</span>
          </motion.div>
        </div>

      </div>
    </motion.header>
  );
}
