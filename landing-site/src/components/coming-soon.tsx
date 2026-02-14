"use client";

import React, { useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Mail, ArrowRight, CheckCircle, Loader2 } from "lucide-react";
import { useTranslations } from "next-intl";

export function ComingSoon() {
  const t = useTranslations("landing");
  const [email, setEmail] = useState("");
  const [status, setStatus] = useState<"idle" | "loading" | "success" | "error">("idle");
  const [message, setMessage] = useState("");
  const faqRaw = t.raw("faq.items");
  const faqItems: Array<{ q: string; a: string }> = Array.isArray(faqRaw)
    ? (faqRaw as unknown as Array<{ q: string; a: string }>)
    : [];

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email) return;

    setStatus("loading");

    try {
      const response = await fetch("/api/contact", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, type: "waitlist" }),
      });

      if (response.ok) {
        setStatus("success");
        setMessage(t("form.success"));
        setEmail("");
      } else {
        throw new Error("Failed to submit");
      }
    } catch {
      setStatus("error");
      setMessage(t("form.error"));
    }
  };

  return (
    <section className="relative min-h-screen overflow-hidden bg-background text-foreground">
      <div className="pointer-events-none absolute inset-0 bg-grid opacity-70" />
      <div className="pointer-events-none absolute inset-0 bg-gradient-to-b from-transparent via-transparent to-background" />

      <div className="container relative py-16">
        <div className="mx-auto flex w-full max-w-3xl flex-col gap-10">
          {/* Brand */}
          <header className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary text-primary-foreground">
              <span className="text-sm font-semibold" aria-hidden="true">
                BH
              </span>
            </div>
            <span className="text-xl font-semibold tracking-tight">{t("brand")}</span>
          </header>

          {/* Hero */}
          <div className="flex flex-col gap-5">
            <Badge variant="outline" className="w-fit border-border text-muted-foreground tabular-nums">
              {t("badge")}
            </Badge>

            <h1 className="text-balance text-3xl font-semibold tracking-tight sm:text-4xl">
              {t("headline")}
            </h1>

            <p className="max-w-2xl text-pretty text-muted-foreground">
              {t("subhead")}
            </p>
          </div>

          {/* Form */}
          <div className="flex flex-col gap-4">
            <div aria-live="polite">
              {status === "success" ? (
                <div className="flex items-start gap-2 rounded-lg border border-border bg-card px-4 py-3 text-sm">
                  <CheckCircle className="mt-0.5 h-5 w-5 text-green-500" aria-hidden="true" />
                  <p className="text-foreground">{message}</p>
                </div>
              ) : (
                <form onSubmit={handleSubmit} className="flex flex-col gap-2 sm:flex-row">
                  <label className="sr-only" htmlFor="waitlist-email">
                    {t("form.emailLabel")}
                  </label>
                  <Input
                    id="waitlist-email"
                    name="email"
                    type="email"
                    required
                    autoComplete="email"
                    inputMode="email"
                    spellCheck={false}
                    placeholder={t("form.emailPlaceholder")}
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="bg-card text-foreground placeholder:text-muted-foreground"
                  />
                  <Button type="submit" disabled={status === "loading"} className="whitespace-nowrap">
                    {status === "loading" ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin motion-reduce:animate-none" aria-hidden="true" />
                        {t("form.submitting")}
                      </>
                    ) : (
                      t("form.submit")
                    )}
                  </Button>
                </form>
              )}
            </div>

            {status === "error" && (
              <p className="text-sm text-red-400" role="alert">
                {message}
              </p>
            )}

            <p className="text-xs text-muted-foreground">{t("form.privacy")}</p>
          </div>

          {/* CTA links */}
          <div className="flex flex-col gap-3 sm:flex-row">
            <Button asChild variant="secondary">
              <a href="mailto:daniel@altfawesome.nl">
                <Mail className="mr-2 h-4 w-4" aria-hidden="true" />
                {t("cta.contact")}
              </a>
            </Button>
            <Button asChild>
              <a href="https://app.brutallyhonest.io" target="_blank" rel="noopener noreferrer">
                {t("cta.earlyAccess")}
                <ArrowRight className="ml-2 h-4 w-4" aria-hidden="true" />
              </a>
            </Button>
          </div>

          {/* FAQ (AEO/GEO-friendly, answer-first) */}
          <section className="mt-6 rounded-xl border border-border bg-card p-6">
            <h2 className="text-lg font-semibold">{t("faq.title")}</h2>
            <div className="mt-4 grid gap-4">
              {faqItems.slice(0, 6).map((item, idx) => (
                <div key={idx} className="min-w-0">
                  <h3 className="text-sm font-medium text-foreground">{item.q}</h3>
                  <p className="mt-1 text-sm text-muted-foreground">{item.a}</p>
                </div>
              ))}
            </div>
          </section>

          {/* Footer */}
          <footer className="pt-2 text-xs text-muted-foreground">
            © {new Date().getFullYear()}{" "}
            <a href="https://altfawesome.nl" target="_blank" rel="noopener noreferrer" className="underline">
              {t("footer.maker")}
            </a>
            {" "}{t("footer.rights")}
          </footer>
        </div>
      </div>
    </section>
  );
}
