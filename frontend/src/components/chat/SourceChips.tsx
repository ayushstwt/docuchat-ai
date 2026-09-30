import React from "react";
import { FileText, ArrowUpRight } from "lucide-react";
import { Source } from "../../api/types";

export interface SourceChipsProps {
  sources?: Source[];
  onSelectSource?: (source: Source) => void;
  className?: string;
}

export const SourceChips: React.FC<SourceChipsProps> = ({
  sources,
  onSelectSource,
  className = "",
}) => {
  if (!sources || sources.length === 0) return null;

  return (
    <div className={`flex flex-wrap items-center gap-1.5 pt-2 ${className}`}>
      {sources.map((src) => (
        <button
          key={src.index}
          type="button"
          onClick={() => onSelectSource?.(src)}
          className="group inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-slate-50 dark:bg-slate-800 hover:bg-indigo-50 dark:hover:bg-indigo-950/60 border border-slate-200 dark:border-slate-700 hover:border-indigo-300 dark:hover:border-indigo-800 text-slate-700 dark:text-slate-200 hover:text-primary dark:hover:text-indigo-300 text-xs font-mono transition-all cursor-pointer shadow-xs"
        >
          <FileText className="w-3.5 h-3.5 text-primary/80 group-hover:text-primary" />
          <span className="font-bold text-primary dark:text-indigo-400">[{src.index}]</span>
          <span className="truncate max-w-[130px]">{src.documentTitle}</span>
          <span className="text-slate-400 dark:text-slate-500 text-[10px]">p.{src.pageNumber}</span>
          <ArrowUpRight className="w-3 h-3 text-slate-400 group-hover:text-primary group-hover:translate-x-0.5 transition-transform" />
        </button>
      ))}
    </div>
  );
};
