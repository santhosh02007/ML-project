import React, { useState } from 'react';
import { Flag, X, CheckCircle2 } from 'lucide-react';
import { submitReport } from '../services/api';

export default function ReportModal({ isOpen, onClose, jobData, onReportSuccess }) {
  const [reason, setReason] = useState('asked_for_payment');
  const [description, setDescription] = useState('');
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState(null);

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await submitReport({
        job_id: jobData?.job_id || null,
        job_title: jobData?.title || 'Unknown Job',
        company: jobData?.company || 'Unknown Company',
        job_description: jobData?.description || '',
        report_reason: reason,
        description: description,
        reporter_email: email
      });
      setSuccess(true);
      setTimeout(() => {
        setSuccess(false);
        onClose();
        if (onReportSuccess) onReportSuccess();
      }, 1500);
    } catch (err) {
      setError(err.message || 'Failed to submit report.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/40 backdrop-blur-xs flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl border border-gray-200 shadow-xl w-full max-w-lg p-6 relative">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-gray-400 hover:text-gray-600 transition"
        >
          <X className="w-5 h-5" />
        </button>

        <div className="flex items-center gap-3 mb-5">
          <div className="w-10 h-10 rounded-xl bg-rose-50 border border-rose-100 flex items-center justify-center text-rose-500">
            <Flag className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-gray-900">Report Fraudulent Job Posting</h3>
            <div className="text-xs text-gray-500">Help protect candidate communities from predatory recruitment scams</div>
          </div>
        </div>

        {success ? (
          <div className="py-8 text-center flex flex-col items-center gap-2">
            <CheckCircle2 className="w-12 h-12 text-green-500" />
            <h4 className="text-base font-bold text-gray-900">Report Logged for Admin Verification</h4>
            <p className="text-xs text-gray-500 max-w-sm">
              Thank you for reporting. Our security team will review and incorporate verified samples into the continuous model retraining pipeline.
            </p>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="flex flex-col gap-4">
            {error && (
              <div className="bg-rose-50 border border-rose-200 p-3 rounded-lg text-rose-700 text-xs">
                {error}
              </div>
            )}

            <div>
              <label className="block text-xs font-semibold text-gray-700 mb-1.5">
                Primary Scam Indicator / Reason *
              </label>
              <select
                value={reason}
                onChange={(e) => setReason(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-lg bg-white border border-gray-300 text-gray-900 text-sm focus:outline-none focus:ring-2 focus:ring-orange-400 focus:border-orange-500"
              >
                <option value="asked_for_payment">Demanded money / registration or equipment fee</option>
                <option value="fake_company">Impersonating a known company or fake brand</option>
                <option value="suspicious_recruiter">Suspicious recruiter / Telegram/WhatsApp only</option>
                <option value="personal_info_requested">Requested OTP / Bank details / Aadhaar / PAN</option>
                <option value="fake_interview">Fake interview / Check cashing scheme</option>
                <option value="other">Other deceptive recruitment tactic</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-gray-700 mb-1.5">
                Additional Evidence / Details (Optional)
              </label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="E.g. Recruiter insisted on wiring $150 via Bitcoin before scheduling call..."
                rows={3}
                className="w-full px-3.5 py-2.5 rounded-lg bg-white border border-gray-300 text-gray-900 text-sm focus:outline-none focus:ring-2 focus:ring-orange-400 focus:border-orange-500 resize-y"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-gray-700 mb-1.5">
                Your Email (Optional, for verification updates)
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="candidate@example.com"
                className="w-full px-3.5 py-2.5 rounded-lg bg-white border border-gray-300 text-gray-900 text-sm focus:outline-none focus:ring-2 focus:ring-orange-400 focus:border-orange-500"
              />
            </div>

            <div className="flex justify-end gap-2.5 pt-2">
              <button
                type="button"
                onClick={onClose}
                className="bg-white border border-gray-300 text-gray-700 hover:bg-gray-50 rounded-lg px-4 py-2 text-sm font-medium transition cursor-pointer"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={loading}
                className="bg-rose-500 hover:bg-rose-600 text-white rounded-lg px-5 py-2 text-sm font-medium shadow-sm transition cursor-pointer disabled:opacity-50"
              >
                {loading ? 'Submitting...' : 'Submit Scam Report'}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
