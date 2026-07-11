"use client";

import { useState, useEffect } from "react";
import { Server, ExternalLink, AlertTriangle, Loader2 } from "lucide-react";

interface DeploymentsViewerProps {
  uploadId: string;
}

export default function DeploymentsViewer({ uploadId }: DeploymentsViewerProps) {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const [deployments, setDeployments] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!uploadId) return;
    const fetchDeps = async () => {
      try {
        const res = await fetch(`/api/agents/${uploadId}/deployments`);
        if (res.ok) {
          const data = await res.json();
          setDeployments(data);
        }
      } catch (e) {
        console.error("Failed to fetch deployments", e);
      } finally {
        setLoading(false);
      }
    };

    const interval = setInterval(fetchDeps, 5000);
    fetchDeps();

    return () => clearInterval(interval);
  }, [uploadId]);

  if (loading && deployments.length === 0) {
    return (
      <div className="flex justify-center p-12 text-zinc-400">
        <Loader2 className="animate-spin w-8 h-8 text-indigo-500" />
      </div>
    );
  }

  if (deployments.length === 0) {
    return (
      <div className="text-center py-20 bg-zinc-50 border border-dashed border-zinc-300 rounded-2xl">
        <Server size={48} className="mx-auto text-zinc-300 mb-4" />
        <h3 className="text-lg font-medium text-zinc-900">No Deployments Yet</h3>
        <p className="text-zinc-500 max-w-md mx-auto mt-2">
          Deployments will appear here once you approve Pull Requests or trigger Previews.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {deployments.map((dep, idx) => (
        <div key={idx} className="p-6 border border-zinc-200 rounded-2xl flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-white shadow-sm hover:shadow-md transition-shadow relative overflow-hidden group">
          {dep.prNumber === 0 && (
            <div className="absolute top-0 left-0 w-1 h-full bg-emerald-500" />
          )}
          {dep.prNumber !== 0 && (
            <div className="absolute top-0 left-0 w-1 h-full bg-indigo-500" />
          )}
          
          <div className="pl-4">
            <h4 className="text-lg font-bold text-zinc-900 flex items-center gap-2">
              <Server size={18} className={dep.prNumber === 0 ? "text-emerald-500" : "text-indigo-500"} />
              {dep.prNumber === 0 ? "Production Deployment" : `Preview Deployment (PR #${dep.prNumber})`}
            </h4>
            <p className="text-sm text-zinc-500 mt-1 font-mono bg-zinc-100 inline-block px-2 py-0.5 rounded">Service: {dep.service}</p>
          </div>
          
          <div>
            {dep.status === "ready" && dep.url ? (
              <a 
                href={dep.url} 
                target="_blank" 
                rel="noreferrer" 
                className="inline-flex items-center gap-2 bg-indigo-50 hover:bg-indigo-100 text-indigo-700 font-medium px-5 py-2.5 rounded-xl transition-colors border border-indigo-200"
              >
                Open App <ExternalLink size={16} />
              </a>
            ) : dep.status === "failed" ? (
              <div className="inline-flex items-center gap-2 bg-red-50 text-red-700 font-medium px-5 py-2.5 rounded-xl border border-red-200">
                <AlertTriangle size={16} />
                <div className="flex flex-col">
                  <span>Deployment Failed</span>
                  {dep.error && <span className="text-xs text-red-500 font-normal">{dep.error}</span>}
                </div>
              </div>
            ) : (
              <div className="inline-flex items-center gap-2 bg-amber-50 text-amber-700 font-medium px-5 py-2.5 rounded-xl border border-amber-200">
                <Loader2 size={16} className="animate-spin" />
                Deploying...
              </div>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}
