"use client";
import { useState } from "react";

import CharterChat from "../components/CharterChat";
import IssueList from "../components/IssueList";
import PRViewer from "../components/PRViewer";

export default function Home() {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState<any>(null);

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

      // Analyze API
      const anRes = await fetch("http://localhost:8000/api/agents:analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ uploadId }),
      });
      
      // Poll for status
      const pollResult = async () => {
        try {
          const res = await fetch(`http://localhost:8000/api/agents/${uploadId}`);
          if (res.ok) {
            const data = await res.json();
            if (data.status) {
              setResult({ uploadId, ...data });
              if (['PASSED', 'REJECTED', 'ERROR'].includes(data.status)) {
                setUploading(false);
                return;
              }
            }
          }
        } catch (e) {
          console.error("Polling error", e);
        }
        setTimeout(pollResult, 3000);
      };
      
      pollResult();

    } catch (e) {
      console.error(e);
      alert("Error occurred");
      setUploading(false);
    }
  };

  return (
    <main className="p-8 max-w-4xl mx-auto">
      <h1 className="text-3xl font-bold mb-4">PoC Foundry - Upload</h1>
      
      <div className="mb-8 p-4 border rounded-lg bg-gray-50">
        <label className="block mb-2 font-medium text-gray-700">対象のPoC（.zipファイル）を選択してください</label>
        <p className="text-sm text-gray-500 mb-4">※フォルダをアップロードする場合は、事前に右クリック等でzip圧縮してください。</p>
        <input 
          type="file" 
          accept=".zip" 
          onChange={(e) => setFile(e.target.files?.[0] || null)} 
          className="mb-6 block w-full text-sm text-gray-500
            file:mr-4 file:py-2 file:px-4
            file:rounded-full file:border-0
            file:text-sm file:font-semibold
            file:bg-blue-50 file:text-blue-700
            hover:file:bg-blue-100
            border border-gray-300 rounded-lg p-3 bg-white cursor-pointer"
        />
        <button 
          onClick={handleUpload} 
          disabled={!file || uploading}
          className="bg-blue-600 text-white px-6 py-2 rounded disabled:opacity-50 disabled:cursor-not-allowed font-medium"
        >
          {uploading ? "Analyzing..." : "Upload & Analyze"}
        </button>
      </div>

      {result && (
        <div className="p-4 border rounded-lg shadow space-y-4">
          <h2 className="text-2xl font-semibold">Results</h2>
          
          <div className="p-4 rounded text-white font-bold text-lg bg-gray-800">
            Status: <span className={result.status === "PASSED" ? "text-green-400" : "text-red-400"}>{result.status}</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <h3 className="text-xl font-medium border-b pb-2 mb-2">Charter Evaluation</h3>
              <pre className="bg-gray-100 p-4 rounded overflow-auto text-sm max-h-96 text-gray-900">
                {JSON.stringify(result.charter, null, 2)}
              </pre>
            </div>
            <div>
              <h3 className="text-xl font-medium border-b pb-2 mb-2">Interactive Chat</h3>
              <CharterChat uploadId={result.uploadId} />
            </div>
          </div>

          <div>
            <h3 className="text-xl font-medium border-b pb-2 mb-2">Technical Analysis</h3>
            <pre className="bg-gray-100 p-4 rounded overflow-auto text-sm max-h-96 text-gray-900">
              {JSON.stringify(result.analysis, null, 2)}
            </pre>
          </div>

          {result.status === 'PASSED' && (
            <div className="mt-4">
              <button 
                onClick={async () => {
                  setUploading(true);
                  try {
                    const res = await fetch(`http://localhost:8000/api/agents/${result.uploadId}:register`, { method: 'POST' });
                    const json = await res.json();
                    alert(`Registered! Repo URL: ${json.repoUrl}`);
                    setResult({...result, status: 'REGISTERED'});
                  } catch (e) {
                    console.error(e);
                  } finally {
                    setUploading(false);
                  }
                }}
                disabled={uploading}
                className="bg-green-600 text-white px-4 py-2 rounded"
              >
                Register to GitHub
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
                    alert(`Issues planning started in background!`);
                    setResult({...result, status: 'PLANNING'});
                  } catch (e) {
                    console.error(e);
                  } finally {
                    setUploading(false);
                  }
                }}
                disabled={uploading}
                className="bg-purple-600 text-white px-4 py-2 rounded"
              >
                Plan Issues
              </button>
            </div>
          )}
          
          {['PLANNING', 'PR_OPEN', 'PREVIEW_READY', 'MERGED'].includes(result.status) && (
            <div className="mt-4 border-t pt-4">
              <h3 className="text-xl font-medium mb-4">Issues & Implementation</h3>
              <IssueList 
                uploadId={result.uploadId} 
                onImplemented={(prUrl, branch) => {
                  setResult({...result, status: 'PR_OPEN', prNumber: prUrl.split('/').pop(), prBranch: branch});
                }} 
              />
            </div>
          )}
          
          {['PR_OPEN', 'PREVIEW_READY'].includes(result.status) && (
            <PRViewer 
              uploadId={result.uploadId} 
              prNumber={result.prNumber} 
              prBranch={result.prBranch} 
              onApproved={() => setResult({...result, status: 'MERGED'})}
            />
          )}

          {result.status === 'MERGED' && (
            <div className="mt-4 p-4 bg-green-100 text-green-800 rounded-lg">
              <h3 className="text-xl font-bold mb-2">実装完了 🎉</h3>
              <p>PRがマージされ、Issue対応が完了しました。</p>
            </div>
          )}
        </div>
      )}
    </main>
  );
}
