"use client";

import { useTranslations } from "next-intl";
import { 
  Eye, 
  FileSearch, 
  MessageSquareWarning, 
  ShieldCheck, 
  Users, 
  Zap,
  Brain,
  Target
} from "lucide-react";

// Animated Background Pattern
function GridPattern() {
  return (
    <div className="absolute inset-0 opacity-[0.03]">
      <svg className="w-full h-full" xmlns="http://www.w3.org/2000/svg">
        <defs>
          <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
            <path d="M 40 0 L 0 0 0 40" fill="none" stroke="white" strokeWidth="1"/>
          </pattern>
        </defs>
        <rect width="100%" height="100%" fill="url(#grid)" />
      </svg>
    </div>
  );
}

// Floating Orb Animation
function FloatingOrb({ delay = 0, size = 200, top, left }: { 
  delay?: number; 
  size?: number;
  top: string;
  left: string;
}) {
  return (
    <div 
      className="absolute rounded-full blur-[100px] opacity-[0.03] animate-pulse bg-white"
      style={{
        width: size,
        height: size,
        top,
        left,
        animationDelay: `${delay}s`,
        animationDuration: '4s',
      }}
    />
  );
}

// Icon Wrapper with background
function IconBox({ icon: Icon, color }: { icon: typeof Eye; color: string }) {
  const colorClasses: Record<string, string> = {
    blue: "bg-[rgba(59,130,246,0.15)] text-[#3b82f6]",
    green: "bg-[rgba(34,197,94,0.15)] text-[#22c55e]",
    yellow: "bg-[rgba(245,158,11,0.15)] text-[#f59e0b]",
    red: "bg-[rgba(239,68,68,0.15)] text-[#ef4444]",
  };

  return (
    <div className={`w-12 h-12 rounded-lg flex items-center justify-center ${colorClasses[color]} group-hover:scale-110 transition-transform`}>
      <Icon className="w-6 h-6" />
    </div>
  );
}

// Visual Demo Card - Shows the app in action
function DemoVisual({ t }: { t: ReturnType<typeof useTranslations<"benefits">> }) {
  return (
    <div className="mt-4 space-y-3">
      <div className="flex items-center gap-2 text-sm">
        <span className="w-2 h-2 bg-[#22c55e] rounded-full animate-pulse" />
        <span className="text-muted-foreground">{t("analyzing")}</span>
      </div>
      <div className="space-y-2">
        <div className="flex items-center gap-3">
          <span className="text-xs text-muted-foreground w-20">{t("consistency")}</span>
          <div className="flex-1 h-2 bg-secondary rounded-full overflow-hidden">
            <div className="h-full bg-[#22c55e] rounded-full" style={{ width: '78%' }} />
          </div>
          <span className="text-xs font-medium">78%</span>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-xs text-muted-foreground w-20">{t("confidence")}</span>
          <div className="flex-1 h-2 bg-secondary rounded-full overflow-hidden">
            <div className="h-full bg-[#3b82f6] rounded-full" style={{ width: '92%' }} />
          </div>
          <span className="text-xs font-medium">92%</span>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-xs text-muted-foreground w-20">{t("claims")}</span>
          <div className="flex-1 h-2 bg-secondary rounded-full overflow-hidden">
            <div className="h-full bg-[#f59e0b] rounded-full" style={{ width: '45%' }} />
          </div>
          <span className="text-xs font-medium">12</span>
        </div>
      </div>
    </div>
  );
}

// Live waveform visual for Real-Time card
function WaveformVisual() {
  return (
    <div className="mt-6 flex items-end justify-center gap-1 h-24">
      {[40, 65, 45, 80, 55, 70, 35, 90, 50, 75, 45, 85, 60].map((h, i) => (
        <div
          key={i}
          className="w-2 bg-[#f59e0b] rounded-full animate-pulse"
          style={{ 
            height: `${h}%`,
            animationDelay: `${i * 0.1}s`,
            animationDuration: '1s'
          }}
        />
      ))}
    </div>
  );
}

