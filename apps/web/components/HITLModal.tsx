"use client";

import React, { useState } from "react";

export interface HITLModalProps {
  isOpen: boolean;
  blockedReason: string;
  requiresEnvVars?: boolean;
  onApprove: (envVars?: Record<string, string>) => void;
  onCancel: () => void;
}

export function HITLModal({ isOpen, blockedReason, requiresEnvVars, onApprove, onCancel }: HITLModalProps) {
  const [envKey, setEnvKey] = useState("");
  const [envVal, setEnvVal] = useState("");
  const [envs, setEnvs] = useState<Record<string, string>>({});

  if (!isOpen) return null;

  const handleAddEnv = () => {
    if (envKey.trim() && envVal.trim()) {
      setEnvs({ ...envs, [envKey.trim()]: envVal.trim() });
      setEnvKey("");
      setEnvVal("");
    }
  };

  const handleApprove = () => {
    onApprove(requiresEnvVars ? envs : undefined);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50" data-testid="hitl-modal">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-lg overflow-hidden">
        <div className="p-4 bg-yellow-50 border-b border-yellow-100 flex items-center">
          <svg className="w-6 h-6 text-yellow-600 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
          <h2 className="text-lg font-bold text-yellow-800">Human Intervention Required</h2>
        </div>
        <div className="p-6">
          <p className="text-sm text-gray-700 mb-4" data-testid="blocked-reason">{blockedReason}</p>
          
          {requiresEnvVars && (
            <div className="mb-4">
              <h3 className="text-sm font-semibold mb-2">Environment Variables</h3>
              <div className="flex space-x-2 mb-2">
                <input 
                  type="text" 
                  placeholder="KEY (e.g. API_KEY)" 
                  value={envKey}
                  onChange={(e) => setEnvKey(e.target.value)}
                  className="flex-1 border border-gray-300 p-2 rounded text-sm"
                  data-testid="env-key-input"
                />
                <input 
                  type="text" 
                  placeholder="VALUE" 
                  value={envVal}
                  onChange={(e) => setEnvVal(e.target.value)}
                  className="flex-1 border border-gray-300 p-2 rounded text-sm"
                  data-testid="env-val-input"
                />
                <button onClick={handleAddEnv} className="px-3 py-2 bg-blue-600 text-white rounded text-sm hover:bg-blue-700" data-testid="env-add-btn">Add</button>
              </div>
              {Object.keys(envs).length > 0 && (
                <ul className="mt-2 text-xs border border-gray-200 rounded bg-gray-50 p-2" data-testid="env-list">
                  {Object.entries(envs).map(([k, v]) => (
                    <li key={k} className="flex justify-between py-1 border-b border-gray-200 last:border-0">
                      <span className="font-mono text-gray-800">{k}</span>
                      <span className="font-mono text-gray-500">{"*".repeat(v.length)}</span>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          )}
        </div>
        <div className="p-4 border-t border-gray-100 flex justify-end space-x-3 bg-gray-50">
          <button 
            onClick={onCancel}
            className="px-4 py-2 border border-gray-300 rounded text-sm font-medium text-gray-700 hover:bg-gray-100"
            data-testid="hitl-cancel-btn"
          >
            Reject / Cancel
          </button>
          <button 
            onClick={handleApprove}
            className="px-4 py-2 bg-yellow-600 rounded text-sm font-medium text-white hover:bg-yellow-700"
            data-testid="hitl-approve-btn"
          >
            Approve & Continue
          </button>
        </div>
      </div>
    </div>
  );
}
