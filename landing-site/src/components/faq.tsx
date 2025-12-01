"use client";

import { useTranslations } from "next-intl";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";

const faqKeys = [
  "privacy",
  "truthExtraction",
  "hardware",
  "consent",
  "accuracy",
  "humanJudgment",
  "export",
  "difference",
] as const;

export function FAQ() {
  const t = useTranslations("faq");

  return (
    <section id="faq" className="py-24 relative">
      <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Header */}
        <div className="text-center mb-16">
          <p className="text-sm font-semibold text-[oklch(0.7_0.15_195)] uppercase tracking-wider mb-4">
            {t("sectionLabel")}
          </p>
          <h2 className="text-3xl sm:text-4xl md:text-5xl font-bold mb-6">
            {t("headline")}
          </h2>
          <p className="text-lg text-muted-foreground">
            {t("subheadline")}
          </p>
        </div>

        {/* FAQ Accordion */}
        <Accordion type="single" collapsible className="space-y-4">
          {faqKeys.map((key, index) => (
            <AccordionItem
              key={key}
              value={`item-${index}`}
              className="bg-card border border-border rounded-xl px-6 data-[state=open]:border-muted-foreground/30"
            >
              <AccordionTrigger className="text-left font-medium hover:no-underline py-6">
                {t(`questions.${key}.q`)}
              </AccordionTrigger>
              <AccordionContent className="text-muted-foreground pb-6">
                {t(`questions.${key}.a`)}
              </AccordionContent>
            </AccordionItem>
          ))}
        </Accordion>
      </div>
    </section>
  );
}
