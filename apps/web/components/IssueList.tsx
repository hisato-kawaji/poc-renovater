"use client";

import { useState, useEffect } from "react";
import PRViewer from "./PRViewer";

interface Issue {
  id: string;
  title: string;
  body: string;
  type: string;
  priority: number;
  status: string;
  url?: string;
  prUrl?: string;
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export default function IssueList({ uploadId, agentResult }: { uploadId: string, agentResult?: any }) {
  const [issues, setIssues] = useState<Issue[]>([]);
  const [loading, setLoading] = useState(true);
  const [implementingId, setImplementingId] = useState<string | null>(null);

  useEffect(() => {
    const fetchIssues = async () => {
      try {
        const res = await fetch(`/api/agents/${uploadId}/issues`);
        if (res.ok) {
          const data = await res.json();
          // Sort by priority (1 is highest)
          data.sort((a: Issue, b: Issue) => a.priority - b.priority);
          setIssues(data);
        }
      } catch (e) {
        console.error("Failed to fetch issues", e);
      } finally {
        setLoading(false);
      }
    };

    fetchIssues();
    const interval = setInterval(fetchIssues, 5000); // poll to see status updates
    return () => clearInterval(interval);
  }, [uploadId]);

  const handleImplement = async (issueId: string) => {
    setImplementingId(issueId);
    try {
      // The API returns PR URL, but since it's a background task, the endpoint is now async
      const res = await fetch(`/api/agents/${uploadId}/issues/${issueId}:implement`, {
        method: "POST"
      });
      if (res.ok) {
        alert("Implementation task started in the background!");
      } else {
        const err = await res.json();
        alert(`Error: ${err.detail || 'Implementation failed'}`);
      }
    } catch (e) {
      console.error("Implementation error", e);
      alert("Failed to start implementation.");
    } finally {
      setImplementingId(null);
    }
  };

  if (loading && issues.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-zinc-400">
        <div className="animate-spin rounded-full h-8 w-8 border-2 border-zinc-300 border-t-indigo-600 mb-4"></div>
        Loading issues...
      </div>
    );
  }

  if (issues.length === 0) {
    return (
      <div className="text-center py-20 bg-zinc-50 border border-dashed border-zinc-300 rounded-2xl">
        <h3 className="text-lg font-medium text-zinc-900">No issues found.</h3>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {issues.map(issue => (
        <div key={issue.id} className="border border-zinc-200 rounded-2xl p-6 bg-white shadow-sm hover:shadow-md transition-shadow flex flex-col gap-3 group relative overflow-hidden">
          <div className="flex justify-between items-start">
            <div className="flex flex-col">
              <h4 className="text-xl font-bold text-zinc-900 group-hover:text-indigo-700 transition-colors">{issue.title}</h4>
              {issue.id.startsWith("autofix-") && (
                <span className="text-xs font-semibold text-rose-500 mt-1">🔧 AUTO-FIX DETECTED</span>
              )}
            </div>
            <span className={`px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wide border ${
              issue.status === 'open' ? 'bg-blue-50 text-blue-700 border-blue-200' :
              issue.status === 'in_progress' ? (issue.id.startsWith("autofix-") ? 'bg-rose-50 text-rose-700 border-rose-200' : 'bg-amber-50 text-amber-700 border-amber-200') :
              'bg-emerald-50 text-emerald-700 border-emerald-200'
            }`}>
              {issue.status === 'open' ? (issue.id.startsWith("autofix-") ? "WAITING AUTO-FIX" : "WAITING FOR USER") : 
               issue.status === 'in_progress' && issue.id.startsWith("autofix-") ? "AUTO-FIXING (自動対応中)" : 
               issue.status.replace('_', ' ')}
            </span>
          </div>
          <p className="text-zinc-600 line-clamp-2 leading-relaxed">{issue.body}</p>
          <div className="flex flex-wrap gap-4 text-sm mt-3 text-zinc-500 bg-zinc-50 p-3 rounded-xl border border-zinc-100">
            <div className="flex items-center gap-1.5"><span className="uppercase text-xs font-bold tracking-wider text-zinc-400">Type</span> <span className="font-semibold text-zinc-700">{issue.type}</span></div>
            <div className="flex items-center gap-1.5"><span className="uppercase text-xs font-bold tracking-wider text-zinc-400">Priority</span> <span className="font-semibold text-zinc-700">P{issue.priority}</span></div>
            {issue.url && (
              <a href={issue.url} target="_blank" rel="noreferrer" className="flex items-center gap-1 text-indigo-600 hover:text-indigo-700 font-medium hover:underline">
                View on GitHub
              </a>
            )}
            {issue.prUrl && (
              <a href={issue.prUrl} target="_blank" rel="noreferrer" className="flex items-center gap-1 text-purple-600 hover:text-purple-700 font-medium hover:underline">
                View PR
              </a>
            )}
          </div>
          <div className="mt-4 flex justify-end">
            <button 
              onClick={() => handleImplement(issue.id)}
              disabled={implementingId === issue.id || issue.status !== 'open' || issue.id.startsWith("autofix-")}
              className="bg-indigo-600 hover:bg-indigo-700 text-white px-6 py-2.5 rounded-xl font-medium shadow-sm shadow-indigo-200 disabled:opacity-50 disabled:cursor-not-allowed transition-all active:scale-[0.98]"
            >
              {implementingId === issue.id ? "Starting..." : issue.id.startsWith("autofix-") && issue.status === 'open' ? "Auto-starting..." : "Implement"}
            </button>
          </div>

          {/* Render PRViewer directly underneath the issue being worked on! */}
          {issue.status === 'in_progress' && issue.prUrl && agentResult?.status && ['PR_OPEN', 'PREVIEW_READY'].includes(agentResult.status) && (
            <div className="mt-6 pt-6 border-t border-zinc-200">
              <div className="bg-amber-50 text-amber-800 p-3 rounded-lg text-sm font-semibold mb-4 border border-amber-200">
                🔔 プレビューおよびマージの判断をお待ちしています
              </div>
              <PRViewer 
                uploadId={uploadId} 
                prNumber={parseInt(issue.prUrl.split("/").pop() || "0")} 
                prBranch={agentResult.prBranch || "main"} 
                onApproved={async () => {
                  // Mark as merged
                  window.location.reload();
                }}
              />
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
