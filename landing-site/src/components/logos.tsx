"use client";

import { useTranslations } from "next-intl";

export function Logos() {
  const t = useTranslations("logos");
  
  const logoKeys = [
    "enterprise",
    "dueDiligence",
    "hr",
    "journalists",
    "researchers",
    "legal",
    "consultancies",
    "investors",
  ] as const;

  return (
    <section className="py-16 border-y border-border bg-secondary/20">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <p className="text-center text-sm text-muted-foreground mb-8">
          {t("headline")}
        </p>
        <div className="flex flex-wrap justify-center items-center gap-x-12 gap-y-6">
          {logoKeys.map((key) => (
            <div
              key={key}
              className="text-muted-foreground/60 font-medium text-sm tracking-wide hover:text-foreground transition-colors"
            >
              {t(key)}
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
