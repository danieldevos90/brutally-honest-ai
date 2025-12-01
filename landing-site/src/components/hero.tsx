"use client";

import Link from "next/link";
import { useTranslations } from "next-intl";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ArrowRight, Play, Shield, Zap, Lock } from "lucide-react";

export function Hero() {
  const t = useTranslations("hero");

  return (
    <section className="relative min-h-screen flex items-center justify-center pt-20 overflow-hidden">
      {/* Background Grid */}
      <div className="absolute inset-0 bg-grid opacity-50" />

      <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20 md:py-32">
        <div className="grid lg:grid-cols-2 gap-12 lg:gap-20 items-center">
          {/* Left Content */}
          <div className="text-center lg:text-left">
            {/* Social Proof Badge */}
            <Badge
              variant="secondary"
              className="mb-6 px-4 py-2 text-sm font-medium bg-secondary border border-border rounded-full inline-flex items-center gap-2"
            >
              <span className="w-2 h-2 bg-[#22c55e] rounded-full animate-pulse-dot" />
              <span>{t("badge")}</span>
            </Badge>

            {/* Main Headline */}
            <h1 className="text-4xl sm:text-5xl md:text-6xl lg:text-7xl font-bold tracking-tight mb-6">
              <span className="block">{t("headline1")}</span>
              <span className="block text-white">{t("headline2")}</span>
            </h1>

            {/* Subheadline */}
            <p className="text-lg md:text-xl text-muted-foreground max-w-xl mx-auto lg:mx-0 mb-8">
              {t.rich("subheadline", {
                say: (chunks) => <em>{chunks}</em>,
                do: (chunks) => <em>{chunks}</em>,
              })}
            </p>

            {/* CTA Buttons */}
            <div className="flex flex-col sm:flex-row gap-4 justify-center lg:justify-start">
              <Button
                asChild
                size="lg"
                className="text-lg px-8 py-6 rounded-full bg-white text-black hover:bg-white/90 font-medium"
              >
                <Link href="https://app.brutallyhonest.io">
                  {t("startTrial")}
                  <ArrowRight className="ml-2 w-5 h-5" />
                </Link>
              </Button>
              <Button
                asChild
                variant="outline"
                size="lg"
                className="text-lg px-8 py-6 rounded-full border-border hover:bg-secondary font-medium"
              >
                <Link href="#how-it-works">
                  <Play className="mr-2 w-5 h-5" />
                  {t("seeHow")}
                </Link>
              </Button>
            </div>

            {/* Trust Indicators */}
            <div className="mt-10 flex flex-wrap items-center gap-6 justify-center lg:justify-start text-sm text-muted-foreground">
              <div className="flex items-center gap-2">
                <Shield className="w-4 h-4 text-[#22c55e]" />
                <span>{t("gdpr")}</span>
              </div>
              <div className="flex items-center gap-2">
                <Zap className="w-4 h-4 text-[#f59e0b]" />
                <span>{t("realtime")}</span>
              </div>
              <div className="flex items-center gap-2">
                <Lock className="w-4 h-4 text-[#3b82f6]" />
                <span>{t("noDataLeaves")}</span>
              </div>
            </div>
          </div>

          {/* Right - Product Preview */}
          <div className="relative lg:pl-8">
            <div className="relative rounded-xl overflow-hidden border border-border bg-card">
              {/* Mock App Interface */}
              <div className="p-3 border-b border-border bg-secondary/50">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-[#ef4444]" />
                  <div className="w-3 h-3 rounded-full bg-[#f59e0b]" />
                  <div className="w-3 h-3 rounded-full bg-[#22c55e]" />
                  <span className="ml-4 text-sm text-muted-foreground">{t("appUrl")}</span>
                </div>
              </div>
              <div className="p-6 space-y-4">
                {/* Live Transcription */}
                <div className="rounded-lg bg-secondary p-4 border border-border">
                  <div className="flex items-center gap-2 mb-3">
                    <span className="w-2 h-2 bg-[#22c55e] rounded-full animate-pulse-dot" />
                    <span className="text-sm font-medium">{t("liveTranscription")}</span>
                  </div>
                  <p className="text-sm text-muted-foreground italic">
                    {t("liveQuote")}
                  </p>
                </div>
                
                {/* Inconsistency Alert */}
                <div className="rounded-lg bg-[rgba(239,68,68,0.1)] border border-[rgba(239,68,68,0.3)] p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-[#ef4444] text-sm font-semibold">{t("inconsistencyDetected")}</span>
                  </div>
                  <p className="text-sm text-muted-foreground">
                    {t("inconsistencyDetail")}
                  </p>
                </div>

                {/* Truth Score */}
                <div className="rounded-lg bg-secondary p-4 border border-border">
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-sm font-medium">{t("truthScore")}</span>
                    <span className="text-2xl font-bold text-white">67%</span>
                  </div>
                  <div className="w-full bg-background rounded-full h-2">
                    <div className="bg-white h-2 rounded-full" style={{ width: '67%' }} />
                  </div>
                </div>
              </div>
            </div>

            {/* Floating Elements */}
            <div className="absolute -top-4 -right-4 bg-[rgba(34,197,94,0.15)] border border-[rgba(34,197,94,0.3)] rounded-lg px-4 py-2 text-sm">
              {t("factVerified")}
            </div>
            <div className="absolute -bottom-4 -left-4 bg-card border border-border rounded-lg px-4 py-2 text-sm">
              {t("claimsAnalyzed")}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
