import React, { useState, useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  History,
  Search,
  RefreshCw,
  LogIn,
  UploadCloud,
  FileText,
  Bot,
  MessageSquare,
  Sparkles,
  ChevronLeft,
  ChevronRight,
  ShieldCheck,
  CheckCircle2,
  XCircle,
} from "lucide-react";
import { activityLogsApi } from "../api/activityLogs";
import { Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from "../components/ui/Table";
import { Button } from "../components/ui/Button";

export const ActivityLogsPage: React.FC = () => {
  const [page, setPage] = useState(1);
  const [size] = useState(15);
  const [search, setSearch] = useState("");
  const [actionFilter, setActionFilter] = useState<string>("all");

  const { data, isLoading, isFetching, refetch } = useQuery({
    queryKey: ["activity-logs", page, size],
    queryFn: async () => {
      return await activityLogsApi.list({ page, size });
    },
  });

  const logs = data?.items || [];
  const metadata = data?.metadata;

  const filteredLogs = useMemo(() => {
    return logs.filter((log) => {
      const matchesFilter =
        actionFilter === "all" || log.action.toLowerCase() === actionFilter.toLowerCase();
      const matchesSearch =
        !search.trim() ||
        log.action.toLowerCase().includes(search.toLowerCase()) ||
        log.subAction.toLowerCase().includes(search.toLowerCase());
      return matchesFilter && matchesSearch;
    });
  }, [logs, actionFilter, search]);

  const getActionIcon = (action: string) => {
    switch (action) {
      case "USER_LOGIN":
        return <LogIn className="w-4 h-4 text-primary" />;
      case "DOCUMENT_UPLOAD":
        return <UploadCloud className="w-4 h-4 text-blue-600" />;
      case "DOCUMENT_CHUNK":
        return <FileText className="w-4 h-4 text-indigo-600" />;
      case "DOCUMENT_EMBED":
        return <Sparkles className="w-4 h-4 text-emerald-600" />;
      case "CONVERSATION_CREATE":
        return <MessageSquare className="w-4 h-4 text-purple-600" />;
      case "CHAT_MESSAGE":
        return <Bot className="w-4 h-4 text-primary" />;
      default:
        return <History className="w-4 h-4 text-slate-500" />;
    }
  };

  const getActionLabel = (action: string) => {
    switch (action) {
      case "USER_LOGIN":
        return "User Login Session";
      case "DOCUMENT_UPLOAD":
        return "Document Upload";
      case "DOCUMENT_CHUNK":
        return "PDF Text & Page Chunking";
      case "DOCUMENT_EMBED":
        return "pgvector Embedding Generation";
      case "CONVERSATION_CREATE":
        return "Conversation Session Created";
      case "CHAT_MESSAGE":
        return "Chat RAG Inference Stream";
      default:
        return action;
    }
  };

  const totalEvents = metadata?.totalItems || logs.length;
  const successEvents = logs.filter((l) => l.subAction === "SUCCESS").length;
  const successRate = logs.length > 0 ? Math.round((successEvents / logs.length) * 100) : 100;

  return (
    <div className="w-full max-w-7xl mx-auto px-6 py-8 space-y-6">
      {/* 1. Header & Workspace Meta */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-xs font-mono text-slate-500 mb-1">
            <span>Workspace</span>
            <span>/</span>
            <span className="text-primary font-semibold">Audit &amp; Activity</span>
          </div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">
            Activity Log
          </h1>
          <p className="text-sm text-slate-500 mt-0.5">
            Audit trail of security events, document operations, and workspace chat inferences.
          </p>
        </div>

        {/* Action toolbar */}
        <div className="flex flex-wrap items-center gap-2">
          <div className="relative w-56">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5 pointer-events-none" />
            <input
              type="text"
              placeholder="Search activity..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full h-9 pl-9 pr-3 text-xs bg-white border border-slate-200 rounded-md focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary shadow-xs"
            />
          </div>

          <select
            value={actionFilter}
            onChange={(e) => setActionFilter(e.target.value)}
            className="h-9 px-3 text-xs bg-white border border-slate-200 rounded-md focus:outline-none focus:ring-2 focus:ring-primary/20 cursor-pointer font-medium text-slate-700 shadow-xs"
          >
            <option value="all">All actions</option>
            <option value="USER_LOGIN">Authentication</option>
            <option value="DOCUMENT_UPLOAD">Uploads</option>
            <option value="DOCUMENT_CHUNK">Chunking</option>
            <option value="DOCUMENT_EMBED">Embeddings</option>
            <option value="CONVERSATION_CREATE">Conversations</option>
            <option value="CHAT_MESSAGE">Chat Inference</option>
          </select>

          <button
            onClick={() => refetch()}
            title="Refresh logs"
            className="h-9 w-9 rounded-md border border-slate-200 bg-white flex items-center justify-center text-slate-500 hover:text-slate-800 hover:bg-slate-50 transition-colors shadow-xs"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isFetching ? "animate-spin" : ""}`} />
          </button>
        </div>
      </div>

      {/* 2. KPI Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-white rounded-xl p-5 border border-slate-200 shadow-xs flex items-center justify-between">
          <div>
            <div className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">
              Total Logged Events
            </div>
            <div className="text-2xl font-bold text-slate-900 mt-1">
              {totalEvents}
            </div>
            <span className="text-[11px] text-slate-500">Persisted in Postgres</span>
          </div>
          <div className="w-10 h-10 rounded-xl bg-indigo-50 text-primary flex items-center justify-center">
            <History className="w-5 h-5" />
          </div>
        </div>

        <div className="bg-white rounded-xl p-5 border border-slate-200 shadow-xs flex items-center justify-between">
          <div>
            <div className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">
              Operation Success Rate
            </div>
            <div className="text-2xl font-bold text-emerald-600 mt-1">
              {successRate}%
            </div>
            <span className="text-[11px] text-slate-500">Standard runtime nominal</span>
          </div>
          <div className="w-10 h-10 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center">
            <CheckCircle2 className="w-5 h-5" />
          </div>
        </div>

        <div className="bg-white rounded-xl p-5 border border-slate-200 shadow-xs flex items-center justify-between">
          <div>
            <div className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">
              Security Compliance
            </div>
            <div className="text-2xl font-bold text-slate-900 mt-1">
              Enforced
            </div>
            <span className="text-[11px] text-slate-500">Multi-tenant scoped</span>
          </div>
          <div className="w-10 h-10 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center">
            <ShieldCheck className="w-5 h-5" />
          </div>
        </div>
      </div>

      {/* 3. Activity Logs Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden flex flex-col">
        {isLoading ? (
          <div className="p-12 text-center text-xs text-slate-400">
            Loading activity stream...
          </div>
        ) : filteredLogs.length === 0 ? (
          <div className="p-12 text-center text-xs text-slate-500">
            No activity logs recorded yet.
          </div>
        ) : (
          <div>
            <Table className="border-none">
              <TableHeader>
                <TableRow>
                  <TableHead className="w-1/2">Action Event</TableHead>
                  <TableHead>Result Status</TableHead>
                  <TableHead>Timestamp (UTC)</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredLogs.map((log) => (
                  <TableRow key={log.id}>
                    <TableCell className="font-medium text-slate-900">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-lg bg-slate-100 flex items-center justify-center shrink-0">
                          {getActionIcon(log.action)}
                        </div>
                        <div className="flex flex-col min-w-0">
                          <span className="text-xs font-semibold text-slate-800">
                            {getActionLabel(log.action)}
                          </span>
                          <span className="text-[10px] text-slate-400 font-mono">
                            {log.action}
                          </span>
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>
                      {log.subAction === "SUCCESS" ? (
                        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-50 border border-emerald-200 text-emerald-700">
                          <CheckCircle2 className="w-3 h-3 text-emerald-600" />
                          Success
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-rose-50 border border-rose-200 text-rose-700">
                          <XCircle className="w-3 h-3 text-rose-600" />
                          Failed
                        </span>
                      )}
                    </TableCell>
                    <TableCell className="text-xs text-slate-600 font-mono">
                      {new Date(log.createdOn).toLocaleString()}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>

            {/* Pagination Controls */}
            {metadata && metadata.totalPages > 1 && (
              <div className="p-4 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
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
    </div>
  );
};
