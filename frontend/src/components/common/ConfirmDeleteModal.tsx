import React from "react";
import { AlertTriangle, Trash2, X } from "lucide-react";
import { Button } from "../ui/Button";

export interface ConfirmDeleteModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title?: string;
  itemName?: string;
  itemType?: "document" | "conversation" | "data";
  description?: string;
  isDeleting?: boolean;
}

export const ConfirmDeleteModal: React.FC<ConfirmDeleteModalProps> = ({
  isOpen,
  onClose,
  onConfirm,
  title,
  itemName,
  itemType = "data",
  description,
  isDeleting = false,
}) => {
  if (!isOpen) return null;

  const modalTitle = title || `Delete ${itemType.charAt(0).toUpperCase() + itemType.slice(1)}`;

  const defaultDescription =
    itemType === "document"
      ? "This will permanently remove the PDF file and all of its vectorized semantic chunks. This action cannot be undone."
      : itemType === "conversation"
      ? "This will permanently delete this conversation and all of its message history. This action cannot be undone."
      : "This action cannot be undone and will permanently remove this data.";

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-slate-900/60 backdrop-blur-xs transition-opacity animate-in fade-in"
        onClick={!isDeleting ? onClose : undefined}
      />

      {/* Modal Dialog */}
      <div className="flex min-h-full items-center justify-center p-4 text-center">
        <div
          className="relative w-full max-w-md transform overflow-hidden rounded-2xl bg-white dark:bg-slate-900 text-left shadow-2xl transition-all border border-slate-200 dark:border-slate-800 animate-in zoom-in-95 duration-150 p-6"
          onClick={(e) => e.stopPropagation()}
        >
          {/* Close button */}
          <button
            type="button"
            onClick={onClose}
            disabled={isDeleting}
            className="absolute top-4 right-4 p-1.5 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-colors disabled:opacity-50"
          >
            <X className="w-4 h-4" />
          </button>

          <div className="flex items-start gap-4">
            {/* Warning Icon Badge */}
            <div className="w-11 h-11 rounded-xl bg-rose-50 dark:bg-rose-950/60 border border-rose-200 dark:border-rose-900/80 flex items-center justify-center text-rose-600 dark:text-rose-400 shrink-0 shadow-xs">
              <AlertTriangle className="w-5 h-5" />
            </div>

            <div className="flex-1 min-w-0 pr-4">
              <h3 className="text-base font-bold text-slate-900 dark:text-slate-100 tracking-tight">
                {modalTitle}
              </h3>

              {itemName && (
                <div className="mt-2 p-2.5 rounded-lg bg-slate-50 dark:bg-slate-800/70 border border-slate-200/80 dark:border-slate-700/80 flex items-center gap-2">
                  <Trash2 className="w-4 h-4 text-slate-400 dark:text-slate-500 shrink-0" />
                  <span className="text-xs font-semibold text-slate-800 dark:text-slate-200 truncate">
                    {itemName}
                  </span>
                </div>
              )}

              <p className="mt-2.5 text-xs text-slate-500 dark:text-slate-400 leading-relaxed">
                {description || defaultDescription}
              </p>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="mt-6 flex items-center justify-end gap-3 pt-4 border-t border-slate-100 dark:border-slate-800">
            <Button
              type="button"
              variant="secondary"
              size="md"
              onClick={onClose}
              disabled={isDeleting}
            >
              Cancel
            </Button>
            <Button
              type="button"
              variant="danger"
              size="md"
              onClick={onConfirm}
              isLoading={isDeleting}
              leftIcon={<Trash2 className="w-4 h-4" />}
            >
              {isDeleting ? "Deleting..." : "Delete Permanently"}
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};
