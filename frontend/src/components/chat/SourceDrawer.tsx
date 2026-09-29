import React from "react";
import { X, FileText, Sparkles, BookOpen } from "lucide-react";
import { Source } from "../../api/types";

export interface SourceDrawerProps {
  source: Source | null;
  onClose: () => void;
}

export const SourceDrawer: React.FC<SourceDrawerProps> = ({ source, onClose }) => {
  if (!source) return null;

  const scorePercentage = source.score
    ? Math.round(source.score * 100)
    : undefined;

  return (
    <aside className="w-80 shrink-0 h-full bg-white border-l border-slate-200 flex flex-col justify-between shadow-sm relative z-20 animate-in slide-in-from-right duration-200">
      {/* Header */}
      <div className="h-14 px-4 border-b border-slate-100 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <BookOpen className="w-4 h-4 text-primary" />
          <span className="text-sm font-bold text-slate-900">Verified Source</span>
          <span className="text-[11px] font-mono px-2 py-0.5 rounded-full bg-indigo-50 text-primary font-semibold">
            [{source.index}]
          </span>
        </div>
        <button
          onClick={onClose}
          className="p-1 rounded-md text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition-colors"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {/* Document Meta Card */}
        <div className="bg-slate-50 rounded-xl p-3.5 border border-slate-200/80 space-y-3">
          <div className="flex items-start justify-between gap-2">
            <div className="flex items-start gap-2 min-w-0">
              <FileText className="w-4 h-4 text-primary shrink-0 mt-0.5" />
              <div className="min-w-0">
                <div className="text-xs font-bold text-slate-900 truncate">
                  {source.documentTitle}
                </div>
                <div className="text-[11px] text-slate-500 font-mono">
                  Page {source.pageNumber}
                </div>
              </div>
            </div>
            {scorePercentage !== undefined && (
              <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 flex items-center gap-1 shrink-0 font-mono">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                {scorePercentage}% Match
              </span>
            )}
          </div>

          {/* Snippet extract */}
          <div className="bg-white rounded-lg p-3 border border-slate-200 space-y-1.5 shadow-xs">
            <div className="flex items-center justify-between text-[10px] text-slate-400 font-mono">
              <span>DOCUMENT EXTRACT</span>
              {source.score !== undefined && (
                <span>SIMILARITY: {source.score.toFixed(3)}</span>
              )}
            </div>
            <p className="text-xs text-slate-700 leading-relaxed font-serif bg-slate-50/50 p-2 rounded border border-slate-100 italic">
              &ldquo;{source.snippet}&rdquo;
            </p>
          </div>
        </div>
      </div>

      {/* Bottom Footer */}
      <div className="p-3 bg-slate-50 border-t border-slate-200 text-center">
        <div className="flex items-center justify-center gap-1 text-[11px] text-slate-500">
          <Sparkles className="w-3.5 h-3.5 text-primary" />
          <span>Grounding verified via pgvector cosine distance</span>
        </div>
      </div>
    </aside>
  );
};
