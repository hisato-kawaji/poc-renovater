"use client";

import React from "react";

export interface ErrorModalProps {
  isOpen: boolean;
  errorMessage: string;
  onRetry: () => void;
  onCancel: () => void;
}

export function ErrorModal({ isOpen, errorMessage, onRetry, onCancel }: ErrorModalProps) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50" data-testid="error-modal">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-lg overflow-hidden">
        <div className="p-4 bg-red-50 border-b border-red-100 flex items-center">
          <svg className="w-6 h-6 text-red-500 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <h2 className="text-lg font-bold text-red-700">Pipeline Job Failed</h2>
        </div>
        <div className="p-6">
          <p className="text-sm text-gray-700 mb-2">The following error occurred during execution:</p>
          <div className="bg-gray-100 p-3 rounded-md overflow-auto max-h-48 text-xs font-mono text-gray-800 break-words" data-testid="error-message">
            {errorMessage}
          </div>
        </div>
        <div className="p-4 border-t border-gray-100 flex justify-end space-x-3 bg-gray-50">
          <button 
            onClick={onCancel}
            className="px-4 py-2 border border-gray-300 rounded text-sm font-medium text-gray-700 hover:bg-gray-100"
            data-testid="cancel-btn"
          >
            Cancel Pipeline
          </button>
          <button 
            onClick={onRetry}
            className="px-4 py-2 bg-red-600 rounded text-sm font-medium text-white hover:bg-red-700"
            data-testid="retry-btn"
          >
            Retry Job
          </button>
        </div>
      </div>
    </div>
  );
}
