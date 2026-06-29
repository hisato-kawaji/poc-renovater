"use client";
import { useState, useEffect, useRef } from "react";

interface LogEntry {
  timestamp: string;
  level: string;
  message: string;
  logger: string;
}

export default function DebugConsole() {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const fetchLogs = async () => {
      try {
        const res = await fetch("http://localhost:8000/api/logs");
        if (res.ok) {
          const data = await res.json();
          setLogs(data.logs);
        }
      } catch (e) {
        // Ignore fetch errors so it doesn't spam console
      }
    };

    fetchLogs();
    const interval = setInterval(fetchLogs, 2000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, [logs]);

  return (
    <div className="flex flex-col h-full">
      <h3 className="text-white font-bold mb-4 border-b border-gray-700 pb-2 flex items-center justify-between">
        <span>System Logs</span>
        <span className="text-xs bg-gray-800 px-2 py-1 rounded text-gray-400">Auto-refresh</span>
      </h3>
      <div ref={containerRef} className="flex-1 overflow-auto font-mono text-[11px] leading-relaxed space-y-1">
        {logs.length === 0 ? (
          <div className="text-gray-500 italic">No logs available...</div>
        ) : (
          logs.map((log, i) => {
            const isError = log.level === "ERROR" || log.level === "WARNING";
            const isInfo = log.level === "INFO";
            const colorClass = isError ? "text-red-400" : isInfo ? "text-blue-300" : "text-gray-300";
            const timeStr = new Date(log.timestamp).toLocaleTimeString('en-US', { hour12: false, fractionalSecondDigits: 3 });
            return (
              <div key={i} className="break-words">
                <span className="text-gray-500 mr-2">[{timeStr}]</span>
                <span className={`${colorClass} font-semibold mr-2`}>{log.level}</span>
                <span className="text-gray-300">{log.message}</span>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
