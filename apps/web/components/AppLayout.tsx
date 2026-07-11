"use client";

import { useState } from "react";
import { Sidebar } from "./Sidebar";
import DebugConsole from "./DebugConsole";
import { TerminalSquare, X } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

export function AppLayout({ children }: { children: React.ReactNode }) {
  const [debugOpen, setDebugOpen] = useState(false);

  return (
    <div className="flex h-screen overflow-hidden bg-zinc-50 text-zinc-900">
      <Sidebar />
      
      <main className="flex-1 overflow-auto bg-zinc-50 relative shadow-inner">
        {children}

        {/* Toggle Debug Console Button */}
        <button
          onClick={() => setDebugOpen(true)}
          className={`absolute bottom-6 right-6 p-4 rounded-full shadow-2xl transition-all duration-300 z-40 ${
            debugOpen ? "scale-0 opacity-0" : "scale-100 opacity-100 bg-zinc-900 hover:bg-zinc-800 text-white"
          }`}
        >
          <TerminalSquare size={24} />
        </button>
      </main>

      <AnimatePresence>
        {debugOpen && (
          <motion.aside
            initial={{ width: 0, opacity: 0 }}
            animate={{ width: 450, opacity: 1 }}
            exit={{ width: 0, opacity: 0 }}
            transition={{ type: "spring", stiffness: 300, damping: 30 }}
            className="bg-zinc-950 border-l border-zinc-800 shadow-2xl flex flex-col relative z-50 overflow-hidden"
          >
            <div className="p-3 border-b border-zinc-800 flex justify-between items-center bg-zinc-900/50">
              <span className="text-zinc-300 font-mono text-sm flex items-center gap-2">
                <TerminalSquare size={16} /> Debug Console
              </span>
              <button 
                onClick={() => setDebugOpen(false)}
                className="text-zinc-400 hover:text-white p-1 rounded-md hover:bg-zinc-800 transition-colors"
              >
                <X size={18} />
              </button>
            </div>
            <div className="flex-1 p-4 overflow-hidden flex flex-col min-w-[450px]">
              <DebugConsole />
            </div>
          </motion.aside>
        )}
      </AnimatePresence>
    </div>
  );
}
