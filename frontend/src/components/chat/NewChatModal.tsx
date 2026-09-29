import React, { useState, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import {
  MessageSquarePlus,
  Search,
  Check,
  FileText,
  AlertCircle,
  Sparkles,
} from "lucide-react";
import { Modal } from "../ui/Modal";
import { Button } from "../ui/Button";
import { Document } from "../../api/types";
import { conversationsApi } from "../../api/conversations";
import { ApiError } from "../../api/client";

export interface NewChatModalProps {
  isOpen: boolean;
  onClose: () => void;
  documents: Document[];
  initialSelectedDocIds?: number[];
}

export const NewChatModal: React.FC<NewChatModalProps> = ({
  isOpen,
  onClose,
  documents,
  initialSelectedDocIds = [],
}) => {
  const [selectedIds, setSelectedIds] = useState<number[]>(initialSelectedDocIds);
  const [title, setTitle] = useState("");
  const [search, setSearch] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const navigate = useNavigate();

  // Filter only READY documents
  const readyDocuments = useMemo(
    () => documents.filter((doc) => doc.status === "READY"),
    [documents]
  );

  const filteredDocs = useMemo(() => {
    if (!search.trim()) return readyDocuments;
    return readyDocuments.filter((d) =>
      d.title.toLowerCase().includes(search.toLowerCase())
    );
  }, [readyDocuments, search]);

  const toggleSelect = (id: number) => {
    setSelectedIds((prev) =>
      prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id]
    );
  };

  const selectAll = () => {
    if (selectedIds.length === readyDocuments.length) {
      setSelectedIds([]);
    } else {
      setSelectedIds(readyDocuments.map((d) => d.id));
    }
  };

  const handleStartChat = async (e: React.FormEvent) => {
    e.preventDefault();
    if (selectedIds.length === 0) {
      setErrorMsg("Please select at least one document for grounding.");
      return;
    }

    try {
      setIsLoading(true);
      setErrorMsg(null);
      const conversation = await conversationsApi.create({
        documentIds: selectedIds,
        title: title.trim() || undefined,
      });
      onClose();
      navigate(`/chat/${conversation.id}`);
    } catch (err: unknown) {
      if (err instanceof ApiError) {
        setErrorMsg(err.message);
      } else {
        setErrorMsg("Failed to start conversation. Please try again.");
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} maxWidth="xl">
      <div className="flex flex-col gap-4">
        {/* Header */}
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-indigo-50 text-primary flex items-center justify-center">
            <MessageSquarePlus className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-slate-900 tracking-tight">
              Start a new chat
            </h3>
            <p className="text-xs text-slate-500">
              Select one or more indexed documents to ground your conversation with verified citations.
            </p>
          </div>
        </div>

        {errorMsg && (
          <div className="p-3 rounded-lg bg-rose-50 border border-rose-200 flex items-center gap-2 text-rose-700 text-xs">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{errorMsg}</span>
          </div>
        )}

        <form onSubmit={handleStartChat} className="flex flex-col gap-4">
          {/* Custom title input (optional) */}
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">
              Conversation Title (optional)
            </label>
            <input
              type="text"
              placeholder="e.g., Q3 Earnings Analysis"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full h-10 px-3 rounded-md bg-white border border-slate-300 text-sm placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary"
            />
          </div>

          {/* Search bar & Selection status */}
          <div className="flex flex-col gap-2">
            <div className="flex items-center justify-between text-xs text-slate-600">
              <span className="font-semibold">Select Grounding Documents:</span>
              {readyDocuments.length > 0 && (
                <button
                  type="button"
                  onClick={selectAll}
                  className="text-primary hover:text-primary-hover font-semibold hover:underline"
                >
                  {selectedIds.length === readyDocuments.length
                    ? "Deselect all"
                    : "Select all ready"}
                </button>
              )}
            </div>

            <div className="relative">
              <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3 pointer-events-none" />
              <input
                type="text"
                placeholder="Search ready documents..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full h-9 pl-9 pr-3 text-xs bg-slate-50 border border-slate-200 rounded-md focus:outline-none focus:bg-white focus:ring-2 focus:ring-primary/20 focus:border-primary"
              />
            </div>
          </div>

          {/* Document list */}
          <div className="max-h-60 overflow-y-auto border border-slate-200 rounded-lg divide-y divide-slate-100 bg-slate-50/50">
            {readyDocuments.length === 0 ? (
              <div className="p-6 text-center text-xs text-slate-500">
                No indexed documents ready for chat. Please upload and wait for indexing.
              </div>
            ) : filteredDocs.length === 0 ? (
              <div className="p-6 text-center text-xs text-slate-500">
                No documents match &ldquo;{search}&rdquo;
              </div>
            ) : (
              filteredDocs.map((doc) => {
                const isSelected = selectedIds.includes(doc.id);
                return (
                  <div
                    key={doc.id}
                    onClick={() => toggleSelect(doc.id)}
                    className={`flex items-center justify-between p-3 cursor-pointer transition-colors ${
                      isSelected
                        ? "bg-indigo-50/80 border-l-4 border-l-primary"
                        : "hover:bg-white"
                    }`}
                  >
                    <div className="flex items-center gap-2.5 min-w-0">
                      <div
                        className={`w-5 h-5 rounded border flex items-center justify-center shrink-0 transition-colors ${
                          isSelected
                            ? "bg-primary border-primary text-white"
                            : "border-slate-300 bg-white"
                        }`}
                      >
                        {isSelected && <Check className="w-3.5 h-3.5" />}
                      </div>
                      <FileText className="w-4 h-4 text-slate-400 shrink-0" />
                      <div className="flex flex-col min-w-0">
                        <span className="text-xs font-semibold text-slate-800 truncate">
                          {doc.title}
                        </span>
                        <span className="text-[11px] text-slate-400 font-mono">
                          {doc.pageCount ? `${doc.pageCount} pages · ` : ""}
                          {(doc.fileSize / 1024).toFixed(1)} KB
                        </span>
                      </div>
                    </div>
                  </div>
                );
              })
            )}
          </div>

          {/* Footer buttons */}
          <div className="flex items-center justify-between pt-2 border-t border-slate-100">
            <span className="text-xs text-slate-500 font-medium">
              {selectedIds.length} document{selectedIds.length === 1 ? "" : "s"} selected
            </span>
            <div className="flex items-center gap-2">
              <Button type="button" variant="secondary" size="md" onClick={onClose}>
                Cancel
              </Button>
              <Button
                type="submit"
                variant="primary"
                size="md"
                disabled={selectedIds.length === 0}
                isLoading={isLoading}
                rightIcon={<Sparkles className="w-4 h-4" />}
              >
                Start Chat
              </Button>
            </div>
          </div>
        </form>
      </div>
    </Modal>
  );
};
