import React, { useState, useRef, useMemo } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  UploadCloud,
  FileText,
  Search,
  RefreshCw,
  Trash2,
  MessageSquare,
  AlertCircle,
  CheckCircle2,
  FolderOpen,
  PieChart,
  X,
  ChevronLeft,
  ChevronRight,
  Plus,
} from "lucide-react";
import { documentsApi } from "../api/documents";
import { DocumentStatus } from "../api/types";
import { StatusBadge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from "../components/ui/Table";
import { useToast } from "../components/ui/Toast";
import { NewChatModal } from "../components/chat/NewChatModal";
import { SkeletonTable } from "../components/ui/Skeleton";
import { ApiError } from "../api/client";

export const DocumentsPage: React.FC = () => {
  const queryClient = useQueryClient();
  const toast = useToast();

  const [page, setPage] = useState(1);
  const [size] = useState(10);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [isNewChatOpen, setIsNewChatOpen] = useState(false);
  const [chatTargetDocIds, setChatTargetDocIds] = useState<number[]>([]);

  // File Upload State
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [uploadProgress, setUploadProgress] = useState<number | null>(null);
  const [uploadingFileName, setUploadingFileName] = useState<string | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);

  // Fetch documents query
  const { data, isLoading, isFetching, refetch } = useQuery({
    queryKey: ["documents", page, size, statusFilter],
    queryFn: async () => {
      const statusParam =
        statusFilter === "all" ? undefined : (statusFilter as DocumentStatus);
      return await documentsApi.list({
        page,
        size,
        status: statusParam,
      });
    },
    // Auto-poll if any document is currently in UPLOADED or PROCESSING state
    refetchInterval: (query) => {
      const docs = query.state.data?.items || [];
      const hasPending = docs.some(
        (d) => d.status === "UPLOADED" || d.status === "PROCESSING"
      );
      return hasPending ? 3000 : false;
    },
  });

  const documents = data?.items || [];
  const metadata = data?.metadata;

  // Filtered documents by search term
  const filteredDocs = useMemo(() => {
    if (!search.trim()) return documents;
    return documents.filter(
      (d) =>
        d.title.toLowerCase().includes(search.toLowerCase()) ||
        d.originalFilename.toLowerCase().includes(search.toLowerCase())
    );
  }, [documents, search]);

  // Upload mutation
  const uploadMutation = useMutation({
    mutationFn: async (file: File) => {
      setUploadingFileName(file.name);
      setUploadProgress(0);
      setUploadError(null);

      return await documentsApi.upload(file, (progress) => {
        setUploadProgress(progress);
      });
    },
    onSuccess: (uploadedDoc) => {
      toast.success(`"${uploadedDoc.originalFilename}" uploaded successfully. Indexing started.`);
      setUploadProgress(null);
      setUploadingFileName(null);
      queryClient.invalidateQueries({ queryKey: ["documents"] });
    },
    onError: (err: unknown) => {
      const msg = err instanceof ApiError ? err.message : "Failed to upload document.";
      setUploadError(msg);
      toast.error(msg, "Upload Failed");
      setUploadProgress(null);
      setUploadingFileName(null);
    },
  });

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: async (id: number) => {
      return await documentsApi.delete(id);
    },
    onSuccess: () => {
      toast.info("Document deleted.");
      queryClient.invalidateQueries({ queryKey: ["documents"] });
    },
    onError: (err: unknown) => {
      const msg = err instanceof ApiError ? err.message : "Failed to delete document.";
      toast.error(msg);
    },
  });

  const handleFileSelect = (file: File) => {
    if (!file.name.toLowerCase().endsWith(".pdf")) {
      setUploadError("Only PDF files are supported.");
      return;
    }
    if (file.size > 20 * 1024 * 1024) {
      setUploadError("File size exceeds 20 MB limit.");
      return;
    }
    uploadMutation.mutate(file);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFileSelect(e.dataTransfer.files[0]);
    }
  };

  const handleStartChatWithDoc = (docId: number) => {
    setChatTargetDocIds([docId]);
    setIsNewChatOpen(true);
  };

  const totalBytes = documents.reduce((acc, d) => acc + (d.fileSize || 0), 0);
  const totalMB = (totalBytes / (1024 * 1024)).toFixed(1);

  return (
    <div className="w-full max-w-7xl mx-auto px-6 py-8 space-y-6">
      {/* 1. Header & Quick Metrics */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-xs font-mono text-slate-500 dark:text-slate-400 mb-1">
            <span>Workspace</span>
            <span>/</span>
            <span className="text-primary dark:text-indigo-400 font-semibold">Documents</span>
          </div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100 tracking-tight">
            Your Documents
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-0.5">
            Upload PDFs, parse vector embeddings, and initiate contextual conversational analysis.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex items-center gap-3 bg-white dark:bg-slate-900 px-4 py-2 rounded-xl border border-slate-200 dark:border-slate-800 shadow-xs">
            <div className="w-8 h-8 rounded-lg bg-indigo-50 dark:bg-indigo-950/60 flex items-center justify-center text-primary dark:text-indigo-300">
              <FolderOpen className="w-4 h-4" />
            </div>
            <div>
              <div className="text-[10px] text-slate-400 dark:text-slate-500 uppercase font-semibold">
                Repository
              </div>
              <div className="text-sm font-semibold text-slate-800 dark:text-slate-200">
                {metadata?.totalItems || documents.length} files
              </div>
            </div>
          </div>

          <div className="flex items-center gap-3 bg-white dark:bg-slate-900 px-4 py-2 rounded-xl border border-slate-200 dark:border-slate-800 shadow-xs">
            <div className="w-8 h-8 rounded-lg bg-slate-100 dark:bg-slate-800 flex items-center justify-center text-slate-600 dark:text-slate-300">
              <PieChart className="w-4 h-4" />
            </div>
            <div>
              <div className="text-[10px] text-slate-400 dark:text-slate-500 uppercase font-semibold">
                Page Total
              </div>
              <div className="text-sm font-semibold text-slate-800 dark:text-slate-200">
                {totalMB} MB total
              </div>
            </div>
          </div>

          <Button
            variant="primary"
            size="md"
            onClick={() => {
              setChatTargetDocIds([]);
              setIsNewChatOpen(true);
            }}
            leftIcon={<Plus className="w-4 h-4" />}
          >
            New Chat
          </Button>
        </div>
      </div>

      {/* 2. Drag and Drop PDF Upload Box */}
      <div className="space-y-3">
        <div
          onDragOver={(e) => {
            e.preventDefault();
            setIsDragging(true);
          }}
          onDragLeave={() => setIsDragging(false)}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
          className={`relative group cursor-pointer bg-white dark:bg-slate-900 rounded-xl border-2 border-dashed p-8 text-center transition-all ${
            isDragging
              ? "border-primary bg-indigo-50/50 dark:bg-indigo-950/20"
              : "border-slate-300 dark:border-slate-700 hover:border-primary dark:hover:border-primary hover:bg-slate-50/50 dark:hover:bg-slate-800/40"
          }`}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf"
            className="hidden"
            onChange={(e) => {
              if (e.target.files && e.target.files.length > 0) {
                handleFileSelect(e.target.files[0]);
                e.target.value = "";
              }
            }}
          />
          <div className="flex flex-col items-center justify-center pointer-events-none">
            <div className="w-12 h-12 rounded-xl bg-indigo-50 dark:bg-indigo-950/60 text-primary dark:text-indigo-300 group-hover:bg-primary group-hover:text-white flex items-center justify-center mb-3 transition-colors shadow-xs">
              <UploadCloud className="w-6 h-6" />
            </div>
            <div className="text-sm font-semibold text-slate-900 dark:text-slate-100 group-hover:text-primary dark:group-hover:text-indigo-400 transition-colors">
              Drag and drop a PDF here, or <span className="text-primary dark:text-indigo-400 underline">browse files</span>
            </div>
            <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
              Single PDF files up to 20 MB · Vectorized chunking instantly enabled
            </p>
            <div className="mt-3 inline-flex items-center gap-1.5 bg-slate-100 dark:bg-slate-800 px-3 py-1 rounded-full text-[11px] text-slate-600 dark:text-slate-300 font-medium">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />
              Automatic OCR, Page Extraction &amp; Embedding Pipeline
            </div>
          </div>
        </div>

        {/* Upload Progress Bar */}
        {uploadProgress !== null && (
          <div className="bg-white dark:bg-slate-900 rounded-xl p-4 border border-slate-200 dark:border-slate-800 shadow-sm flex items-center justify-between gap-4 animate-in fade-in">
            <div className="flex items-center gap-3 min-w-0">
              <div className="w-9 h-9 rounded-lg bg-indigo-50 dark:bg-indigo-950/60 text-primary dark:text-indigo-300 flex items-center justify-center shrink-0">
                <FileText className="w-5 h-5" />
              </div>
              <div className="min-w-0">
                <div className="text-xs font-semibold text-slate-900 dark:text-slate-100 truncate">
                  {uploadingFileName}
                </div>
                <div className="text-[11px] text-slate-500 dark:text-slate-400">
                  Uploading &amp; generating token embeddings... {uploadProgress}%
                </div>
              </div>
            </div>
            <div className="flex items-center gap-4 w-48">
              <div className="w-full h-2 bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden">
                <div
                  className="h-full bg-primary rounded-full transition-all duration-300"
                  style={{ width: `${uploadProgress}%` }}
                />
              </div>
            </div>
          </div>
        )}

        {uploadError && (
          <div className="p-3 rounded-lg bg-rose-50 dark:bg-rose-950/50 border border-rose-200 dark:border-rose-900 flex items-center justify-between text-xs text-rose-700 dark:text-rose-300">
            <div className="flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{uploadError}</span>
            </div>
            <button
              onClick={() => setUploadError(null)}
              className="text-rose-500 dark:text-rose-400 hover:text-rose-800 dark:hover:text-rose-200"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        )}
      </div>

      {/* 3. Documents Master Table */}
      <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm overflow-hidden flex flex-col transition-colors">
        {/* Toolbar */}
        <div className="p-4 bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800 flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
          <div className="flex items-center gap-2.5">
            <h2 className="text-sm font-bold text-slate-900 dark:text-slate-100">All documents</h2>
            <span className="text-[11px] font-semibold px-2 py-0.5 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400">
              {metadata?.totalItems ?? documents.length} files
            </span>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <div className="relative w-56">
              <Search className="w-4 h-4 text-slate-400 dark:text-slate-500 absolute left-3 top-2.5 pointer-events-none" />
              <input
                type="text"
                placeholder="Filter by title..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full h-9 pl-9 pr-3 text-xs bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-900 dark:text-slate-100 rounded-md focus:outline-none focus:bg-white dark:focus:bg-slate-800 focus:ring-2 focus:ring-primary/20 focus:border-primary"
              />
            </div>

            <select
              value={statusFilter}
              onChange={(e) => {
                setStatusFilter(e.target.value);
                setPage(1);
              }}
              className="h-9 px-3 text-xs bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-md focus:outline-none focus:bg-white dark:focus:bg-slate-800 focus:ring-2 focus:ring-primary/20 cursor-pointer font-medium text-slate-700 dark:text-slate-300"
            >
              <option value="all">All statuses</option>
              <option value="READY">Ready</option>
              <option value="PROCESSING">Processing</option>
              <option value="UPLOADED">Uploaded</option>
              <option value="FAILED">Failed</option>
            </select>

            <button
              onClick={() => refetch()}
              title="Refresh list"
              className="h-9 w-9 rounded-md border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 flex items-center justify-center text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200 hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isFetching ? "animate-spin" : ""}`} />
            </button>
          </div>
        </div>

        {/* Table Content */}
        {isLoading ? (
          <div className="p-4">
            <SkeletonTable rows={5} cols={5} />
          </div>
        ) : documents.length === 0 ? (
          /* Empty State */
          <div className="p-12 text-center flex flex-col items-center justify-center">
            <div className="w-14 h-14 rounded-2xl bg-indigo-50 dark:bg-indigo-950/60 border border-indigo-100 dark:border-indigo-900 flex items-center justify-center text-primary dark:text-indigo-400 mb-3 shadow-xs">
              <FileText className="w-7 h-7" />
            </div>
            <h3 className="text-base font-bold text-slate-900 dark:text-slate-100 mb-1">
              Upload your first PDF
            </h3>
            <p className="text-xs text-slate-500 dark:text-slate-400 max-w-sm mb-5">
              We&apos;ll parse it, chunk the pages, and let you ask questions grounded in your document.
            </p>
            <Button
              variant="primary"
              size="md"
              onClick={() => fileInputRef.current?.click()}
              leftIcon={<UploadCloud className="w-4 h-4" />}
            >
              Upload PDF
            </Button>
          </div>
        ) : (
          <div>
            <Table className="border-none">
              <TableHeader>
                <TableRow>
                  <TableHead className="w-2/5">Document</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Pages</TableHead>
                  <TableHead>File Size</TableHead>
                  <TableHead>Created</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredDocs.map((doc) => (
                  <TableRow key={doc.id}>
                    <TableCell className="font-medium text-slate-900 dark:text-slate-100">
                      <div className="flex items-center gap-2.5">
                        <FileText className="w-4 h-4 text-slate-400 dark:text-slate-500 shrink-0" />
                        <div className="flex flex-col min-w-0">
                          <span className="truncate text-xs font-semibold" title={doc.title}>
                            {doc.title}
                          </span>
                          <span className="text-[11px] text-slate-400 dark:text-slate-500 truncate font-mono">
                            {doc.originalFilename}
                          </span>
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <StatusBadge status={doc.status} />
                    </TableCell>
                    <TableCell className="text-xs text-slate-600 dark:text-slate-300 font-mono">
                      {doc.pageCount ? `${doc.pageCount} pgs` : "—"}
                    </TableCell>
                    <TableCell className="text-xs text-slate-600 dark:text-slate-300 font-mono">
                      {(doc.fileSize / 1024).toFixed(1)} KB
                    </TableCell>
                    <TableCell className="text-xs text-slate-500 dark:text-slate-400">
                      {new Date(doc.createdOn).toLocaleDateString()}
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex items-center justify-end gap-1.5">
                        {doc.status === "READY" && (
                          <Button
                            variant="secondary"
                            size="sm"
                            onClick={() => handleStartChatWithDoc(doc.id)}
                            leftIcon={<MessageSquare className="w-3.5 h-3.5 text-primary dark:text-indigo-400" />}
                          >
                            Chat
                          </Button>
                        )}
                        <button
                          onClick={() => {
                            if (window.confirm(`Delete "${doc.title}"?`)) {
                              deleteMutation.mutate(doc.id);
                            }
                          }}
                          className="p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 dark:hover:bg-rose-950/40 rounded-md transition-colors"
                          title="Delete Document"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>

            {/* Pagination Controls */}
            {metadata && metadata.totalPages > 1 && (
              <div className="p-4 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between text-xs text-slate-500 dark:text-slate-400">
                <span>
                  Page {metadata.currentPage} of {metadata.totalPages} ({metadata.totalItems} total)
                </span>
                <div className="flex items-center gap-1.5">
                  <Button
                    variant="secondary"
                    size="sm"
                    disabled={metadata.currentPage <= 1}
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                    leftIcon={<ChevronLeft className="w-3.5 h-3.5" />}
                  >
                    Previous
                  </Button>
                  <Button
                    variant="secondary"
                    size="sm"
                    disabled={metadata.currentPage >= metadata.totalPages}
                    onClick={() => setPage((p) => p + 1)}
                    rightIcon={<ChevronRight className="w-3.5 h-3.5" />}
                  >
                    Next
                  </Button>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Start New Chat Modal */}
      <NewChatModal
        isOpen={isNewChatOpen}
        onClose={() => {
          setIsNewChatOpen(false);
          setChatTargetDocIds([]);
        }}
        documents={documents}
        initialSelectedDocIds={chatTargetDocIds}
      />
    </div>
  );
};