export function Benefits() {
  const t = useTranslations("benefits");

  return (
    <section id="benefits" className="py-24 relative overflow-hidden">
      {/* Background Effects */}
      <GridPattern />
      <FloatingOrb delay={0} size={400} top="10%" left="10%" />
      <FloatingOrb delay={2} size={300} top="60%" left="70%" />
      <FloatingOrb delay={1} size={250} top="80%" left="20%" />
      
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative">
        {/* Section Header */}
        <div className="text-center mb-16">
          <p className="text-sm font-semibold text-muted-foreground uppercase tracking-wider mb-4">
            {t("sectionLabel")}
          </p>
          <h2 className="text-3xl sm:text-4xl md:text-5xl font-bold mb-6">
            {t("headline")} <span className="text-white">{t("headlineHighlight")}</span>
          </h2>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
            {t("subheadline")}
          </p>
        </div>

        {/* Bento Grid - Fixed 4x3 layout */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          
          {/* Row 1-2: Large (2x2) + Tall Real-Time (1x3) + Small stack */}
          
          {/* Large Card - See What Others Miss (2x2) */}
          <div className="md:col-span-2 md:row-span-2 relative overflow-hidden rounded-xl bg-card border border-border p-6 transition-all duration-300 hover:border-muted-foreground/50 hover:-translate-y-1 group">
            <IconBox icon={Eye} color="blue" />
            <h3 className="text-2xl font-semibold mt-4 mb-2">{t("seeWhatOthersMiss")}</h3>
            <p className="text-muted-foreground">
              {t("seeWhatOthersMissDesc")}
            </p>
            <DemoVisual t={t} />
          </div>

          {/* Real-Time Card (1x3) - Tall */}
          <div className="md:col-span-1 md:row-span-3 relative overflow-hidden rounded-xl bg-card border border-border p-6 transition-all duration-300 hover:border-muted-foreground/50 hover:-translate-y-1 group">
            <IconBox icon={Zap} color="yellow" />
            <h3 className="text-xl font-semibold mt-4 mb-2">{t("realTimeAnalysis")}</h3>
            <p className="text-sm text-muted-foreground">
              {t("realTimeAnalysisDesc")}
            </p>
            <WaveformVisual />
            <div className="mt-4 space-y-2">
              <div className="flex items-center gap-2">
                <span className="w-2 h-2 bg-[#22c55e] rounded-full animate-pulse" />
                <span className="text-xs text-muted-foreground">{t("processingAudio")}</span>
              </div>
              <div className="text-xs text-muted-foreground bg-secondary/50 p-2 rounded">
                {t("realTimeQuote")}
              </div>
              <div className="text-xs text-[#f59e0b] bg-[rgba(245,158,11,0.1)] p-2 rounded border border-[rgba(245,158,11,0.2)]">
                {t("realTimeWarning")}
              </div>
            </div>
          </div>

          {/* Say vs Do (1x1) */}
          <div className="md:col-span-1 md:row-span-1 relative overflow-hidden rounded-xl bg-card border border-border p-6 transition-all duration-300 hover:border-muted-foreground/50 hover:-translate-y-1 group">
            <IconBox icon={MessageSquareWarning} color="yellow" />
            <h3 className="text-lg font-semibold mt-3 mb-1">{t("sayVsDo")}</h3>
            <p className="text-sm text-muted-foreground">
              {t("sayVsDoDesc")}
            </p>
          </div>

          {/* Fact Check (1x1) */}
          <div className="md:col-span-1 md:row-span-1 relative overflow-hidden rounded-xl bg-card border border-border p-6 transition-all duration-300 hover:border-muted-foreground/50 hover:-translate-y-1 group">
            <IconBox icon={FileSearch} color="red" />
            <h3 className="text-lg font-semibold mt-3 mb-1">{t("factCheck")}</h3>
            <p className="text-sm text-muted-foreground">
              {t("factCheckDesc")}
            </p>
          </div>

          {/* Row 3: Mission Alignment (2x1) + Extract Signals (1x1) + (Real-Time continues) */}
          
          {/* Mission Alignment (2x1) */}
          <div className="md:col-span-2 md:row-span-1 relative overflow-hidden rounded-xl bg-card border border-border p-6 transition-all duration-300 hover:border-muted-foreground/50 hover:-translate-y-1 group">
            <div className="flex items-start gap-4">
              <IconBox icon={Target} color="yellow" />
              <div className="flex-1">
                <h3 className="text-lg font-semibold mb-1">{t("missionAlignment")}</h3>
                <p className="text-sm text-muted-foreground">
                  {t("missionAlignmentDesc")}
                </p>
              </div>
              <div className="hidden md:grid grid-cols-2 gap-2">
                <div className="bg-secondary/50 rounded-lg px-3 py-2 text-center">
                  <div className="text-lg font-bold">12</div>
                  <div className="text-[10px] text-muted-foreground">{t("gaps")}</div>
                </div>
                <div className="bg-secondary/50 rounded-lg px-3 py-2 text-center">
                  <div className="text-lg font-bold text-[#22c55e]">3</div>
                  <div className="text-[10px] text-muted-foreground">{t("verified")}</div>
                </div>
              </div>
            </div>
          </div>

          {/* Extract Signals (1x1) */}
          <div className="md:col-span-1 md:row-span-1 relative overflow-hidden rounded-xl bg-card border border-border p-6 transition-all duration-300 hover:border-muted-foreground/50 hover:-translate-y-1 group">
            <IconBox icon={Brain} color="green" />
            <h3 className="text-lg font-semibold mt-3 mb-1">{t("extractSignals")}</h3>
            <p className="text-sm text-muted-foreground">
              {t("extractSignalsDesc")}
            </p>
          </div>

          {/* Row 4: Privacy (2x1) + Profiles (1x1) + Empty (or additional) */}
          
          {/* Privacy (2x1) */}
          <div className="md:col-span-2 md:row-span-1 relative overflow-hidden rounded-xl bg-[rgba(34,197,94,0.05)] border border-border p-6 transition-all duration-300 hover:border-muted-foreground/50 hover:-translate-y-1 group">
            <div className="flex items-center gap-4">
              <IconBox icon={ShieldCheck} color="green" />
              <div className="flex-1">
                <h3 className="text-lg font-semibold mb-1">{t("privacyLocal")}</h3>
                <p className="text-sm text-muted-foreground">
                  {t("privacyLocalDesc")}
                </p>
              </div>
              <div className="hidden md:flex items-center gap-2 px-3 py-1.5 bg-[rgba(34,197,94,0.15)] rounded-full">
                <span className="w-2 h-2 bg-[#22c55e] rounded-full" />
                <span className="text-xs font-medium text-[#22c55e]">{t("secure")}</span>
              </div>
            </div>
          </div>

          {/* Profiles (1x1) */}
          <div className="md:col-span-1 md:row-span-1 relative overflow-hidden rounded-xl bg-card border border-border p-6 transition-all duration-300 hover:border-muted-foreground/50 hover:-translate-y-1 group">
            <IconBox icon={Users} color="blue" />
            <h3 className="text-lg font-semibold mt-3 mb-1">{t("truthProfiles")}</h3>
            <p className="text-sm text-muted-foreground">
              {t("truthProfilesDesc")}
            </p>
          </div>

          {/* Final small card to fill the grid */}
          <div className="md:col-span-1 md:row-span-1 relative overflow-hidden rounded-xl bg-card border border-border p-6 transition-all duration-300 hover:border-muted-foreground/50 hover:-translate-y-1 group flex flex-col items-center justify-center text-center">
            <div className="text-4xl font-bold mb-2">{t("poweredByAI")}</div>
            <p className="text-sm text-muted-foreground">
              {t("poweredByAIDesc")}
            </p>
          </div>

        </div>
      </div>
    </section>
  );
}
