"use client";

import { useState, useEffect } from "react";
import Link from "next/link";

type Agent = {
  id: string;
  status: string;
  prNumber?: string;
  repo?: {
    url: string;
    fullName: string;
  };
  charter?: {
    score: number;
    decision: string;
  };
  createdAt?: string;
};

export default function Dashboard() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchAgents = async () => {
    try {
      const res = await fetch("/api/agents", {
        headers: { "X-Tenant-ID": "test-tenant" } // Mock tenant ID for now
      });
      if (res.ok) {
        const data = await res.json();
        setAgents(data);
      }
    } catch (e) {
      console.error("Failed to fetch agents", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAgents();
    const interval = setInterval(fetchAgents, 5000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return <div className="p-8">Loading dashboard...</div>;
  }

  return (
    <div className="p-8 bg-gray-50 min-h-screen">
      <div className="max-w-6xl mx-auto">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Multi-PoC Dashboard</h1>
          <Link href="/" className="px-4 py-2 bg-blue-600 text-white rounded-lg shadow hover:bg-blue-700 transition">
            + New PoC
          </Link>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {agents.length === 0 ? (
            <div className="col-span-full p-8 text-center bg-white rounded-xl shadow-sm border border-gray-100 text-gray-500">
              No PoCs found in this tenant.
            </div>
          ) : (
            agents.map((agent) => (
              <div key={agent.id} className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden flex flex-col hover:shadow-md transition">
                <div className="p-5 flex-1">
                  <div className="flex justify-between items-start mb-4">
                    <h3 className="font-semibold text-lg text-gray-800 break-all">{agent.id.substring(0, 13)}...</h3>
                    <span className={`px-3 py-1 rounded-full text-xs font-bold ${
                      agent.status === "PASSED" || agent.status === "MERGED" ? "bg-green-100 text-green-700" :
                      agent.status === "REJECTED" || agent.status === "ERROR" ? "bg-red-100 text-red-700" :
                      "bg-blue-100 text-blue-700"
                    }`}>
                      {agent.status}
                    </span>
                  </div>
                  
                  {agent.createdAt && (
                    <div className="mb-3 text-sm">
                      <span className="text-gray-500 mr-2">Created:</span>
                      <span className="font-medium text-gray-900">{new Date(agent.createdAt).toLocaleString()}</span>
                    </div>
                  )}

                  {agent.charter && (
                    <div className="mb-3 text-sm">
                      <span className="text-gray-500 mr-2">Charter Score:</span>
                      <span className="font-medium text-gray-900">{agent.charter.score}/100</span>
                    </div>
                  )}

                  {agent.repo && (
                    <div className="mb-3 text-sm">
                      <span className="text-gray-500 block mb-1">Repository:</span>
                      <a href={agent.repo.url} target="_blank" rel="noreferrer" className="text-blue-600 hover:underline break-all">
                        {agent.repo.fullName}
                      </a>
                    </div>
                  )}
                  
                  {agent.prNumber && (
                    <div className="mb-3 text-sm">
                      <span className="text-gray-500 mr-2">Active PR:</span>
                      <span className="font-medium text-gray-900">#{agent.prNumber}</span>
                    </div>
                  )}
                </div>
                <div className="bg-gray-50 px-5 py-3 border-t border-gray-100">
                  <button className="text-sm font-medium text-blue-600 hover:text-blue-800 w-full text-center">
                    View Details
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
