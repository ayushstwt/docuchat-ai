import React from "react";

export interface SkeletonProps extends React.HTMLAttributes<HTMLDivElement> {
  className?: string;
}

export const Skeleton: React.FC<SkeletonProps> = ({ className = "", ...props }) => {
  return (
    <div
      className={`animate-pulse rounded-md bg-slate-200 dark:bg-slate-800 ${className}`}
      {...props}
    />
  );
};

export const SkeletonText: React.FC<{
  lines?: number;
  className?: string;
  lastLineWidth?: string;
}> = ({ lines = 3, className = "", lastLineWidth = "w-3/4" }) => {
  return (
    <div className={`space-y-2 ${className}`}>
      {Array.from({ length: lines }).map((_, idx) => (
        <Skeleton
          key={idx}
          className={`h-4 ${idx === lines - 1 ? lastLineWidth : "w-full"}`}
        />
      ))}
    </div>
  );
};

export const SkeletonCard: React.FC<{ className?: string }> = ({
  className = "",
}) => {
  return (
    <div
      className={`p-5 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-xs space-y-3 ${className}`}
    >
      <div className="flex items-center justify-between">
        <Skeleton className="h-3 w-24" />
        <Skeleton className="h-8 w-8 rounded-lg" />
      </div>
      <Skeleton className="h-7 w-16" />
      <Skeleton className="h-3 w-32" />
    </div>
  );
};

export const SkeletonTable: React.FC<{
  rows?: number;
  cols?: number;
  className?: string;
}> = ({ rows = 5, cols = 4, className = "" }) => {
  return (
    <div
      className={`w-full overflow-hidden border border-slate-200 dark:border-slate-800 rounded-xl bg-white dark:bg-slate-900 shadow-xs ${className}`}
    >
      <div className="p-4 border-b border-slate-100 dark:border-slate-800 flex items-center justify-between">
        <Skeleton className="h-4 w-32" />
        <Skeleton className="h-8 w-24 rounded-md" />
      </div>
      <div className="divide-y divide-slate-100 dark:divide-slate-850">
        {Array.from({ length: rows }).map((_, rIdx) => (
          <div key={rIdx} className="p-4 flex items-center justify-between gap-4">
            <div className="flex items-center gap-3 flex-1">
              <Skeleton className="w-8 h-8 rounded-lg shrink-0" />
              <div className="space-y-1.5 flex-1 max-w-sm">
                <Skeleton className="h-3.5 w-full" />
                <Skeleton className="h-2.5 w-2/3" />
              </div>
            </div>
            {Array.from({ length: cols - 1 }).map((_, cIdx) => (
              <Skeleton
                key={cIdx}
                className="h-4 w-20 hidden sm:block shrink-0"
              />
            ))}
          </div>
        ))}
      </div>
    </div>
  );
};

export const SkeletonChatBubble: React.FC<{ isUser?: boolean }> = ({
  isUser = false,
}) => {
  if (isUser) {
    return (
      <div className="flex flex-col items-end gap-1.5 max-w-lg ml-auto animate-pulse">
        <div className="h-12 w-64 rounded-2xl rounded-tr-xs bg-indigo-200 dark:bg-indigo-900/60" />
        <div className="h-2 w-12 bg-slate-200 dark:bg-slate-800 rounded" />
      </div>
    );
  }

  return (
    <div className="flex items-start gap-3 max-w-2xl animate-pulse">
      <Skeleton className="w-8 h-8 rounded-lg shrink-0 mt-0.5" />
      <div className="flex-1 space-y-2 bg-white dark:bg-slate-900 rounded-2xl rounded-tl-xs p-5 border border-slate-200 dark:border-slate-800">
        <Skeleton className="h-4 w-5/6" />
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-4 w-3/4" />
        <div className="pt-2 flex gap-2">
          <Skeleton className="h-6 w-24 rounded-full" />
          <Skeleton className="h-6 w-28 rounded-full" />
        </div>
      </div>
    </div>
  );
};
