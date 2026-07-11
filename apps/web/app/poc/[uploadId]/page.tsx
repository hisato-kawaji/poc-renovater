"use client";
import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { Activity, MessageSquare, Code2, Server, CheckCircle2, AlertCircle, Clock } from "lucide-react";

import CharterChat from "../../../components/CharterChat";
import IssueList from "../../../components/IssueList";
import PRViewer from "../../../components/PRViewer";
import { JobTracker } from "../../../components/JobTracker";
import { ErrorModal } from "../../../components/ErrorModal";
import { HITLModal } from "../../../components/HITLModal";
import DeploymentsViewer from "../../../components/DeploymentsViewer";

const statusIcons: Record<string, React.ReactNode> = {
  ANALYZING: <Activity size={18} />,
  PASSED: <CheckCircle2 size={18} />,
  REJECTED: <AlertCircle size={18} />,
  REGISTERED: <Code2 size={18} />,
  PLANNING: <Clock size={18} />,
  PR_OPEN: <Code2 size={18} />,
  PREVIEW_READY: <Server size={18} />,
  MERGED: <CheckCircle2 size={18} />,
  ERROR: <AlertCircle size={18} />,
  IDLE: <Clock size={18} />,
};

const statusColors: Record<string, string> = {
  ANALYZING: "bg-blue-500/10 text-blue-600 border-blue-500/20",
  PASSED: "bg-emerald-500/10 text-emerald-600 border-emerald-500/20",
  REJECTED: "bg-red-500/10 text-red-600 border-red-500/20",
  REGISTERED: "bg-purple-500/10 text-purple-600 border-purple-500/20",
  PLANNING: "bg-indigo-500/10 text-indigo-600 border-indigo-500/20",
  PR_OPEN: "bg-amber-500/10 text-amber-600 border-amber-500/20",
  PREVIEW_READY: "bg-cyan-500/10 text-cyan-600 border-cyan-500/20",
  CHANGES_REQUESTED: "bg-rose-500/10 text-rose-600 border-rose-500/20",
  MERGED: "bg-emerald-500/10 text-emerald-600 border-emerald-500/20",
  ERROR: "bg-red-500/10 text-red-600 border-red-500/20",
  IDLE: "bg-zinc-500/10 text-zinc-600 border-zinc-500/20",
};

