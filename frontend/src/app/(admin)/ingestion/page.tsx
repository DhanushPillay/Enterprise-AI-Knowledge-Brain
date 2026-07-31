"use client";

import { useState, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { UploadCloud, File as FileIcon, Loader2, CheckCircle2, AlertCircle } from "lucide-react";
import { ingestDocument, type IngestResponse } from "@/services/api";

export default function IngestionPage() {
  const [isDragging, setIsDragging] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [result, setResult] = useState<IngestResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFileSelect(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      handleFileSelect(e.target.files[0]);
    }
  };

  const handleFileSelect = (selectedFile: File) => {
    const validTypes = [".pdf", ".md", ".txt"];
    const ext = selectedFile.name.substring(selectedFile.name.lastIndexOf('.')).toLowerCase();
    
    if (!validTypes.includes(ext)) {
      setError(`Unsupported file type: ${ext}. Supported: PDF, MD, TXT`);
      return;
    }
    
    setFile(selectedFile);
    setError(null);
    setResult(null);
  };

  const handleUpload = async () => {
    if (!file) return;

    setIsUploading(true);
    setError(null);
    setResult(null);

    try {
      const res = await ingestDocument(file);
      setResult(res);
      setFile(null); // Clear selected file after success
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="flex-1 w-full h-full p-12 md:p-24 flex flex-col items-center">
      <div className="w-full max-w-4xl text-left self-start mb-16">
        <h2 className="font-mono text-accent-dopamine text-[11px] tracking-[0.3em] uppercase mb-6">
          Data Operations // Pipeline
        </h2>
        
        <h1 className="font-heading text-foreground text-5xl md:text-6xl tracking-tight mb-4">
          Ingestion Engine.
        </h1>
        <p className="font-sans text-foreground/50 text-lg">
          Upload organizational documents to build the semantic knowledge graph.
        </p>
      </div>

      <div className="w-full max-w-2xl flex flex-col items-center">
        <input 
          type="file" 
          ref={fileInputRef} 
          className="hidden" 
          onChange={handleFileChange}
          accept=".pdf,.txt,.md"
        />

        <AnimatePresence mode="wait">
          {!file && !isUploading && !result && (
            <motion.div
              key="dropzone"
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              onClick={() => fileInputRef.current?.click()}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              className={`relative w-full border-2 border-dashed ${isDragging ? 'border-accent-dopamine bg-accent-dopamine/5' : 'border-foreground/20'} p-16 flex flex-col items-center justify-center cursor-pointer hover:border-accent-dopamine/50 hover:bg-white/5 transition-colors group rounded-3xl overflow-hidden`}
            >
              <div className="absolute inset-0 bg-gradient-to-b from-accent-dopamine/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
              <motion.div 
                animate={{ y: [0, -8, 0] }}
                transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
                className="mb-8"
              >
                <UploadCloud className={`w-16 h-16 ${isDragging ? 'text-accent-dopamine' : 'text-foreground/30 group-hover:text-accent-dopamine'} transition-colors drop-shadow-xl`} />
              </motion.div>
              
              <div className="relative z-10 font-mono text-[9px] uppercase tracking-widest text-foreground/40 mb-6 group-hover:text-accent-dopamine transition-colors">
                Supported Formats: PDF, MD, TXT
              </div>
              <div className="relative z-10 font-sans text-2xl font-medium text-foreground text-center">
                Click or drop data here<br/>
                <span className="text-foreground/50 text-lg">to begin graph extraction.</span>
              </div>
            </motion.div>
          )}

          {file && !isUploading && (
            <motion.div
              key="file-selected"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="w-full flex flex-col items-center"
            >
              <div className="bg-white border border-black/10 rounded-2xl p-6 w-full flex items-center justify-between mb-8 shadow-sm">
                <div className="flex items-center gap-4">
                  <div className="bg-black/5 p-3 rounded-xl">
                    <FileIcon className="w-8 h-8 text-black" />
                  </div>
                  <div>
                    <h3 className="font-sans font-medium text-lg text-black">{file.name}</h3>
                    <p className="font-mono text-xs text-[#666]">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
                  </div>
                </div>
                <button 
                  onClick={() => setFile(null)}
                  className="font-mono text-xs uppercase tracking-widest text-red-500 hover:bg-red-50 px-4 py-2 rounded-lg transition-colors"
                >
                  Cancel
                </button>
              </div>

              <button
                onClick={handleUpload}
                className="bg-black hover:bg-black/80 text-white font-sans font-medium text-lg px-12 py-4 rounded-full transition-colors flex items-center gap-3 w-full justify-center"
              >
                <UploadCloud className="w-5 h-5" />
                Start Processing Pipeline
              </button>
            </motion.div>
          )}

          {isUploading && (
            <motion.div
              key="uploading"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="flex flex-col items-center justify-center py-20"
            >
              <Loader2 className="w-16 h-16 text-black animate-spin mb-8" />
              <h3 className="font-heading text-3xl mb-4 text-black">Processing Data</h3>
              <div className="font-mono text-sm text-[#666] flex flex-col items-center gap-2">
                <span className="flex items-center gap-2"><Loader2 className="w-3 h-3 animate-spin"/> Chunking text...</span>
                <span className="flex items-center gap-2"><Loader2 className="w-3 h-3 animate-spin"/> Extracting entities via LLM...</span>
                <span className="flex items-center gap-2"><Loader2 className="w-3 h-3 animate-spin"/> Writing to Neo4j...</span>
              </div>
            </motion.div>
          )}

          {result && (
            <motion.div
              key="result"
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              className="w-full bg-white border border-black/10 rounded-3xl p-8 shadow-sm flex flex-col items-center"
            >
              <div className="w-16 h-16 bg-emerald-100 rounded-full flex items-center justify-center mb-6">
                <CheckCircle2 className="w-8 h-8 text-emerald-600" />
              </div>
              <h3 className="font-heading text-3xl text-black mb-2">Ingestion Complete</h3>
              <p className="font-sans text-[#666] mb-8">{result.filename}</p>

              <div className="grid grid-cols-2 md:grid-cols-3 gap-4 w-full mb-8">
                <div className="bg-black/5 rounded-2xl p-4 text-center">
                  <div className="font-heading text-3xl text-black mb-1">{result.chunks_created}</div>
                  <div className="font-mono text-[9px] uppercase tracking-widest text-[#666]">Chunks</div>
                </div>
                <div className="bg-black/5 rounded-2xl p-4 text-center">
                  <div className="font-heading text-3xl text-black mb-1">{result.entities_extracted}</div>
                  <div className="font-mono text-[9px] uppercase tracking-widest text-[#666]">Entities</div>
                </div>
                <div className="bg-black/5 rounded-2xl p-4 text-center">
                  <div className="font-heading text-3xl text-black mb-1">{result.relationships_extracted}</div>
                  <div className="font-mono text-[9px] uppercase tracking-widest text-[#666]">Relations</div>
                </div>
              </div>

              <button
                onClick={() => setResult(null)}
                className="bg-black/5 hover:bg-black/10 text-black font-sans font-medium px-8 py-3 rounded-full transition-colors"
              >
                Process Another File
              </button>
            </motion.div>
          )}
        </AnimatePresence>

        {error && (
          <motion.div 
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="mt-8 p-4 bg-red-50 border border-red-200 text-red-600 rounded-xl flex items-start gap-3 w-full"
          >
            <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
            <div className="font-sans text-sm">{error}</div>
          </motion.div>
        )}
      </div>
    </div>
  );
}
