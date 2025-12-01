"use client";

import { Check } from "lucide-react";
import { useTranslations } from "next-intl";
import { Button } from "@/components/ui/button";
import Link from "next/link";

const Pricing = () => {
  const t = useTranslations("pricing");

  const features = [
    t("features.transcription"),
    t("features.factChecking"),
    t("features.inconsistency"),
    t("features.knowledgeBases"),
    t("features.profileManagement"),
    t("features.api"),
    t("features.support"),
  ];

  return (
    <section id="pricing" className="py-24">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col gap-10 md:flex-row">
          <div className="w-auto md:w-1/2 lg:w-2/3">
            <h2 className="mb-4 text-balance text-4xl font-bold md:text-5xl">
              {t("headline")}
            </h2>
            <p className="text-muted-foreground mb-4 text-lg">
              {t("description")}
            </p>
            <Button variant="default" size="lg" asChild>
              <Link href="mailto:hello@brutallyhonest.io">{t("getQuote")}</Link>
            </Button>
          </div>
          <div className="w-auto bg-muted rounded-md border p-11 md:w-1/2 lg:w-1/3">
            <p className="text-5xl font-bold">
              {t("custom")}<span className="text-lg text-muted-foreground ml-2">{t("pricingLabel")}</span>
            </p>
            <p className="text-muted-foreground text-sm mt-2">
              {t("tailored")}
            </p>
            <ul className="space-y-4 pt-5 font-medium">
              {features.map((feature, index) => (
                <li key={index} className="flex">
                  <Check className="mr-2 text-emerald-500 flex-shrink-0" />
                  <span className="text-muted-foreground">{feature}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    </section>
  );
};

export { Pricing };
