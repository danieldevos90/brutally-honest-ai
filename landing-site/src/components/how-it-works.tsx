"use client";

import { useTranslations } from "next-intl";
import { Upload, Cpu, BarChart3 } from "lucide-react";

export function HowItWorks() {
  const t = useTranslations("howItWorks");

  const steps = [
    {
      number: "01",
      icon: Upload,
      title: t("step1Title"),
      description: t("step1Desc"),
      iconColor: "text-[#3b82f6]",
      iconBg: "bg-[rgba(59,130,246,0.15)]",
    },
    {
      number: "02",
      icon: Cpu,
      title: t("step2Title"),
      description: t("step2Desc"),
      iconColor: "text-[#f59e0b]",
      iconBg: "bg-[rgba(245,158,11,0.15)]",
    },
    {
      number: "03",
      icon: BarChart3,
      title: t("step3Title"),
      description: t("step3Desc"),
      iconColor: "text-[#22c55e]",
      iconBg: "bg-[rgba(34,197,94,0.15)]",
    },
  ];

  return (
    <section id="how-it-works" className="py-24 bg-secondary/30 relative">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Header */}
        <div className="text-center mb-16">
          <p className="text-sm font-semibold text-muted-foreground uppercase tracking-wider mb-4">
            {t("sectionLabel")}
          </p>
          <h2 className="text-3xl sm:text-4xl md:text-5xl font-bold mb-6">
            {t("headline")}
          </h2>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
            {t("subheadline")}
          </p>
        </div>

        {/* Steps */}
        <div className="grid md:grid-cols-3 gap-8">
          {steps.map((step, index) => {
            const Icon = step.icon;
            return (
              <div key={index} className="relative">
                {/* Connector Line */}
                {index < steps.length - 1 && (
                  <div className="hidden md:block absolute top-16 left-[60%] w-[80%] h-px bg-border" />
                )}
                
                <div className="text-center group">
                  {/* Step Icon */}
                  <div className="inline-flex items-center justify-center w-32 h-32 rounded-2xl bg-card border border-border mb-6 relative group-hover:border-muted-foreground/50 transition-colors">
                    <Icon className={`w-12 h-12 ${step.iconColor}`} />
                    <span className="absolute -top-3 -right-3 w-8 h-8 rounded-full bg-white text-black flex items-center justify-center text-sm font-bold">
                      {step.number}
                    </span>
                  </div>
                  
                  <h3 className="text-xl font-semibold mb-3">{step.title}</h3>
                  <p className="text-muted-foreground">{step.description}</p>
                </div>
              </div>
            );
          })}
        </div>

        {/* Additional Info */}
        <div className="mt-16 text-center">
          <div className="inline-flex items-center gap-4 px-6 py-3 rounded-full bg-card border border-border">
            <span className="flex items-center gap-2 text-sm">
              <span className="w-2 h-2 bg-[#22c55e] rounded-full" />
              {t("worksOffline")}
            </span>
            <span className="w-px h-4 bg-border" />
            <span className="flex items-center gap-2 text-sm">
              <span className="w-2 h-2 bg-[#3b82f6] rounded-full" />
              {t("gpuAccelerated")}
            </span>
            <span className="w-px h-4 bg-border" />
            <span className="flex items-center gap-2 text-sm">
              <span className="w-2 h-2 bg-[#f59e0b] rounded-full" />
              {t("selfHosted")}
            </span>
          </div>
        </div>
      </div>
    </section>
  );
}
