import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import InspectorView from './pages/InspectorView';
import BatchView from './pages/BatchView';
import AnalyticsView from './pages/AnalyticsView';
import AdminView from './pages/AdminView';
import CustomCursor from './components/CustomCursor';
import GradientMesh from './components/GradientMesh';
import { fetchModelInfo } from './services/api';

export default function App() {
  const [activeTab, setActiveTab] = useState('inspector');
  const [modelInfo, setModelInfo] = useState(null);

  useEffect(() => {
    fetchModelInfo()
      .then(setModelInfo)
      .catch(console.error);
  }, []);

  return (
    <div className="relative min-h-screen bg-[#FAFAFA] flex flex-col text-gray-900 overflow-x-hidden selection:bg-orange-100 selection:text-orange-900">
      {/* Performance-optimized Custom Cursor & Background Canvas */}
      <CustomCursor />
      <GradientMesh />

      {/* Main Application Container */}
      <div className="relative z-10 flex flex-col min-h-screen">
        {/* Navigation Header */}
        <Navbar
          activeTab={activeTab}
          setActiveTab={setActiveTab}
          modelInfo={modelInfo}
        />

        {/* Main Content Area */}
        <main className="flex-1">
          {activeTab === 'inspector' && <InspectorView />}
          {activeTab === 'batch' && <BatchView />}
          {activeTab === 'analytics' && <AnalyticsView />}
          {activeTab === 'admin' && <AdminView />}
        </main>

        {/* Footer */}
        <footer className="border-t border-gray-200/80 py-6 px-8 text-center text-xs text-gray-500 bg-white/80 backdrop-blur-xs">
          <div className="max-w-7xl mx-auto flex flex-col sm:flex-row justify-between items-center gap-2">
            <div>
              <strong className="text-gray-800 font-semibold">Veritas Recruitment Fraud & Scam Detection Platform</strong> &copy; 2026. Production ML & Explainability Defense.
            </div>
            <div>
              Decision-Support Intelligence &bull; Trained on Stratified Kaggle EMSCAD Dataset (70/30 Resampled Distribution)
            </div>
          </div>
        </footer>
      </div>
    </div>
  );
}
