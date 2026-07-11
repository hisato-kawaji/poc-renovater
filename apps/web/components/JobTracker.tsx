"use client";

import React from "react";

export type StepStatus = "PENDING" | "IN_PROGRESS" | "COMPLETED" | "FAILED" | "BLOCKED";

export interface JobStep {
  id: string;
  label: string;
}

export const JOB_STEPS: JobStep[] = [
  { id: "UPLOADED", label: "Upload & Extract" },
  { id: "CODE_EMBEDDING_INGESTION", label: "Vector DB Ingestion" },
  { id: "ARCHITECTURE_ANALYSIS", label: "Architecture Analysis" },
  { id: "CHARTER_EVALUATION", label: "Charter Evaluation" },
  { id: "GITHUB_REPO_CREATED", label: "GitHub Repository Creation" },
  { id: "ISSUES_PLANNED", label: "Issue Planning" },
  { id: "SANDBOX_PROVISIONED", label: "Sandbox Provisioning" },
  { id: "IMPLEMENTATION_START", label: "Agent Initialized" },
  { id: "DIFF_GENERATED", label: "Diff Generation" },
  { id: "TEST_EXECUTION", label: "Test Execution" },
  { id: "PR_CREATED", label: "Pull Request Creation" },
  { id: "CI_CD_BUILD", label: "CI/CD Build Pipeline" },
  { id: "PREVIEW_DEPLOYED", label: "Preview Deployment" },
  { id: "HEALTH_CHECK_VERIFICATION", label: "Health Check" },
  { id: "MERGED", label: "Merged & Finalized" },
];

export interface JobTrackerProps {
  currentStepId: string;
  status: StepStatus;
}

export function JobTracker({ currentStepId, status }: JobTrackerProps) {
  const currentIndex = JOB_STEPS.findIndex((s) => s.id === currentStepId);

  return (
    <div className="w-full bg-white p-8 rounded-2xl shadow-sm border border-zinc-200 overflow-hidden relative" data-testid="job-tracker">
      <div className="absolute top-0 right-0 p-32 bg-indigo-50/50 blur-3xl rounded-full pointer-events-none -z-10" />
      <h3 className="text-xl font-bold tracking-tight text-zinc-900 mb-8 flex items-center gap-3">
        <div className="w-8 h-8 rounded-lg bg-indigo-100 flex items-center justify-center text-indigo-600">
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>
        </div>
        Pipeline Execution Tracker
      </h3>
      
      <div className="relative pl-6 space-y-6">
        <div className="absolute left-[22px] top-4 bottom-4 w-px bg-gradient-to-b from-indigo-500/20 via-zinc-200 to-zinc-100"></div>
        {JOB_STEPS.map((step, idx) => {
          const isCompleted = idx < currentIndex || (idx === currentIndex && status === "COMPLETED");
          const isCurrent = idx === currentIndex;
          const isFailed = isCurrent && status === "FAILED";
          const isBlocked = isCurrent && status === "BLOCKED";

          let dotStyle = "bg-white border-zinc-200";
          let textStyle = "text-zinc-400";
          
          if (isCompleted) {
            dotStyle = "bg-emerald-500 border-emerald-500 shadow-sm shadow-emerald-500/30";
            textStyle = "text-zinc-800 font-medium";
          } else if (isCurrent && status === "IN_PROGRESS") {
            dotStyle = "bg-white border-indigo-500 shadow-sm shadow-indigo-500/30";
            textStyle = "text-indigo-700 font-bold";
          } else if (isFailed) {
            dotStyle = "bg-red-500 border-red-500 shadow-sm shadow-red-500/30";
            textStyle = "text-red-700 font-bold";
          } else if (isBlocked) {
            dotStyle = "bg-amber-500 border-amber-500 shadow-sm shadow-amber-500/30";
            textStyle = "text-amber-700 font-bold";
          }

          return (
            <div key={step.id} className="relative flex items-center group" data-testid={`step-${step.id}`}>
              <div className={`absolute -left-6 w-5 h-5 rounded-full border-[3px] flex items-center justify-center z-10 transition-all duration-300 ${dotStyle}`}>
                {isCompleted && (
                  <svg className="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                  </svg>
                )}
                {isCurrent && status === "IN_PROGRESS" && (
                  <div className="w-2 h-2 rounded-full bg-indigo-500 animate-pulse" />
                )}
              </div>
              <div className={`ml-4 text-sm transition-colors duration-300 ${textStyle} flex items-center gap-3`}>
                {step.label}
                {isCurrent && status === "IN_PROGRESS" && (
                  <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-indigo-50 text-indigo-600 border border-indigo-200">
                    <div className="w-1.5 h-1.5 rounded-full bg-indigo-500 animate-bounce" />
                    In Progress
                  </span>
                )}
                {isFailed && (
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-red-50 text-red-600 border border-red-200">
                    Failed
                  </span>
                )}
                {isBlocked && (
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-amber-50 text-amber-700 border border-amber-200">
                    Action Required
                  </span>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
