"use client";
import React from "react";

export default function PipelineProgress({ status }: { status: string }) {
  const steps = [
    { id: "UPLOAD", label: "Upload & Extract", activeFor: ["ANALYZING"] },
    { id: "CHARTER", label: "Charter Eval", activeFor: ["PASSED", "REJECTED"] },
    { id: "REGISTER", label: "GitHub Register", activeFor: ["REGISTERED"] },
    { id: "PLAN", label: "Plan Issues", activeFor: ["PLANNING"] },
    { id: "IMPLEMENT", label: "Implement Code", activeFor: ["PR_OPEN"] },
    { id: "PREVIEW", label: "Deploy Preview", activeFor: ["PREVIEW_READY"] },
    { id: "MERGE", label: "Merged", activeFor: ["MERGED"] },
  ];

  let currentStepIndex = -1;
  // Determine current step index based on status logic
  if (!status) currentStepIndex = -1;
  else if (status === "ANALYZING") currentStepIndex = 0;
  else if (status === "PASSED" || status === "REJECTED") currentStepIndex = 1;
  else if (status === "REGISTERED") currentStepIndex = 2;
  else if (status === "PLANNING") currentStepIndex = 3;
  else if (status === "PR_OPEN") currentStepIndex = 4;
  else if (status === "PREVIEW_READY") currentStepIndex = 5;
  else if (status === "MERGED") currentStepIndex = 6;
  else if (status === "ERROR") currentStepIndex = 0; // or wherever it failed

  return (
    <div className="mb-8 w-full">
      <div className="flex items-center justify-between w-full relative">
        {/* Background line */}
        <div className="absolute left-0 top-1/2 transform -translate-y-1/2 w-full h-1 bg-gray-200 z-0"></div>
        {/* Progress line */}
        {currentStepIndex >= 0 && (
          <div 
            className="absolute left-0 top-1/2 transform -translate-y-1/2 h-1 bg-blue-500 z-0 transition-all duration-500"
            style={{ width: `${(currentStepIndex / (steps.length - 1)) * 100}%` }}
          ></div>
        )}

        {steps.map((step, index) => {
          const isCompleted = index < currentStepIndex;
          const isCurrent = index === currentStepIndex;
          const isFailed = isCurrent && (status === "REJECTED" || status === "ERROR");

          let circleColor = "bg-gray-200 border-gray-300 text-gray-500";
          if (isCompleted) circleColor = "bg-blue-500 border-blue-500 text-white";
          if (isCurrent && !isFailed) circleColor = "bg-blue-100 border-blue-500 text-blue-600 ring-4 ring-blue-50";
          if (isFailed) circleColor = "bg-red-100 border-red-500 text-red-600 ring-4 ring-red-50";

          return (
            <div key={step.id} className="relative z-10 flex flex-col items-center group">
              <div className={`w-8 h-8 rounded-full border-2 flex items-center justify-center font-semibold text-xs shadow-sm transition-colors ${circleColor}`}>
                {isCompleted ? "✓" : index + 1}
              </div>
              <div className={`absolute top-10 text-[10px] font-medium whitespace-nowrap px-2 py-1 rounded ${isCurrent ? 'bg-gray-800 text-white' : 'text-gray-500'}`}>
                {step.label}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
