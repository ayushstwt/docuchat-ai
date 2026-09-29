import React, { useState, useEffect, useRef, useMemo } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Search,
  MessageSquare,
  Send,
  Square,
  Sparkles,
  BookOpen,
  Trash2,
  FileText,
  Plus,
} from "lucide-react";
import { conversationsApi } from "../api/conversations";
import { documentsApi } from "../api/documents";
import { streamMessage } from "../api/stream";
import { Source } from "../api/types";
import { MessageBubble } from "../components/chat/MessageBubble";
import { SourceDrawer } from "../components/chat/SourceDrawer";
import { NewChatModal } from "../components/chat/NewChatModal";
import { Button } from "../components/ui/Button";
import { useToast } from "../components/ui/Toast";
import { ApiError } from "../api/client";

export const ChatPage: React.FC = () => {
  const { conversationId } = useParams<{ conversationId?: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const toast = useToast();

  const selectedConvId = conversationId ? parseInt(conversationId, 10) : null;

  // Conversations list query
  const { data: convData, isLoading: isLoadingConvs } = useQuery({
    queryKey: ["conversations"],
    queryFn: async () => {
      return await conversationsApi.list({ page: 1, size: 50 });
    },
  });

  const conversations = convData?.items || [];

  // Documents list query for the modal & doc names
  const { data: docsData } = useQuery({
    queryKey: ["documents", "all"],
    queryFn: async () => {
      return await documentsApi.list({ page: 1, size: 100 });
    },
  });

  const documents = docsData?.items || [];
  const docMap = useMemo(() => {
    const map = new Map<number, string>();
    documents.forEach((d) => map.set(d.id, d.title));
    return map;
  }, [documents]);

  // If no conversationId is in URL but conversations exist, navigate to the first one
  useEffect(() => {
    if (!conversationId && conversations.length > 0) {
      navigate(`/chat/${conversations[0].id}`, { replace: true });
    }
  }, [conversationId, conversations, navigate]);

  // Current active conversation
  const activeConversation = useMemo(() => {
    return conversations.find((c) => c.id === selectedConvId);
  }, [conversations, selectedConvId]);

  // Messages list query for selected conversation
  const { data: messagesData, isLoading: isLoadingMessages } = useQuery({
    queryKey: ["messages", selectedConvId],
    queryFn: async () => {
      if (!selectedConvId) return null;
      return await conversationsApi.listMessages(selectedConvId, {
        page: 1,
        size: 100,
      });
    },
    enabled: !!selectedConvId,
  });

  const historicalMessages = messagesData?.items || [];

  // Local state for streaming response & input
  const [inputMessage, setInputMessage] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamingContent, setStreamingContent] = useState("");
  const [streamingSources, setStreamingSources] = useState<Source[]>([]);
  const [activeSource, setActiveSource] = useState<Source | null>(null);
  const [isNewChatOpen, setIsNewChatOpen] = useState(false);
  const [chatSearch, setChatSearch] = useState("");

  const abortControllerRef = useRef<AbortController | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [historicalMessages, streamingContent]);

  // Delete conversation mutation
  const deleteConvMutation = useMutation({
    mutationFn: async (id: number) => {
      return await conversationsApi.delete(id);
    },
    onSuccess: (_, deletedId) => {
      toast.info("Conversation deleted.");
      queryClient.invalidateQueries({ queryKey: ["conversations"] });
      if (selectedConvId === deletedId) {
        navigate("/chat", { replace: true });
      }
    },
    onError: (err: unknown) => {
      const msg =
        err instanceof ApiError ? err.message : "Failed to delete conversation.";
      toast.error(msg);
    },
  });

  // Stop streaming handler
  const handleStopStreaming = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setIsStreaming(false);
  };

  // Submit message handler
  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputMessage.trim() || isStreaming || !selectedConvId) return;

    const question = inputMessage.trim();
    setInputMessage("");
    setIsStreaming(true);
    setStreamingContent("");
    setStreamingSources([]);

    // Optimistically update or start streaming
    abortControllerRef.current = new AbortController();

    try {
      await streamMessage(
        selectedConvId,
        question,
        {
          onSources: (sources) => {
            setStreamingSources(sources);
          },
          onToken: (token) => {
            setStreamingContent((prev) => prev + token);
          },
          onDone: () => {
            setIsStreaming(false);
            setStreamingContent("");
            setStreamingSources([]);
            queryClient.invalidateQueries({
              queryKey: ["messages", selectedConvId],
            });
            queryClient.invalidateQueries({ queryKey: ["conversations"] });
          },
          onError: (err) => {
            setIsStreaming(false);
            toast.error(err.message, "Chat Error");
          },
        },
        abortControllerRef.current.signal
      );
    } catch (err: unknown) {
      setIsStreaming(false);
      if (err instanceof ApiError) {
        toast.error(err.message);
      } else if (err instanceof Error && err.name !== "AbortError") {
        toast.error("Failed to stream response.");
      }
    }
  };

  const filteredConversations = useMemo(() => {
    if (!chatSearch.trim()) return conversations;
    return conversations.filter((c) =>
      c.title.toLowerCase().includes(chatSearch.toLowerCase())
    );
  }, [conversations, chatSearch]);

  return (
    <div className="flex h-full w-full overflow-hidden bg-slate-50">
      {/* 1. Conversations Sidebar */}
      <aside className="w-64 bg-white border-r border-slate-200 flex flex-col justify-between shrink-0 h-full">
        {/* Top actions & search */}
        <div className="p-3 border-b border-slate-100 flex flex-col gap-2.5">
          <Button
            variant="primary"
            size="md"
            className="w-full justify-center"
            onClick={() => setIsNewChatOpen(true)}
            leftIcon={<Plus className="w-4 h-4" />}
          >
            New chat
          </Button>

          <div className="relative w-full">
            <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-2.5 pointer-events-none" />
            <input
              type="text"
              placeholder="Search chats..."
              value={chatSearch}
              onChange={(e) => setChatSearch(e.target.value)}
              className="w-full h-8 pl-8 pr-2.5 text-xs bg-slate-50 border border-slate-200 rounded-md focus:outline-none focus:bg-white focus:ring-2 focus:ring-primary/20 focus:border-primary"
            />
          </div>
        </div>

        {/* Conversation list */}
        <div className="flex-1 overflow-y-auto p-2 space-y-1">
          {isLoadingConvs ? (
            <div className="p-4 text-center text-xs text-slate-400">
              Loading chats...
            </div>
          ) : filteredConversations.length === 0 ? (
            <div className="p-4 text-center text-xs text-slate-400">
              No conversations found.
            </div>
          ) : (
            filteredConversations.map((conv) => {
              const isActive = conv.id === selectedConvId;
              return (
                <div
                  key={conv.id}
                  onClick={() => navigate(`/chat/${conv.id}`)}
                  className={`group relative rounded-lg p-2.5 flex items-center justify-between cursor-pointer transition-colors ${
                    isActive
                      ? "bg-indigo-50/80 text-primary border border-indigo-100 font-medium"
                      : "text-slate-700 hover:bg-slate-100 hover:text-slate-900"
                  }`}
                >
                  <div className="flex items-center gap-2.5 min-w-0 pr-1">
                    <MessageSquare
                      className={`w-4 h-4 shrink-0 ${
                        isActive ? "text-primary" : "text-slate-400"
                      }`}
                    />
                    <div className="min-w-0 flex flex-col">
                      <span className="text-xs truncate font-medium">
                        {conv.title}
                      </span>
                      <span className="text-[10px] text-slate-400 font-mono">
                        {conv.documentIds.length} doc
                        {conv.documentIds.length === 1 ? "" : "s"}
                      </span>
                    </div>
                  </div>

                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      if (window.confirm(`Delete conversation "${conv.title}"?`)) {
                        deleteConvMutation.mutate(conv.id);
                      }
                    }}
                    className="opacity-0 group-hover:opacity-100 p-1 rounded text-slate-400 hover:text-rose-600 transition-opacity"
                    title="Delete Chat"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              );
            })
          )}
        </div>
      </aside>

      {/* 2. Chat Feed Area */}
      <main className="flex-1 flex flex-col min-w-0 bg-slate-50 h-full relative">
        {activeConversation ? (
          <>
            {/* Header */}
            <header className="h-14 px-6 bg-white border-b border-slate-200 shrink-0 flex items-center justify-between z-10">
              <div className="flex items-center gap-3 min-w-0">
                <div className="flex items-center gap-2 min-w-0">
                  <h2 className="text-sm font-bold text-slate-900 truncate">
                    {activeConversation.title}
                  </h2>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 font-medium flex items-center gap-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                    Grounded
                  </span>
                </div>

                {/* Grounding documents chips */}
                <div className="hidden lg:flex items-center gap-1.5 pl-3 border-l border-slate-200">
                  {activeConversation.documentIds.map((docId) => (
                    <span
                      key={docId}
                      className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-slate-100 text-slate-600 text-[11px] font-mono max-w-[140px] truncate"
                    >
                      <FileText className="w-3 h-3 text-primary shrink-0" />
                      <span className="truncate">
                        {docMap.get(docId) || `Doc #${docId}`}
                      </span>
                    </span>
                  ))}
                </div>
              </div>

              {/* Header Right Actions */}
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() =>
                    setActiveSource((prev) =>
                      prev
                        ? null
                        : streamingSources[0] ||
                          historicalMessages[historicalMessages.length - 1]?.sources?.[0] ||
                          null
                    )
                  }
                  className="p-1.5 rounded-lg border border-slate-200 text-slate-600 hover:bg-slate-100 hover:text-slate-900 transition-colors"
                  title="Toggle Sources"
                >
                  <BookOpen className="w-4 h-4" />
                </button>
              </div>
            </header>

            {/* Messages Thread */}
            <div className="flex-1 overflow-y-auto px-4 md:px-8 py-6 space-y-5">
              <div className="max-w-3xl mx-auto space-y-5">
                {isLoadingMessages ? (
                  <div className="p-8 text-center text-xs text-slate-400">
                    Loading message history...
                  </div>
                ) : historicalMessages.length === 0 && !isStreaming ? (
                  <div className="p-12 text-center flex flex-col items-center justify-center">
                    <div className="w-12 h-12 rounded-xl bg-indigo-50 text-primary flex items-center justify-center mb-3">
                      <Sparkles className="w-6 h-6" />
                    </div>
                    <h3 className="text-base font-bold text-slate-900 mb-1">
                      Ask anything about your documents
                    </h3>
                    <p className="text-xs text-slate-500 max-w-sm">
                      Responses are strictly grounded in your uploaded documents and include verified citations.
                    </p>
                  </div>
                ) : (
                  historicalMessages.map((msg) => (
                    <MessageBubble
                      key={msg.id}
                      message={msg}
                      onSelectSource={(src) => setActiveSource(src)}
                    />
                  ))
                )}

                {/* Streaming Assistant Response */}
                {isStreaming && (
                  <MessageBubble
                    message={{
                      role: "ASSISTANT",
                      content: streamingContent,
                      sources: streamingSources,
                      isStreaming: true,
                    }}
                    onSelectSource={(src) => setActiveSource(src)}
                  />
                )}

                <div ref={messagesEndRef} />
              </div>
            </div>

            {/* Bottom Chat Input Bar */}
            <footer className="p-4 bg-white border-t border-slate-200 shrink-0">
              <div className="max-w-3xl mx-auto space-y-2">
                {isStreaming && (
                  <div className="flex justify-center mb-1">
                    <button
                      type="button"
                      onClick={handleStopStreaming}
                      className="inline-flex items-center gap-1.5 px-3 py-1 bg-white hover:bg-rose-50 text-rose-600 rounded-full border border-rose-200 shadow-xs text-xs font-medium transition-colors"
                    >
                      <Square className="w-3 h-3 fill-current" />
                      Stop generating
                    </button>
                  </div>
                )}

                <form
                  onSubmit={handleSendMessage}
                  className="bg-slate-50 rounded-xl p-2.5 border border-slate-200 focus-within:bg-white focus-within:ring-2 focus-within:ring-primary/20 focus-within:border-primary transition-all shadow-xs"
                >
                  <textarea
                    rows={2}
                    value={inputMessage}
                    onChange={(e) => setInputMessage(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" && !e.shiftKey) {
                        e.preventDefault();
                        handleSendMessage(e);
                      }
                    }}
                    placeholder="Ask a question about your documents, compare metrics, or cite specifics..."
                    className="w-full bg-transparent text-sm text-slate-900 placeholder:text-slate-400 outline-none resize-none font-sans"
                  />

                  <div className="flex items-center justify-between pt-1 border-t border-slate-100">
                    <span className="text-[10px] text-slate-400 font-mono">
                      {inputMessage.length} / 4,000
                    </span>

                    <Button
                      type="submit"
                      variant="primary"
                      size="sm"
                      disabled={!inputMessage.trim() || isStreaming}
                      className="rounded-full w-8 h-8 p-0"
                    >
                      <Send className="w-3.5 h-3.5" />
                    </Button>
                  </div>
                </form>

                <div className="flex items-center justify-center gap-2 text-[11px] text-slate-400">
                  <span>Enter to send · Shift+Enter for new line</span>
                  <span>•</span>
                  <span className="text-emerald-600 font-medium">Grounded RAG Guard active</span>
                </div>
              </div>
            </footer>
          </>
        ) : (
          /* Empty / No Selected Conversation */
          <div className="flex-1 flex flex-col items-center justify-center p-8 text-center">
            <div className="w-14 h-14 rounded-2xl bg-indigo-50 border border-indigo-100 flex items-center justify-center text-primary mb-3 shadow-xs">
              <MessageSquare className="w-7 h-7" />
            </div>
            <h3 className="text-lg font-bold text-slate-900 mb-1">
              Start a new conversation
            </h3>
            <p className="text-xs text-slate-500 max-w-sm mb-5">
              Select one or more indexed documents to begin asking questions.
            </p>
            <Button
              variant="primary"
              size="md"
              onClick={() => setIsNewChatOpen(true)}
              leftIcon={<Plus className="w-4 h-4" />}
            >
              Start Chat
            </Button>
          </div>
        )}
      </main>

      {/* 3. Verified Sources Inspector Panel */}
      <SourceDrawer
        source={activeSource}
        onClose={() => setActiveSource(null)}
      />

      {/* New Chat Modal */}
      <NewChatModal
        isOpen={isNewChatOpen}
        onClose={() => setIsNewChatOpen(false)}
        documents={documents}
      />
    </div>
  );
};
