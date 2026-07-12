"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { LayoutDashboard, PlusCircle, Settings, ChevronLeft, ChevronRight, Cpu } from "lucide-react";
import { motion } from "framer-motion";

export function Sidebar() {
  const [collapsed, setCollapsed] = useState(false);
  const pathname = usePathname();

  const navItems = [
    { name: "Dashboard", href: "/", icon: LayoutDashboard },
    { name: "New PoC", href: "/new", icon: PlusCircle },
  ];

  return (
    <motion.aside
      initial={{ width: 280 }}
      animate={{ width: collapsed ? 80 : 280 }}
      transition={{ type: "spring", stiffness: 300, damping: 30 }}
      className="bg-zinc-950 text-zinc-100 flex flex-col h-screen border-r border-zinc-800 shadow-2xl relative z-10"
    >
      <div className="p-4 flex items-center justify-between border-b border-zinc-800">
        {!collapsed && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="flex items-center gap-3"
          >
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center shadow-lg shadow-indigo-500/30">
              <Cpu size={18} className="text-white" />
            </div>
            <span className="font-bold text-lg tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-indigo-400 to-purple-400">
              PoC Renovater
            </span>
          </motion.div>
        )}
        {collapsed && (
          <div className="w-full flex justify-center">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center shadow-lg shadow-indigo-500/30">
              <Cpu size={18} className="text-white" />
            </div>
          </div>
        )}
      </div>

      <button
        onClick={() => setCollapsed(!collapsed)}
        className="absolute -right-4 top-6 bg-zinc-800 border border-zinc-700 text-zinc-400 hover:text-white rounded-full p-1.5 shadow-lg z-20 hover:bg-zinc-700 transition-colors"
      >
        {collapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
      </button>

      <nav className="flex-1 py-6 flex flex-col gap-2 px-3">
        {navItems.map((item) => {
          const isActive = pathname === item.href;
          const Icon = item.icon;
          return (
            <Link
              key={item.name}
              href={item.href}
              className={`flex items-center gap-3 px-3 py-3 rounded-xl transition-all duration-200 group relative ${
                isActive
                  ? "bg-zinc-800 text-white shadow-md shadow-black/20"
                  : "text-zinc-400 hover:bg-zinc-900 hover:text-zinc-200"
              }`}
            >
              <Icon
                size={20}
                className={isActive ? "text-indigo-400" : "group-hover:text-zinc-300 transition-colors"}
              />
              {!collapsed && (
                <span className="font-medium text-sm tracking-wide">{item.name}</span>
              )}
              {isActive && !collapsed && (
                <motion.div
                  layoutId="sidebar-active"
                  className="absolute inset-0 rounded-xl border border-indigo-500/30 bg-indigo-500/10 pointer-events-none"
                  initial={false}
                  transition={{ type: "spring", stiffness: 300, damping: 30 }}
                />
              )}
            </Link>
          );
        })}
      </nav>

      <div className="p-4 border-t border-zinc-800">
        <div className={`flex items-center gap-3 px-3 py-3 rounded-xl text-zinc-500 cursor-not-allowed ${collapsed ? 'justify-center' : ''}`}>
          <Settings size={20} />
          {!collapsed && <span className="font-medium text-sm">Settings</span>}
        </div>
      </div>
    </motion.aside>
  );
}
