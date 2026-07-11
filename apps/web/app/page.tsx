"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { PlusCircle, Search, Activity, Code2, Server, CheckCircle2, AlertCircle, Clock, ExternalLink } from "lucide-react";

type Agent = {
  id: string;
  status: string;
  repo?: { fullName: string; url: string };
  createdAt?: string;
  updatedAt?: string;
};

const statusColors: Record<string, string> = {
  ANALYZING: "bg-blue-500/10 text-blue-500 border-blue-500/20",
  PASSED: "bg-emerald-500/10 text-emerald-500 border-emerald-500/20",
  REJECTED: "bg-red-500/10 text-red-500 border-red-500/20",
  REGISTERED: "bg-purple-500/10 text-purple-500 border-purple-500/20",
  PLANNING: "bg-indigo-500/10 text-indigo-500 border-indigo-500/20",
  PR_OPEN: "bg-amber-500/10 text-amber-500 border-amber-500/20",
  PREVIEW_READY: "bg-cyan-500/10 text-cyan-500 border-cyan-500/20",
  CHANGES_REQUESTED: "bg-rose-500/10 text-rose-500 border-rose-500/20",
  MERGED: "bg-emerald-500/10 text-emerald-500 border-emerald-500/20",
  ERROR: "bg-red-500/10 text-red-500 border-red-500/20",
  IDLE: "bg-zinc-500/10 text-zinc-500 border-zinc-500/20",
};

const statusIcons: Record<string, React.ReactNode> = {
  ANALYZING: <Activity size={14} />,
  PASSED: <CheckCircle2 size={14} />,
  REJECTED: <AlertCircle size={14} />,
  REGISTERED: <Code2 size={14} />,
  PLANNING: <Clock size={14} />,
  PR_OPEN: <Code2 size={14} />,
  PREVIEW_READY: <Server size={14} />,
  MERGED: <CheckCircle2 size={14} />,
  ERROR: <AlertCircle size={14} />,
  IDLE: <Clock size={14} />,
};

export default function Dashboard() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchAgents() {
      try {
        const res = await fetch("/api/agents");
        if (res.ok) {
          const data = await res.json();
          setAgents(data);
        }
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    }
    fetchAgents();
  }, []);

  return (
    <div className="p-8 max-w-7xl mx-auto min-h-screen">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-zinc-900">Dashboard</h1>
          <p className="text-zinc-500 mt-1">Manage your active Proof of Concepts</p>
        </div>
        <Link
          href="/new"
          className="flex items-center gap-2 bg-zinc-900 hover:bg-zinc-800 text-white px-5 py-2.5 rounded-xl transition-all shadow-lg shadow-zinc-200 font-medium"
        >
          <PlusCircle size={18} />
          New PoC
        </Link>
      </div>

      <div className="bg-white rounded-2xl shadow-sm border border-zinc-200 overflow-hidden">
        <div className="p-4 border-b border-zinc-200 flex items-center gap-4 bg-zinc-50/50">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-zinc-400" size={18} />
            <input
              type="text"
              placeholder="Search PoCs..."
              className="w-full pl-10 pr-4 py-2 bg-white border border-zinc-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all"
            />
          </div>
        </div>

        {loading ? (
          <div className="p-12 text-center text-zinc-400 flex flex-col items-center">
            <div className="animate-spin rounded-full h-8 w-8 border-2 border-zinc-300 border-t-indigo-600 mb-4"></div>
            Loading PoCs...
          </div>
        ) : agents.length === 0 ? (
          <div className="p-16 text-center">
            <div className="w-16 h-16 bg-zinc-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <PlusCircle size={24} className="text-zinc-400" />
            </div>
            <h3 className="text-lg font-medium text-zinc-900 mb-1">No PoCs found</h3>
            <p className="text-zinc-500 mb-6">Get started by creating your first Proof of Concept.</p>
            <Link
              href="/new"
              className="inline-flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white px-5 py-2.5 rounded-xl transition-colors font-medium shadow-sm shadow-indigo-200"
            >
              <PlusCircle size={18} />
              Create PoC
            </Link>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-zinc-600">
              <thead className="text-xs uppercase bg-zinc-50 text-zinc-500 border-b border-zinc-200">
                <tr>
                  <th className="px-6 py-4 font-medium">PoC ID</th>
                  <th className="px-6 py-4 font-medium">Status</th>
                  <th className="px-6 py-4 font-medium">Repository</th>
                  <th className="px-6 py-4 font-medium">Created At</th>
                  <th className="px-6 py-4 font-medium text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-100">
                {agents.map((agent) => (
                  <tr key={agent.id} className="hover:bg-zinc-50/50 transition-colors group">
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-lg bg-zinc-100 flex items-center justify-center font-mono text-xs font-medium text-zinc-600 border border-zinc-200">
                          {agent.id.substring(0, 2).toUpperCase()}
                        </div>
                        <span className="font-mono text-zinc-900 font-medium">{agent.id}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold border ${statusColors[agent.status] || "bg-zinc-100 text-zinc-600 border-zinc-200"}`}>
                        {statusIcons[agent.status]}
                        {agent.status}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      {agent.repo ? (
                        <div className="flex items-center gap-2">
                          <span className="text-zinc-700 font-medium">{agent.repo.fullName}</span>
                          <a
                            href={agent.repo.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-zinc-400 hover:text-indigo-600 transition-colors"
                          >
                            <ExternalLink size={14} />
                          </a>
                        </div>
                      ) : (
                        <span className="text-zinc-400 italic">Not registered yet</span>
                      )}
                    </td>
                    <td className="px-6 py-4 text-zinc-500 text-sm">
                      {agent.createdAt ? new Date(agent.createdAt).toLocaleString() : <span className="text-zinc-400 italic">Unknown</span>}
                    </td>
                    <td className="px-6 py-4 text-right">
                      <Link
                        href={`/poc/${agent.id}`}
                        className="inline-flex items-center justify-center px-4 py-1.5 text-sm font-medium bg-white border border-zinc-200 text-zinc-700 rounded-lg hover:bg-zinc-50 hover:text-indigo-600 hover:border-indigo-200 transition-all shadow-sm group-hover:shadow"
                      >
                        Open Detail
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
