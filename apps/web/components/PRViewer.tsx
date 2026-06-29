"use client";

import { useState, useEffect } from "react";

export default function PRViewer({ uploadId, prNumber, prBranch, onApproved }: { uploadId: string, prNumber: string, prBranch: string, onApproved: () => void }) {
  const [diff, setDiff] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [loadingAction, setLoadingAction] = useState<string | null>(null);

  useEffect(() => {
    const fetchDiff = async () => {
      setLoading(true);
      try {
        const res = await fetch(`http://localhost:8000/api/agents/${uploadId}/pulls/${prNumber}/diff`);
        if (res.ok) {
          const data = await res.json();
          setDiff(data.diff);
        }
      } catch (e) {
        console.error("Failed to fetch diff", e);
      } finally {
        setLoading(false);
      }
    };
    fetchDiff();
  }, [uploadId, prNumber]);

  const handleAction = async (action: 'deploy' | 'approve') => {
    setLoadingAction(action);
    try {
      if (action === 'deploy') {
        const res = await fetch(`http://localhost:8000/api/agents/${uploadId}/pulls/${prNumber}:deploy-preview`, { method: "POST" });
        if (res.ok) {
          const data = await res.json();
          alert(`Deploy Preview triggered successfully!\nURL: ${data.url}`);
          window.open(data.url, '_blank');
        } else {
          const data = await res.json();
          alert(`Failed to deploy: ${data.detail || 'Unknown error'}`);
        }
      } else if (action === 'approve') {
        const res = await fetch(`http://localhost:8000/api/agents/${uploadId}/pulls/${prNumber}:approve`, { method: "POST" });
        if (res.ok) {
          alert("PR Approved and Merged!");
          onApproved();
        } else {
          const data = await res.json();
          alert(`Failed to approve: ${data.detail || 'Unknown error'}`);
        }
      }
    } catch (e) {
      console.error(`Action ${action} failed`, e);
      alert(`Action ${action} failed`);
    } finally {
      setLoadingAction(null);
    }
  };

  return (
    <div className="border rounded-lg bg-white shadow-sm flex flex-col mt-4">
      <div className="bg-gray-100 px-4 py-3 border-b rounded-t-lg font-medium flex justify-between items-center">
        <span>Pull Request #{prNumber} (Branch: {prBranch})</span>
        <div className="flex gap-2">
          <button
            onClick={() => handleAction('deploy')}
            disabled={loadingAction !== null}
            className="bg-indigo-600 text-white px-3 py-1 rounded text-sm disabled:opacity-50"
          >
            {loadingAction === 'deploy' ? 'Deploying...' : 'Deploy Preview'}
          </button>
          <button
            onClick={() => handleAction('approve')}
            disabled={loadingAction !== null}
            className="bg-green-600 text-white px-3 py-1 rounded text-sm disabled:opacity-50"
          >
            {loadingAction === 'approve' ? 'Approving...' : 'Approve PR'}
          </button>
        </div>
      </div>
      <div className="p-4 bg-gray-50 overflow-auto max-h-96 text-sm font-mono">
        {loading ? (
          <div className="text-gray-500">Loading diff...</div>
        ) : diff ? (
          <pre className="whitespace-pre-wrap text-gray-900">{diff}</pre>
        ) : (
          <div className="text-gray-500">No diff available.</div>
        )}
      </div>
    </div>
  );
}
