import React from "react";

type FaqItem = {
  q: string;
  a: string;
};

function safeString(value: unknown): string {
  if (typeof value === "string") return value;
  return "";
}

export function LandingJsonLd(props: {
  locale: string;
  url: string;
  title: string;
  description: string;
  faq: Array<Partial<FaqItem>>;
}) {
  const orgName = "ALT F AWESOME";
  const brandName = "Brutally Honest";

  const faqItems = (props.faq || [])
    .map((i) => ({
      q: safeString(i.q),
      a: safeString(i.a),
    }))
    .filter((i) => i.q && i.a)
    .slice(0, 12); // keep it tight for validators and crawlers

  const graph: Array<Record<string, unknown>> = [
    {
      "@type": "Organization",
      "@id": `${props.url}#org`,
      name: orgName,
      url: props.url,
      brand: {
        "@type": "Brand",
        name: brandName,
      },
    },
    {
      "@type": "WebSite",
      "@id": `${props.url}#website`,
      url: props.url,
      name: brandName,
      inLanguage: props.locale,
    },
    {
      "@type": "WebPage",
      "@id": `${props.url}#webpage`,
      url: props.url,
      name: props.title,
      description: props.description,
      isPartOf: { "@id": `${props.url}#website` },
      about: { "@id": `${props.url}#org` },
      inLanguage: props.locale,
    },
  ];

  if (faqItems.length > 0) {
    graph.push({
      "@type": "FAQPage",
      "@id": `${props.url}#faq`,
      url: props.url,
      inLanguage: props.locale,
      mainEntity: faqItems.map((item) => ({
        "@type": "Question",
        name: item.q,
        acceptedAnswer: {
          "@type": "Answer",
          text: item.a,
        },
      })),
    });
  }

  const jsonLd: Record<string, unknown> = {
    "@context": "https://schema.org",
    "@graph": graph,
  };

  return (
    <script
      type="application/ld+json"
      dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
    />
  );
}

