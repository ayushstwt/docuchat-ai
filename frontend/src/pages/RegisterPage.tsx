import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  Bot,
  Zap,
  CheckCircle,
  ShieldCheck,
  ArrowRight,
  AlertCircle,
} from "lucide-react";
import { Button } from "../components/ui/Button";
import { Input } from "../components/ui/Input";
import { authApi } from "../api/auth";
import { useAuthStore } from "../store/authStore";
import { useToast } from "../components/ui/Toast";
import { ApiError } from "../api/client";

export const RegisterPage: React.FC = () => {
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

  const { setAuth } = useAuthStore();
  const navigate = useNavigate();
  const toast = useToast();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);
    setFieldErrors({});

    const newFieldErrors: Record<string, string> = {};
    if (!fullName.trim()) newFieldErrors.fullName = "Full name is required";
    if (!email.trim()) newFieldErrors.email = "Email is required";
    if (!password) newFieldErrors.password = "Password is required";
    if (password.length < 8) {
      newFieldErrors.password = "Password must be at least 8 characters long";
    }
    if (password !== confirmPassword) {
      newFieldErrors.confirmPassword = "Passwords do not match";
    }

    if (Object.keys(newFieldErrors).length > 0) {
      setFieldErrors(newFieldErrors);
      return;
    }

    try {
      setIsLoading(true);
      await authApi.register({
        fullName: fullName.trim(),
        email: email.trim(),
        password,
      });

      // Auto login after successful registration
      const tokenResp = await authApi.login({
        email: email.trim(),
        password,
      });

      setAuth(tokenResp);
      toast.success("Account created successfully. Welcome to DocuChat!");
      navigate("/documents", { replace: true });
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
        setErrorMsg("Registration failed. Please try again.");
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col lg:flex-row bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100 transition-colors">
      {/* Left Column: Brand & Hero Value Proposition */}
      <div className="hidden lg:flex lg:w-1/2 bg-gradient-to-br from-primary-900 via-primary-800 to-indigo-950 text-white p-12 xl:p-16 flex-col justify-between relative overflow-hidden">
        {/* Ambient blobs */}
        <div className="absolute top-0 right-0 -mr-20 -mt-20 w-96 h-96 rounded-full bg-primary-500/20 blur-3xl pointer-events-none" />
        <div className="absolute bottom-0 left-0 -ml-20 -mb-20 w-96 h-96 rounded-full bg-indigo-500/15 blur-3xl pointer-events-none" />

        {/* Top: Brand Header */}
        <div className="relative z-10 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-white/10 backdrop-blur-md flex items-center justify-center text-white border border-white/20 shadow-md">
              <Bot className="w-6 h-6" />
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
              Get Started with DocuChat
            </span>
            <h1 className="text-4xl font-bold tracking-tight leading-tight">
              Create your account
            </h1>
            <p className="mt-3 text-indigo-100 text-sm leading-relaxed">
              Unlock vector retrieval and AI chat for your legal, research, and technical documents.
            </p>
          </div>

          <div className="space-y-4">
            <div className="flex items-start gap-3.5">
              <div className="w-9 h-9 rounded-lg bg-white/10 flex items-center justify-center shrink-0 border border-white/10">
                <Zap className="w-4 h-4 text-white" />
              </div>
              <div>
                <h4 className="text-sm font-semibold">Fast PDF chunking & embeddings</h4>
                <p className="text-xs text-indigo-200 mt-0.5 leading-normal">
                  Automatic text extraction and pgvector indexing with Azure OpenAI.
                </p>
              </div>
            </div>

            <div className="flex items-start gap-3.5">
              <div className="w-9 h-9 rounded-lg bg-white/10 flex items-center justify-center shrink-0 border border-white/10">
                <CheckCircle className="w-4 h-4 text-white" />
              </div>
              <div>
                <h4 className="text-sm font-semibold">Accurate page citations</h4>
                <p className="text-xs text-indigo-200 mt-0.5 leading-normal">
                  Verify answers against source documents with page-numbered references.
                </p>
              </div>
            </div>

            <div className="flex items-start gap-3.5">
              <div className="w-9 h-9 rounded-lg bg-white/10 flex items-center justify-center shrink-0 border border-white/10">
                <ShieldCheck className="w-4 h-4 text-white" />
              </div>
              <div>
                <h4 className="text-sm font-semibold">User isolation</h4>
                <p className="text-xs text-indigo-200 mt-0.5 leading-normal">
                  Every user’s documents and chat histories are strictly isolated.
                </p>
              </div>
            </div>
          </div>
        </div>

        <div className="relative z-10 text-xs text-indigo-200">
          DocuChat AI · Secure Document Intelligence Platform
        </div>
      </div>

      {/* Right Column: Register Form */}
      <div className="flex-1 flex flex-col justify-center items-center p-6 sm:p-12 lg:p-16">
        <div className="w-full max-w-md">
          {/* Mobile Brand Header */}
          <div className="flex items-center gap-2.5 mb-8 lg:hidden">
            <div className="w-9 h-9 rounded-lg bg-primary flex items-center justify-center text-white">
              <Bot className="w-5 h-5" />
            </div>
            <span className="font-bold text-slate-900 dark:text-slate-100 text-lg">DocuChat AI</span>
          </div>

          <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm p-8 sm:p-10 transition-colors">
            <div className="mb-6">
              <h2 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-100">
                Create an account
              </h2>
              <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
                Enter your details to start chatting with your PDFs.
              </p>
            </div>

            {errorMsg && (
              <div className="mb-5 p-3.5 rounded-lg bg-rose-50 dark:bg-rose-950/50 border border-rose-200 dark:border-rose-900 flex items-start gap-2.5 text-rose-700 dark:text-rose-300 text-sm">
                <AlertCircle className="w-5 h-5 shrink-0 mt-0.5 text-rose-600 dark:text-rose-400" />
                <div className="flex-1 text-xs font-medium">{errorMsg}</div>
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-4">
              <Input
                label="Full name"
                type="text"
                placeholder="Sarah Jenkins"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                error={fieldErrors.fullName}
                autoComplete="name"
                required
              />

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
                placeholder="Must include letters and numbers"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                error={fieldErrors.password}
                autoComplete="new-password"
                required
              />

              <Input
                label="Confirm password"
                type="password"
                placeholder="Repeat password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                error={fieldErrors.confirmPassword}
                autoComplete="new-password"
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
                Create account
              </Button>
            </form>

            <div className="mt-6 pt-6 border-t border-slate-100 dark:border-slate-800 text-center">
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Already have an account?{" "}
                <Link
                  to="/login"
                  className="font-semibold text-primary dark:text-indigo-400 hover:text-primary-hover underline underline-offset-4"
                >
                  Sign in
                </Link>
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
