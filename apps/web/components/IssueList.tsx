"use client";

import { useState, useEffect } from "react";

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

export default function IssueList({ uploadId, onImplemented }: { uploadId: string, onImplemented: (prUrl: string, branch: string) => void }) {
  const [issues, setIssues] = useState<Issue[]>([]);
  const [loading, setLoading] = useState(true);
  const [implementingId, setImplementingId] = useState<string | null>(null);

  const fetchIssues = async () => {
    try {
      const res = await fetch(`http://localhost:8000/api/agents/${uploadId}/issues`);
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

  useEffect(() => {
    fetchIssues();
    const interval = setInterval(fetchIssues, 5000); // poll to see status updates
    return () => clearInterval(interval);
  }, [uploadId]);

  const handleImplement = async (issueId: string) => {
    setImplementingId(issueId);
    try {
      // The API returns PR URL, but since it's a background task, the endpoint is now async
      const res = await fetch(`http://localhost:8000/api/agents/${uploadId}/issues/${issueId}:implement`, {
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
      fetchIssues(); // refresh status
    }
  };

  if (loading && issues.length === 0) {
    return <div className="text-gray-500">Loading issues...</div>;
  }

  if (issues.length === 0) {
    return <div className="text-gray-500">No issues found.</div>;
  }

  return (
    <div className="space-y-4">
      {issues.map(issue => (
        <div key={issue.id} className="border rounded-lg p-4 bg-white shadow-sm flex flex-col gap-2">
          <div className="flex justify-between items-start">
            <h4 className="text-lg font-semibold">{issue.title}</h4>
            <span className={`px-2 py-1 rounded text-xs font-medium uppercase ${
              issue.status === 'open' ? 'bg-blue-100 text-blue-800' :
              issue.status === 'in_progress' ? 'bg-yellow-100 text-yellow-800' :
              'bg-green-100 text-green-800'
            }`}>
              {issue.status}
            </span>
          </div>
          <p className="text-sm text-gray-600 line-clamp-2">{issue.body}</p>
          <div className="flex gap-4 text-sm mt-2 text-gray-500">
            <span>Type: <span className="font-medium text-gray-700">{issue.type}</span></span>
            <span>Priority: <span className="font-medium text-gray-700">P{issue.priority}</span></span>
            {issue.url && (
              <a href={issue.url} target="_blank" rel="noreferrer" className="text-blue-600 hover:underline">
                View on GitHub
              </a>
            )}
            {issue.prUrl && (
              <a href={issue.prUrl} target="_blank" rel="noreferrer" className="text-purple-600 hover:underline">
                View PR
              </a>
            )}
          </div>
          <div className="mt-4 flex justify-end">
            <button 
              onClick={() => handleImplement(issue.id)}
              disabled={implementingId !== null || issue.status !== 'open'}
              className="bg-indigo-600 text-white px-4 py-2 rounded disabled:opacity-50"
            >
              {implementingId === issue.id ? "Starting..." : "Implement"}
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}