export default function PoCDetail() {
  const params = useParams();
  const uploadId = params.uploadId as string;
  const [activeTab, setActiveTab] = useState("overview");

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);

  const getJobTrackerProps = (apiStatus: string) => {
    let currentStepId = "UPLOADED";
    let status: "IN_PROGRESS" | "COMPLETED" | "FAILED" | "BLOCKED" = "IN_PROGRESS";
    switch(apiStatus) {
      case "ANALYZING": currentStepId = "CHARTER_EVALUATION"; status = "IN_PROGRESS"; break;
      case "PASSED": currentStepId = "CHARTER_EVALUATION"; status = "COMPLETED"; break;
      case "REJECTED": currentStepId = "CHARTER_EVALUATION"; status = "BLOCKED"; break;
      case "REGISTERED": currentStepId = "GITHUB_REPO_CREATED"; status = "COMPLETED"; break;
      case "PLANNING": currentStepId = "ISSUES_PLANNED"; status = "IN_PROGRESS"; break;
      case "PR_OPEN": currentStepId = "PR_CREATED"; status = "COMPLETED"; break;
      case "PREVIEW_READY": currentStepId = "PREVIEW_DEPLOYED"; status = "COMPLETED"; break;
      case "MERGED": currentStepId = "MERGED"; status = "COMPLETED"; break;
      case "ERROR": currentStepId = "IMPLEMENTATION_START"; status = "FAILED"; break;
    }
    return { currentStepId, status };
  };

  const trackerProps = result ? getJobTrackerProps(result.status) : null;

  useEffect(() => {
    if (!uploadId) return;
    const interval = setInterval(async () => {
      try {
        const res = await fetch(`/api/agents/${uploadId}`);
        if (res.ok) {
          const data = await res.json();
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          setResult((prev: any) => {
            if (!prev) return data;
            const next = { ...prev, ...data };
            if (JSON.stringify(prev) !== JSON.stringify(next)) {
              if (prev.status !== next.status || ['REJECTED', 'ERROR'].includes(data.status)) {
                setUploading(false);
              }
              return next;
            }
            return prev;
          });
          setLoading(false);
        }
      } catch (e) {
        console.error("Polling error", e);
      }
    }, 3000);
    return () => clearInterval(interval);
  }, [uploadId]);

  if (loading && !result) {
    return (
      <div className="flex items-center justify-center h-full min-h-screen bg-zinc-50">
        <div className="animate-spin rounded-full h-8 w-8 border-2 border-zinc-300 border-t-indigo-600"></div>
      </div>
    );
  }

  const tabs = [
    { id: "overview", label: "Overview", icon: Activity },
    { id: "chat", label: "Interactive Chat", icon: MessageSquare },
    { id: "issues", label: "Issues & Implementation", icon: Code2 },
    { id: "deployments", label: "Deployments", icon: Server },
  ];

  return (
    <div className="p-8 max-w-7xl mx-auto min-h-screen flex flex-col">
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-zinc-900 flex items-center gap-4">
            PoC: <span className="font-mono text-zinc-500">{uploadId.substring(0, 8)}...</span>
          </h1>
          {result?.repo && (
            <a href={result.repo.url} target="_blank" rel="noopener noreferrer" className="text-indigo-600 hover:underline font-medium mt-1 inline-block">
              {result.repo.fullName}
            </a>
          )}
        </div>
        
        {result && (
          <div className={`flex items-center gap-2 px-4 py-2 rounded-full border shadow-sm ${statusColors[result.status] || "bg-zinc-100 text-zinc-600 border-zinc-200"}`}>
            {statusIcons[result.status]}
            <span className="font-semibold text-sm tracking-wide">{result.status}</span>
          </div>
        )}
      </div>

      {/* Tabs Navigation */}
      <div className="flex space-x-1 bg-white p-1.5 rounded-2xl mb-6 shadow-sm border border-zinc-200 overflow-x-auto">
        {tabs.map((tab) => {
          const isActive = activeTab === tab.id;
          const Icon = tab.icon;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-6 py-3 rounded-xl font-medium text-sm transition-all relative ${
                isActive ? "text-indigo-700" : "text-zinc-500 hover:text-zinc-700 hover:bg-zinc-50"
              }`}
            >
              {isActive && (
                <motion.div
                  layoutId="active-tab"
                  className="absolute inset-0 bg-indigo-50/50 rounded-xl shadow-sm border border-indigo-100/50"
                  initial={false}
                  transition={{ type: "spring", stiffness: 300, damping: 30 }}
                />
              )}
              <span className="relative z-10 flex items-center gap-2">
                <Icon size={16} />
                {tab.label}
              </span>
            </button>
          );
        })}
      </div>

      {/* Tab Content */}
      <div className="flex-1 bg-white rounded-3xl shadow-xl shadow-zinc-200/40 border border-zinc-200 overflow-hidden relative min-h-[500px]">
        <AnimatePresence mode="wait">
          <motion.div
            key={activeTab}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.2 }}
            className="absolute inset-0 overflow-auto p-8"
          >
            {activeTab === "overview" && (
              <div className="space-y-8">
                {trackerProps && (
                  <div className="mb-8">
                    <JobTracker currentStepId={trackerProps.currentStepId} status={trackerProps.status} />
                  </div>
                )}
                
                {result?.status === 'PASSED' && (
                  <div className="bg-gradient-to-r from-emerald-50 to-teal-50 border border-emerald-100 p-6 rounded-xl shadow-sm flex items-center justify-between">
                    <div>
                      <h3 className="font-bold text-emerald-800 text-lg">Charter Evaluation Passed</h3>
                      <p className="text-emerald-600 text-sm mt-1">Ready to create a GitHub repository for this PoC.</p>
                    </div>
                    <button 
                      onClick={async () => {
                        setUploading(true);
                        try {
                          await fetch(`/api/agents/${uploadId}:register`, { method: 'POST' });
                        } catch (e) {
                          console.error(e);
                        }
                      }}
                      disabled={uploading}
                      className="bg-emerald-600 hover:bg-emerald-700 text-white px-6 py-2.5 rounded-lg font-medium shadow-md shadow-emerald-200 transition-colors"
                    >
                      {uploading ? "Processing..." : "Register to GitHub"}
                    </button>
                  </div>
                )}
                
                {result?.status === 'REGISTERED' && (
                  <div className="bg-gradient-to-r from-indigo-50 to-purple-50 border border-indigo-100 p-6 rounded-xl shadow-sm flex items-center justify-between">
                    <div>
                      <h3 className="font-bold text-indigo-800 text-lg">Repository Created</h3>
                      <p className="text-indigo-600 text-sm mt-1">Next step: Let the agent plan the necessary issues.</p>
                    </div>
                    <button 
                      onClick={async () => {
                        setUploading(true);
                        try {
                          await fetch(`/api/agents/${uploadId}/issues:plan`, { method: 'POST' });
                          setActiveTab("issues"); // automatically switch to issues tab
                        } catch (e) {
                          console.error(e);
                        }
                      }}
                      disabled={uploading}
                      className="bg-indigo-600 hover:bg-indigo-700 text-white px-6 py-2.5 rounded-lg font-medium shadow-md shadow-indigo-200 transition-colors"
                    >
                      {uploading ? "Planning..." : "Plan Issues"}
                    </button>
                  </div>
                )}

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="border border-zinc-200 rounded-xl overflow-hidden flex flex-col bg-zinc-50/50">
                    <h3 className="text-sm font-bold tracking-wide uppercase text-zinc-500 bg-zinc-100/50 px-4 py-3 border-b border-zinc-200">Charter Evaluation</h3>
                    <pre className="p-4 overflow-auto text-xs max-h-96 text-zinc-700 flex-1 bg-white">
                      {JSON.stringify(result?.charter, null, 2)}
                    </pre>
                  </div>
                  <div className="border border-zinc-200 rounded-xl overflow-hidden flex flex-col bg-zinc-50/50">
                    <h3 className="text-sm font-bold tracking-wide uppercase text-zinc-500 bg-zinc-100/50 px-4 py-3 border-b border-zinc-200">Technical Analysis</h3>
                    <pre className="p-4 overflow-auto text-xs max-h-96 text-zinc-700 flex-1 bg-white">
                      {JSON.stringify(result?.analysis, null, 2)}
                    </pre>
                  </div>
                </div>
              </div>
            )}

            {activeTab === "chat" && (
              <div className="h-full max-w-4xl mx-auto flex flex-col border border-zinc-200 rounded-xl overflow-hidden shadow-sm">
                <CharterChat uploadId={uploadId} />
              </div>
            )}

            {activeTab === "issues" && (
              <div className="space-y-8 max-w-5xl mx-auto">
                {['PLANNING', 'PR_OPEN', 'PREVIEW_READY', 'MERGED'].includes(result?.status) ? (
                  <>
                    <IssueList uploadId={uploadId} />
                    
                    {['PR_OPEN', 'PREVIEW_READY'].includes(result?.status) && (
                      <div className="mt-12 pt-8 border-t border-zinc-200">
                        <PRViewer 
                          uploadId={uploadId} 
                          prNumber={result.prNumber} 
                          prBranch={result.prBranch} 
                          onApproved={() => setResult({...result, status: 'MERGED'})}
                        />
                      </div>
                    )}

                    {result?.status === 'MERGED' && (
                      <div className="mt-8 p-6 bg-gradient-to-r from-emerald-50 to-teal-50 border border-emerald-200 text-emerald-900 rounded-xl flex items-center gap-5 shadow-sm">
                        <div className="text-5xl drop-shadow-md">🎉</div>
                        <div>
                          <h3 className="text-xl font-bold mb-1">Implementation Complete</h3>
                          <p className="text-sm text-emerald-700">The Pull Request has been merged. Production deployment has started automatically.</p>
                        </div>
                      </div>
                    )}
                  </>
                ) : (
                  <div className="text-center py-20 bg-zinc-50 border border-dashed border-zinc-300 rounded-2xl">
                    <Code2 size={48} className="mx-auto text-zinc-300 mb-4" />
                    <h3 className="text-lg font-medium text-zinc-900">No Issues Planned Yet</h3>
                    <p className="text-zinc-500 max-w-md mx-auto mt-2">
                      Please proceed through the Overview tab to Register the repository and Plan issues first.
                    </p>
                  </div>
                )}
              </div>
            )}

            {activeTab === "deployments" && (
              <div className="max-w-5xl mx-auto">
                <DeploymentsViewer uploadId={uploadId} />
              </div>
            )}
          </motion.div>
        </AnimatePresence>
      </div>

      <ErrorModal 
        isOpen={result?.status === 'ERROR'} 
        errorMessage={result?.errorDetails || "An unexpected error occurred during the pipeline execution."}
        onRetry={async () => {
          if (uploadId) {
            const jobId = result.failedJobId || "job-implement_issue";
            try {
              await fetch(`/api/agents/${uploadId}/jobs/${jobId}/retry`, { method: "POST" });
              setResult({...result, status: 'ANALYZING'});
            } catch (e) {
              console.error(e);
            }
          }
        }} 
        onCancel={() => setResult(null)} 
      />
      <HITLModal
        isOpen={result?.status === 'REJECTED'}
        blockedReason="Charter evaluation was rejected or needs manual intervention. Please check the Chat tab to discuss changes."
        requiresEnvVars={false}
        onApprove={() => setResult({...result, status: 'PASSED'})}
        onCancel={() => setResult(null)}
      />
    </div>
  );
}
