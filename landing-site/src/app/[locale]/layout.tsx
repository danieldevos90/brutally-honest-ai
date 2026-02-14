import type { Metadata } from "next";
import { Inter } from "next/font/google";
import { NextIntlClientProvider } from "next-intl";
import { getMessages, setRequestLocale } from "next-intl/server";
import { notFound } from "next/navigation";
import { locales, type Locale } from "@/i18n/config";
import "../globals.css";
import { getSiteUrl } from "@/lib/site";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
});

export function generateStaticParams() {
  return locales.map((locale) => ({ locale }));
}

type Props = {
  children: React.ReactNode;
  params: Promise<{ locale: string }>;
};

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { locale } = await params;
  setRequestLocale(locale);

  const messages = await getMessages();
  const t = messages.metadata as Record<string, string>;
  const siteUrl = getSiteUrl();
  const localePath = `/${locale}`;
  const canonical = new URL(localePath, siteUrl);

  return {
    metadataBase: new URL(siteUrl),
    title: {
      default: t.title,
      template: `%s | Brutally Honest`,
    },
    description: t.description,
    applicationName: "Brutally Honest",
    authors: [{ name: "ALT F AWESOME", url: "https://altfawesome.nl" }],
    creator: "ALT F AWESOME",
    keywords: [
      "real-time fact checking",
      "AI fact checking",
      "meeting intelligence",
      "interview analysis",
      "negotiation assistant",
      "voice transcription",
      "claim extraction",
      "evidence-based validation",
    ],
    alternates: {
      canonical: canonical.pathname,
      languages: {
        en: "/en",
        nl: "/nl",
      },
    },
    robots: {
      index: true,
      follow: true,
      googleBot: {
        index: true,
        follow: true,
        "max-image-preview": "large",
        "max-snippet": -1,
        "max-video-preview": -1,
      },
    },
    icons: {
      icon: [{ url: "/logo.svg", type: "image/svg+xml" }],
      apple: [{ url: "/logo.svg" }],
    },
    openGraph: {
      title: t.title,
      description: t.description,
      type: "website",
      url: canonical,
      siteName: "Brutally Honest",
      locale: locale === "nl" ? "nl_NL" : "en_US",
    },
    twitter: {
      card: "summary_large_image",
      title: t.title,
      description: t.description,
    },
  };
}

export default async function LocaleLayout({ children, params }: Props) {
  const { locale } = await params;

  // Validate locale
  if (!locales.includes(locale as Locale)) {
    notFound();
  }

  setRequestLocale(locale);
  const messages = await getMessages();

  return (
    <html lang={locale} className="scroll-smooth" suppressHydrationWarning>
      <body className={`${inter.variable} font-sans antialiased`}>
        <a
          href="#main-content"
          className="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:z-50 focus:rounded-md focus:bg-background focus:px-3 focus:py-2 focus:text-sm focus:text-foreground focus:shadow"
        >
          Skip to content
        </a>
        <NextIntlClientProvider messages={messages}>
          {children}
        </NextIntlClientProvider>
      </body>
    </html>
  );
}

