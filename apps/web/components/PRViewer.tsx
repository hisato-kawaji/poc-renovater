"use client";

import { useState, useEffect } from "react";
import { GitPullRequest, Check, MonitorPlay, Loader2 } from "lucide-react";

export default function PRViewer({ uploadId, prNumber, prBranch, onApproved }: { uploadId: string, prNumber: string, prBranch: string, onApproved: () => void }) {
  const [diff, setDiff] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [loadingAction, setLoadingAction] = useState<string | null>(null);

  useEffect(() => {
    const fetchDiff = async () => {
      setLoading(true);
      try {
        const res = await fetch(`/api/agents/${uploadId}/pulls/${prNumber}/diff`);
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
        const res = await fetch(`/api/agents/${uploadId}/pulls/${prNumber}:deploy-preview`, { method: "POST" });
        if (res.ok) {
           alert("Deploy Preview started in the background! Please wait for a few minutes while it builds and deploys.");
           // Start polling for deployment
           const checkDeploy = setInterval(async () => {
              try {
                  const depRes = await fetch(`/api/agents/${uploadId}/deployments`);
                  if (depRes.ok) {
                     const deployments = await depRes.json();
                     // eslint-disable-next-line @typescript-eslint/no-explicit-any
                     const myDeploy = deployments.find((d: any) => d.prNumber === parseInt(prNumber) && (d.status === "ready" || d.status === "failed"));
                     if (myDeploy) {
                        clearInterval(checkDeploy);
                        setLoadingAction(null);
                        if (myDeploy.status === "ready") {
                           alert(`Deploy Preview completed!\nURL: ${myDeploy.url}`);
                           window.open(myDeploy.url, '_blank');
                        } else {
                           alert(`Deploy Preview failed! See Deployments list below for details.`);
                        }
                     }
                  }
              } catch (e) {
                 console.error("Polling deployments failed", e);
              }
           }, 5000);
           return;
        } else {
          const data = await res.json();
          alert(`Failed to start deploy: ${data.detail || 'Unknown error'}`);
        }
      } else if (action === 'approve') {
        const res = await fetch(`/api/agents/${uploadId}/pulls/${prNumber}:approve`, { method: "POST" });
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
      alert(`Action ${action} failed: ${e instanceof Error ? e.message : String(e)}`);
    } finally {
      setLoadingAction(null);
    }
  };

  return (
    <div className="border border-zinc-200 rounded-2xl bg-white shadow-sm flex flex-col mt-4 overflow-hidden">
      <div className="bg-zinc-50 px-6 py-4 border-b border-zinc-200 flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div className="flex items-center gap-3">
          <div className="bg-indigo-100 p-2 rounded-lg text-indigo-600">
            <GitPullRequest size={20} />
          </div>
          <div>
            <h3 className="font-bold text-zinc-900 text-lg">Pull Request #{prNumber}</h3>
            <p className="text-zinc-500 text-sm font-mono mt-0.5">Branch: {prBranch}</p>
          </div>
        </div>
        
        <div className="flex flex-wrap gap-3">
          <button
            onClick={() => handleAction('deploy')}
            disabled={loadingAction !== null}
            className="flex items-center gap-2 bg-white border border-indigo-200 text-indigo-700 hover:bg-indigo-50 px-4 py-2 rounded-xl text-sm font-medium disabled:opacity-50 transition-colors shadow-sm"
          >
            {loadingAction === 'deploy' ? <Loader2 size={16} className="animate-spin" /> : <MonitorPlay size={16} />}
            Deploy Preview
          </button>
          <button
            onClick={() => handleAction('approve')}
            disabled={loadingAction !== null}
            className="flex items-center gap-2 bg-emerald-600 hover:bg-emerald-700 text-white px-5 py-2 rounded-xl text-sm font-medium disabled:opacity-50 transition-colors shadow-sm shadow-emerald-200"
          >
            {loadingAction === 'approve' ? <Loader2 size={16} className="animate-spin" /> : <Check size={16} />}
            Approve & Merge
          </button>
        </div>
      </div>
      <div className="p-6 bg-zinc-900 overflow-auto max-h-[500px] text-sm font-mono custom-scrollbar">
        {loading ? (
          <div className="text-zinc-500 flex items-center justify-center p-10">
            <Loader2 className="animate-spin mr-2" size={20} />
            Loading diff...
          </div>
        ) : diff ? (
          <pre className="whitespace-pre-wrap text-zinc-300">
            {diff.split('\n').map((line, i) => {
              const isAdded = line.startsWith('+');
              const isRemoved = line.startsWith('-');
              const isMeta = line.startsWith('@@') || line.startsWith('diff --git');
              let className = "px-4 block ";
              if (isAdded) className += "bg-emerald-500/10 text-emerald-400";
              else if (isRemoved) className += "bg-rose-500/10 text-rose-400";
              else if (isMeta) className += "text-blue-400 font-bold";
              else className += "text-zinc-400";
              
              return <span key={i} className={className}>{line}</span>;
            })}
          </pre>
        ) : (
          <div className="text-zinc-500 p-10 text-center border border-dashed border-zinc-700 rounded-xl">
            No diff available or PR contains no valid code changes.
          </div>
        )}
      </div>
    </div>
  );
}
