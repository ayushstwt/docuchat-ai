import React, { useState } from "react";
import { Link, useNavigate, useLocation } from "react-router-dom";
import {
  Bot,
  Zap,
  CheckCircle,
  ShieldCheck,
  FileText,
  ArrowRight,
  AlertCircle,
} from "lucide-react";
import { Button } from "../components/ui/Button";
import { Input } from "../components/ui/Input";
import { authApi } from "../api/auth";
import { useAuthStore } from "../store/authStore";
import { ApiError } from "../api/client";

export const LoginPage: React.FC = () => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

  const { setAuth } = useAuthStore();
  const navigate = useNavigate();
  const location = useLocation();
  const from = (location.state as { from?: { pathname?: string } })?.from?.pathname || "/documents";

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);
    setFieldErrors({});

    const newFieldErrors: Record<string, string> = {};
    if (!email.trim()) newFieldErrors.email = "Email is required";
    if (!password) newFieldErrors.password = "Password is required";

    if (Object.keys(newFieldErrors).length > 0) {
      setFieldErrors(newFieldErrors);
      return;
    }

    try {
      setIsLoading(true);
      const tokenResp = await authApi.login({
        email: email.trim(),
        password,
      });
      setAuth(tokenResp);
      navigate(from, { replace: true });
    } catch (err: unknown) {
      if (err instanceof ApiError) {
        setErrorMsg(err.message);
        if (err.fieldErrors) {
          const map: Record<string, string> = {};
          err.fieldErrors.forEach((fe) => {
            if (fe.field) {
              map[fe.field] = fe.message;
            }
          });
          setFieldErrors(map);
        }
      } else {
        setErrorMsg("Failed to sign in. Please check your credentials.");
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen bg-slate-50 text-slate-900">
      {/* Left Column: Brand Hero */}
      <div className="relative hidden lg:flex flex-1 flex-col justify-between p-12 bg-primary text-white overflow-hidden">
        {/* Ambient Backdrops */}
        <div className="absolute -top-32 -left-32 w-96 h-96 rounded-full bg-indigo-300 opacity-20 blur-3xl pointer-events-none" />
        <div className="absolute bottom-0 right-0 w-96 h-96 rounded-full bg-indigo-900 opacity-40 blur-2xl pointer-events-none" />

        {/* Top: Header */}
        <div className="relative z-10 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-white/10 backdrop-blur-md p-2 flex items-center justify-center border border-white/20 shadow-sm">
              <Bot className="w-6 h-6 text-white" />
            </div>
            <div>
              <div className="font-bold text-lg leading-tight tracking-tight">
                DocuChat AI
              </div>
              <div className="text-[11px] text-indigo-200 uppercase tracking-wider font-mono">
                Enterprise Research
              </div>
            </div>
          </div>
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/10 backdrop-blur-md text-xs font-medium border border-white/10">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            <span>v2.4 Ready</span>
          </div>
        </div>

        {/* Middle: Value Pillars */}
        <div className="relative z-10 max-w-lg my-12 flex flex-col gap-8">
          <div>
            <span className="inline-block px-3 py-1 rounded-full text-xs font-medium bg-indigo-500/30 text-indigo-100 border border-indigo-400/30 mb-4">
              Next-Gen Document Intelligence
            </span>
            <h1 className="text-4xl font-bold tracking-tight leading-tight">
              Chat with your PDFs
            </h1>
            <p className="mt-3 text-indigo-100 text-sm leading-relaxed">
              Upload dense technical, financial, or legal files. Query freely and
              receive grounded answers verified to the exact source page.
            </p>
          </div>

          <div className="space-y-4">
            <div className="flex items-start gap-3.5">
              <div className="w-9 h-9 rounded-lg bg-white/10 flex items-center justify-center shrink-0 border border-white/10">
                <Zap className="w-4 h-4 text-white" />
              </div>
              <div>
                <h4 className="text-sm font-semibold">Streaming answers</h4>
                <p className="text-xs text-indigo-200 mt-0.5 leading-normal">
                  Real-time conversational responses powered by Azure OpenAI with near-zero latency.
                </p>
              </div>
            </div>

            <div className="flex items-start gap-3.5">
              <div className="w-9 h-9 rounded-lg bg-white/10 flex items-center justify-center shrink-0 border border-white/10">
                <CheckCircle className="w-4 h-4 text-white" />
              </div>
              <div>
                <h4 className="text-sm font-semibold">Page citations</h4>
                <p className="text-xs text-indigo-200 mt-0.5 leading-normal">
                  Direct page references and verified snippets for reliable audit trails.
                </p>
              </div>
            </div>

            <div className="flex items-start gap-3.5">
              <div className="w-9 h-9 rounded-lg bg-white/10 flex items-center justify-center shrink-0 border border-white/10">
                <ShieldCheck className="w-4 h-4 text-white" />
              </div>
              <div>
                <h4 className="text-sm font-semibold">Private and secure</h4>
                <p className="text-xs text-indigo-200 mt-0.5 leading-normal">
                  Strict workspace tenant isolation. Your confidential proprietary data is fully protected.
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Bottom: Sample Product Preview */}
        <div className="relative z-10 bg-white/10 backdrop-blur-md rounded-xl p-4 border border-white/15 shadow-xl">
          <div className="flex items-center justify-between pb-2.5 mb-2.5 border-b border-white/10 text-xs">
            <div className="flex items-center gap-2">
              <FileText className="w-4 h-4 text-indigo-300" />
              <span className="font-mono text-white truncate max-w-[220px]">
                Annual_Financial_Report_2025.pdf
              </span>
            </div>
            <span className="px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 text-[11px] font-mono">
              Indexed · 48 pgs
            </span>
          </div>
          <div className="bg-white rounded-lg p-3 text-slate-800 shadow-sm text-xs space-y-2">
            <div className="flex items-center gap-1.5 font-semibold text-primary text-[11px]">
              <Bot className="w-3.5 h-3.5" />
              DocuChat Engine
            </div>
            <p className="text-slate-600 leading-snug">
              Total subscription ARR reached $42.8M, representing a 28% YoY expansion with net retention holding at 118%.
            </p>
            <div className="flex items-center gap-2 pt-1 font-mono text-[11px]">
              <span className="px-2 py-0.5 rounded-full bg-indigo-50 border border-indigo-200 text-primary font-medium">
                [p. 14]
              </span>
              <span className="text-slate-400">Score: 94.2%</span>
            </div>
          </div>
        </div>
      </div>

      {/* Right Column: Sign In Form */}
      <div className="flex-1 flex flex-col justify-center items-center p-6 sm:p-12 lg:p-16">
        <div className="w-full max-w-md">
          {/* Mobile Brand Header */}
          <div className="flex items-center gap-2.5 mb-8 lg:hidden">
            <div className="w-9 h-9 rounded-lg bg-primary flex items-center justify-center text-white">
              <Bot className="w-5 h-5" />
            </div>
            <span className="font-bold text-slate-900 text-lg">DocuChat AI</span>
          </div>

          <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-8 sm:p-10">
            <div className="mb-6">
              <h2 className="text-2xl font-bold tracking-tight text-slate-900">
                Welcome back
              </h2>
              <p className="text-sm text-slate-500 mt-1">
                Sign in to access your documents and chat history.
              </p>
            </div>

            {errorMsg && (
              <div className="mb-5 p-3.5 rounded-lg bg-rose-50 border border-rose-200 flex items-start gap-2.5 text-rose-700 text-sm">
                <AlertCircle className="w-5 h-5 shrink-0 mt-0.5 text-rose-600" />
                <div className="flex-1 text-xs font-medium">{errorMsg}</div>
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-4">
              <Input
                label="Email address"
                type="email"
                placeholder="name@company.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                error={fieldErrors.email}
                autoComplete="email"
                required
              />

              <Input
                label="Password"
                type="password"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                error={fieldErrors.password}
                autoComplete="current-password"
                required
              />

              <Button
                type="submit"
                variant="primary"
                size="lg"
                className="w-full mt-2"
                isLoading={isLoading}
                rightIcon={<ArrowRight className="w-4 h-4" />}
              >
                Sign in
              </Button>
            </form>

            <div className="mt-6 pt-6 border-t border-slate-100 text-center">
              <p className="text-xs text-slate-500">
                Don&apos;t have an account?{" "}
                <Link
                  to="/register"
                  className="font-semibold text-primary hover:text-primary-hover underline underline-offset-4"
                >
                  Create an account
                </Link>
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
