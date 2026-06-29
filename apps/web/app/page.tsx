"use client";
import { useState, useEffect } from "react";

import CharterChat from "../components/CharterChat";
import IssueList from "../components/IssueList";
import PRViewer from "../components/PRViewer";
import DebugConsole from "../components/DebugConsole";
import PipelineProgress from "../components/PipelineProgress";

export default function Home() {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState<any>(null);

  useEffect(() => {
    if (!result?.uploadId) return;
    const interval = setInterval(async () => {
      try {
        const res = await fetch(`http://localhost:8000/api/agents/${result.uploadId}`);
        if (res.ok) {
          const data = await res.json();
          setResult((prev: any) => {
            if (!prev) return data;
            const next = { ...prev, ...data };
            if (JSON.stringify(prev) !== JSON.stringify(next)) {
              if (['PASSED', 'REJECTED', 'ERROR', 'REGISTERED', 'PLANNING', 'PR_OPEN', 'PREVIEW_READY', 'MERGED'].includes(data.status)) {
                setUploading(false);
              }
              return next;
            }
            return prev;
          });
        }
      } catch (e) {
        console.error("Polling error", e);
      }
    }, 3000);
    return () => clearInterval(interval);
  }, [result?.uploadId]);

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    try {
      const formData = new FormData();
      formData.append("file", file);

      // Upload API
      const upRes = await fetch("http://localhost:8000/api/uploads", {
        method: "POST",
        body: formData,
      });
      const { uploadId } = await upRes.json();
      setResult({ uploadId, status: "ANALYZING" });

      // Analyze API
      await fetch("http://localhost:8000/api/agents:analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ uploadId }),
      });
      // Polling is handled by useEffect
    } catch (e) {
      console.error(e);
      alert("Error occurred");
      setUploading(false);
    }
  };

  return (
    <div className="flex h-screen overflow-hidden bg-gray-50">
      <main className="flex-1 overflow-auto p-8">
        <div className="max-w-4xl mx-auto">
          <h1 className="text-3xl font-bold mb-8 text-gray-900">PoC Foundry</h1>
          
          {result && <PipelineProgress status={result.status} />}

          <div className="mb-8 p-6 border rounded-xl bg-white shadow-sm">
            <label className="block mb-2 font-semibold text-gray-700 text-lg">対象のPoC（.zipファイル）を選択してください</label>
            <p className="text-sm text-gray-500 mb-6">※フォルダをアップロードする場合は、事前に右クリック等でzip圧縮してください。</p>
            <input 
              type="file" 
              accept=".zip" 
              onChange={(e) => setFile(e.target.files?.[0] || null)} 
              className="mb-6 block w-full text-sm text-gray-500
                file:mr-4 file:py-2.5 file:px-4
                file:rounded-lg file:border-0
                file:text-sm file:font-semibold
                file:bg-blue-50 file:text-blue-700
                hover:file:bg-blue-100
                border border-gray-200 rounded-lg p-3 bg-gray-50 cursor-pointer"
            />
            <button 
              onClick={handleUpload} 
              disabled={!file || uploading}
              className="bg-blue-600 hover:bg-blue-700 text-white px-8 py-2.5 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed font-medium shadow-sm transition-colors"
            >
              {uploading ? "Analyzing..." : "Upload & Analyze"}
            </button>
          </div>

          {result && (
            <div className="p-6 border rounded-xl bg-white shadow-sm space-y-8">
              <div>
                <h2 className="text-2xl font-semibold mb-4">Results</h2>
                <div className="p-4 rounded-lg text-white font-bold text-lg bg-gray-800 flex items-center justify-between">
                  <span>Status</span>
                  <span className={result.status === "PASSED" ? "text-green-400" : result.status === "REJECTED" ? "text-red-400" : "text-blue-400"}>{result.status}</span>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="border rounded-lg overflow-hidden flex flex-col">
                  <h3 className="text-lg font-semibold bg-gray-50 px-4 py-3 border-b">Charter Evaluation</h3>
                  <pre className="p-4 overflow-auto text-xs max-h-96 text-gray-800 flex-1">
                    {JSON.stringify(result.charter, null, 2)}
                  </pre>
                </div>
                <div className="border rounded-lg overflow-hidden flex flex-col">
                  <h3 className="text-lg font-semibold bg-gray-50 px-4 py-3 border-b">Interactive Chat</h3>
                  <div className="p-4 flex-1">
                    <CharterChat uploadId={result.uploadId} />
                  </div>
                </div>
              </div>

              <div className="border rounded-lg overflow-hidden">
                <h3 className="text-lg font-semibold bg-gray-50 px-4 py-3 border-b">Technical Analysis</h3>
                <pre className="p-4 overflow-auto text-xs max-h-64 text-gray-800">
                  {JSON.stringify(result.analysis, null, 2)}
                </pre>
              </div>

              {result.status === 'PASSED' && (
                <div className="mt-4">
                  <button 
                    onClick={async () => {
                      setUploading(true);
                      try {
                        await fetch(`http://localhost:8000/api/agents/${result.uploadId}:register`, { method: 'POST' });
                      } catch (e) {
                        console.error(e);
                      }
                    }}
                    disabled={uploading}
                    className="bg-green-600 hover:bg-green-700 text-white px-6 py-2.5 rounded-lg font-medium transition-colors shadow-sm"
                  >
                    {uploading ? "Processing..." : "Register to GitHub"}
                  </button>
                </div>
              )}
              
              {result.status === 'REGISTERED' && (
                <div className="mt-4">
                  <button 
                    onClick={async () => {
                      setUploading(true);
                      try {
                        await fetch(`http://localhost:8000/api/agents/${result.uploadId}/issues:plan`, { method: 'POST' });
                      } catch (e) {
                        console.error(e);
                      }
                    }}
                    disabled={uploading}
                    className="bg-purple-600 hover:bg-purple-700 text-white px-6 py-2.5 rounded-lg font-medium transition-colors shadow-sm"
                  >
                    {uploading ? "Processing..." : "Plan Issues"}
                  </button>
                </div>
              )}
              
              {['PLANNING', 'PR_OPEN', 'PREVIEW_READY', 'MERGED'].includes(result.status) && (
                <div className="mt-8 border-t pt-8">
                  <h3 className="text-2xl font-semibold mb-6">Issues & Implementation</h3>
                  <IssueList 
                    uploadId={result.uploadId} 
                    onImplemented={(prUrl, branch) => {
                      setResult({...result, status: 'PR_OPEN', prNumber: prUrl.split('/').pop(), prBranch: branch});
                    }} 
                  />
                </div>
              )}
              
              {['PR_OPEN', 'PREVIEW_READY'].includes(result.status) && (
                <div className="mt-8 border-t pt-8">
                  <PRViewer 
                    uploadId={result.uploadId} 
                    prNumber={result.prNumber} 
                    prBranch={result.prBranch} 
                    onApproved={() => setResult({...result, status: 'MERGED'})}
                  />
                </div>
              )}

              {result.status === 'MERGED' && (
                <div className="mt-8 p-6 bg-green-50 border border-green-200 text-green-800 rounded-xl flex items-center gap-4">
                  <div className="text-4xl">🎉</div>
                  <div>
                    <h3 className="text-xl font-bold mb-1">実装完了</h3>
                    <p className="text-sm">PRがマージされ、Issue対応が完了しました。</p>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </main>
      <aside className="w-[450px] bg-gray-900 border-l border-gray-800 p-4 shadow-2xl flex flex-col">
        <DebugConsole />
      </aside>
    </div>
  );
}
