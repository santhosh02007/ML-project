import React from 'react';
import { motion } from 'framer-motion';
import { Sparkles, CheckCircle2, AlertOctagon, DollarSign, Building2, Globe2, ShieldAlert, Languages } from 'lucide-react';

export default function SampleSelector({ samples = [], onSelectSample }) {
  if (!samples || samples.length === 0) return null;

  const getStyleAndIcon = (category) => {
    const isLegit = category.includes('Corporate') || category.includes('Genuine') || category.includes('Disclaimer');
    
    if (isLegit) {
      return {
        className: 'bg-green-50 border border-green-200 text-green-700 hover:bg-green-100 hover:border-green-300',
        icon: <CheckCircle2 className="w-3.5 h-3.5 text-green-600" />
      };
    }

    if (category.includes('Fee') || category.includes('Deposit')) {
      return {
        className: 'bg-rose-50 border border-rose-200 text-rose-600 hover:bg-rose-100 hover:border-rose-300',
        icon: <AlertOctagon className="w-3.5 h-3.5 text-rose-500" />
      };
    }

    if (category.includes('Salary')) {
      return {
        className: 'bg-rose-50 border border-rose-200 text-rose-600 hover:bg-rose-100 hover:border-rose-300',
        icon: <DollarSign className="w-3.5 h-3.5 text-rose-500" />
      };
    }

    if (category.includes('Impersonation')) {
      return {
        className: 'bg-rose-50 border border-rose-200 text-rose-600 hover:bg-rose-100 hover:border-rose-300',
        icon: <Building2 className="w-3.5 h-3.5 text-rose-500" />
      };
    }

    if (category.includes('Tamil') || category.includes('Multilingual')) {
      return {
        className: 'bg-rose-50 border border-rose-200 text-rose-600 hover:bg-rose-100 hover:border-rose-300',
        icon: <Languages className="w-3.5 h-3.5 text-rose-500" />
      };
    }

    return {
      className: 'bg-white border border-gray-200 text-gray-700 hover:border-orange-400 hover:text-orange-500',
      icon: <Sparkles className="w-3.5 h-3.5 text-orange-500" />
    };
  };

  return (
    <motion.div
      initial={{ x: -20, opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      transition={{ delay: 0.1, duration: 0.4, ease: 'easeOut' }}
      className="mb-6"
    >
      <div className="flex items-center gap-2 mb-3">
        <Sparkles className="w-4 h-4 text-orange-500" />
        <span className="text-gray-400 text-xs font-bold uppercase tracking-widest">
          Quick-Load Benchmark Test Scenarios:
        </span>
      </div>

      <div className="flex flex-wrap gap-2">
        {samples.map((sample, i) => {
          const { className, icon } = getStyleAndIcon(sample.category);
          return (
            <motion.button
              key={sample.id}
              onClick={() => onSelectSample(sample)}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.04, duration: 0.3 }}
              whileHover={{ scale: 1.05, y: -2 }}
              whileTap={{ scale: 0.95 }}
              className={`inline-flex items-center gap-2 rounded-full px-4 py-1.5 text-xs font-medium transition shadow-2xs cursor-pointer ${className}`}
            >
              {icon}
              <span>{sample.category}</span>
            </motion.button>
          );
        })}
      </div>
    </motion.div>
  );
}
