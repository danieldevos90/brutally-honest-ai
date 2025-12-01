"use client";

import Link from "next/link";
import { useTranslations } from "next-intl";
import { Button } from "@/components/ui/button";
import { ArrowRight } from "lucide-react";

export function CTA() {
  const t = useTranslations("cta");

  return (
    <section className="py-24 relative">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 relative">
        <div className="text-center rounded-2xl p-12 md:p-16 bg-card border border-border">
          <h2 className="text-3xl sm:text-4xl md:text-5xl font-bold mb-6">
            {t("headline")} <span className="text-white">{t("headlineHighlight")}</span>
          </h2>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto mb-10">
            {t("subheadline")}
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Button
              asChild
              size="lg"
              className="text-lg px-10 py-6 rounded-full bg-white text-black hover:bg-white/90 font-medium"
            >
              <Link href="https://app.brutallyhonest.io">
                {t("launchApp")}
                <ArrowRight className="ml-2 w-5 h-5" />
              </Link>
            </Button>
            <Button
              asChild
              variant="outline"
              size="lg"
              className="text-lg px-10 py-6 rounded-full border-border hover:bg-secondary font-medium"
            >
              <Link href="https://github.com/altfawesome/brutally-honest-ai">
                {t("viewGithub")}
              </Link>
            </Button>
          </div>
          
          <p className="mt-8 text-sm text-muted-foreground">
            {t("noCC")}
          </p>
        </div>
      </div>
    </section>
  );
}
