import React, { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import {
  Copy,
  Check,
  Sparkles,
} from "lucide-react";
import { Message, Source } from "../../api/types";
import { SourceChips } from "./SourceChips";

export interface MessageBubbleProps {
  message: Partial<Message> & { isStreaming?: boolean };
  onSelectSource?: (source: Source) => void;
}

export const MessageBubble: React.FC<MessageBubbleProps> = ({
  message,
  onSelectSource,
}) => {
  const isUser = message.role === "USER";
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    if (message.content) {
      navigator.clipboard.writeText(message.content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  if (isUser) {
    return (
      <div className="flex flex-col items-end gap-1 max-w-2xl ml-auto">
        <div className="bg-primary text-white px-4 py-3 rounded-2xl rounded-tr-xs shadow-xs text-sm leading-relaxed whitespace-pre-wrap">
          {message.content}
        </div>
        <span className="text-[10px] text-slate-400 font-mono pr-1">
          {message.createdOn
            ? new Date(message.createdOn).toLocaleTimeString([], {
                hour: "2-digit",
                minute: "2-digit",
              })
            : "Just now"}
        </span>
      </div>
    );
  }

  // Assistant Bubble
  return (
    <div className="flex items-start gap-3 max-w-3xl">
      {/* Bot Icon */}
      <div
        className={`w-8 h-8 rounded-lg bg-primary text-white flex items-center justify-center shrink-0 shadow-xs mt-0.5 ${
          message.isStreaming ? "animate-pulse" : ""
        }`}
      >
        <Sparkles className="w-4 h-4" />
      </div>

      <div className="flex-1 min-w-0 space-y-2">
        <div className="bg-white rounded-2xl rounded-tl-xs p-5 shadow-xs border border-slate-200/80 text-slate-900 space-y-3">
          {/* Content rendered with ReactMarkdown */}
          <div className="prose prose-sm max-w-none text-slate-800 leading-relaxed font-sans text-sm prose-p:my-2 prose-headings:font-semibold prose-code:font-mono prose-code:text-xs prose-code:bg-slate-100 prose-code:px-1.5 prose-code:py-0.5 prose-code:rounded prose-pre:bg-slate-900 prose-pre:text-slate-100 prose-table:my-3 prose-th:px-3 prose-th:py-2 prose-td:px-3 prose-td:py-2 prose-th:bg-slate-50 prose-table:border prose-th:border prose-td:border">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {message.content || ""}
            </ReactMarkdown>
            {message.isStreaming && (
              <span className="inline-block w-2 h-4 bg-primary ml-1 align-middle animate-pulse rounded-xs" />
            )}
          </div>

          {/* Sources Section */}
          {message.sources && message.sources.length > 0 && (
            <div className="pt-2 border-t border-slate-100">
              <div className="text-[11px] font-semibold uppercase text-slate-400 font-mono mb-1">
                Verified Sources
              </div>
              <SourceChips
                sources={message.sources}
                onSelectSource={onSelectSource}
              />
            </div>
          )}

          {/* Metadata & Actions */}
          {!message.isStreaming && (
            <div className="pt-2 flex items-center justify-between text-xs text-slate-400 border-t border-slate-50">
              <div className="flex items-center gap-3">
                <button
                  type="button"
                  onClick={handleCopy}
                  className="hover:text-slate-700 flex items-center gap-1 transition-colors cursor-pointer text-[11px]"
                >
                  {copied ? (
                    <>
                      <Check className="w-3.5 h-3.5 text-emerald-600" />
                      <span className="text-emerald-600 font-medium">Copied</span>
                    </>
                  ) : (
                    <>
                      <Copy className="w-3.5 h-3.5" />
                      <span>Copy</span>
                    </>
                  )}
                </button>
              </div>

              {message.createdOn && (
                <span className="text-[10px] font-mono">
                  {new Date(message.createdOn).toLocaleTimeString([], {
                    hour: "2-digit",
                    minute: "2-digit",
                  })}
                </span>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
