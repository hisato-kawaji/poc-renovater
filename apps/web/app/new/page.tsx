"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { UploadCloud, FolderArchive, ArrowRight, Loader2 } from "lucide-react";
import { motion } from "framer-motion";

export default function NewPoC() {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const router = useRouter();

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    try {
      const formData = new FormData();
      formData.append("file", file);

      // Upload API
      const upRes = await fetch("/api/uploads", {
        method: "POST",
        body: formData,
      });
      const { uploadId } = await upRes.json();

      // Start Analyze API asynchronously
      await fetch("/api/agents:analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ uploadId }),
      });
      
      // Redirect to detail page
      router.push(`/poc/${uploadId}`);
    } catch (e) {
      console.error(e);
      alert("Error occurred during upload.");
      setUploading(false);
    }
  };

  return (
    <div className="p-8 max-w-4xl mx-auto min-h-screen flex flex-col items-center justify-center">
      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full text-center mb-10"
      >
        <h1 className="text-4xl font-bold tracking-tight text-zinc-900 mb-4">Create New PoC</h1>
        <p className="text-zinc-500 text-lg">Upload your source code as a .zip file to get started with analysis and planning.</p>
      </motion.div>

      <motion.div 
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ delay: 0.1 }}
        className="w-full max-w-2xl"
      >
        <div className="bg-white rounded-3xl shadow-xl shadow-zinc-200/50 border border-zinc-200 p-10 overflow-hidden relative">
          {/* Decorative background gradient */}
          <div className="absolute -top-24 -right-24 w-48 h-48 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none" />
          <div className="absolute -bottom-24 -left-24 w-48 h-48 bg-purple-500/10 rounded-full blur-3xl pointer-events-none" />

          <div className="relative z-10 flex flex-col items-center">
            <div className={`w-24 h-24 rounded-2xl flex items-center justify-center mb-8 transition-colors ${file ? 'bg-indigo-50 border-2 border-indigo-200 text-indigo-600' : 'bg-zinc-50 border-2 border-dashed border-zinc-300 text-zinc-400'}`}>
              {file ? <FolderArchive size={40} /> : <UploadCloud size={40} />}
            </div>

            <label className="block w-full text-center cursor-pointer group">
              <span className="sr-only">Choose zip file</span>
              <div className="relative">
                <input
                  type="file"
                  accept=".zip"
                  onChange={(e) => setFile(e.target.files?.[0] || null)}
                  className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                  disabled={uploading}
                />
                <div className={`w-full p-4 border-2 border-dashed rounded-xl transition-all ${
                  file ? 'border-indigo-300 bg-indigo-50/50' : 'border-zinc-300 bg-zinc-50 group-hover:bg-zinc-100 group-hover:border-zinc-400'
                }`}>
                  {file ? (
                    <div className="flex items-center justify-center gap-2 text-indigo-700 font-medium">
                      <FolderArchive size={18} />
                      {file.name}
                      <span className="text-indigo-400 text-sm ml-2">({(file.size / 1024 / 1024).toFixed(2)} MB)</span>
                    </div>
                  ) : (
                    <div className="text-zinc-600 font-medium">
                      Click to browse or drag and drop your .zip file here
                    </div>
                  )}
                </div>
              </div>
            </label>

            <button
              onClick={handleUpload}
              disabled={!file || uploading}
              className="mt-8 w-full flex items-center justify-center gap-2 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 text-white px-8 py-4 rounded-xl disabled:opacity-50 disabled:cursor-not-allowed font-bold text-lg shadow-lg shadow-indigo-200 transition-all active:scale-[0.98]"
            >
              {uploading ? (
                <>
                  <Loader2 className="animate-spin" size={24} />
                  Uploading & Analyzing...
                </>
              ) : (
                <>
                  Start Process
                  <ArrowRight size={20} />
                </>
              )}
            </button>
          </div>
        </div>
      </motion.div>
    </div>
  );
}
