import React, { InputHTMLAttributes, forwardRef } from "react";

export interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  helperText?: string;
  error?: string;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  (
    {
      label,
      helperText,
      error,
      leftIcon,
      rightIcon,
      className = "",
      id,
      ...props
    },
    ref
  ) => {
    const inputId = id || (label ? label.toLowerCase().replace(/\s+/g, "-") : undefined);

    return (
      <div className="w-full flex flex-col gap-1.5">
        {label && (
          <label
            htmlFor={inputId}
            className="text-xs font-semibold text-slate-700 dark:text-slate-300 tracking-tight"
          >
            {label}
          </label>
        )}
        <div className="relative flex items-center w-full">
          {leftIcon && (
            <div className="absolute left-3 flex items-center pointer-events-none text-slate-400 dark:text-slate-500">
              {leftIcon}
            </div>
          )}
          <input
            ref={ref}
            id={inputId}
            className={`w-full h-10 px-3 py-2 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 text-sm rounded-md border ${
              error
                ? "border-error focus:border-error focus:ring-error/20"
                : "border-slate-300 dark:border-slate-700 focus:border-primary focus:ring-primary/20"
            } placeholder:text-slate-400 dark:placeholder:text-slate-500 focus:outline-none focus:ring-3 transition-all ${
              leftIcon ? "pl-9" : ""
            } ${rightIcon ? "pr-9" : ""} disabled:bg-slate-100 dark:disabled:bg-slate-850 disabled:text-slate-500 disabled:cursor-not-allowed ${className}`}
            {...props}
          />
          {rightIcon && (
            <div className="absolute right-3 flex items-center text-slate-400 dark:text-slate-500">
              {rightIcon}
            </div>
          )}
        </div>
        {error ? (
          <p className="text-xs text-error font-medium">{error}</p>
        ) : helperText ? (
          <p className="text-xs text-slate-500 dark:text-slate-400">{helperText}</p>
        ) : null}
      </div>
    );
  }
);

Input.displayName = "Input";
