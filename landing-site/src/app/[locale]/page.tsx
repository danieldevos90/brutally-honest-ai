import { setRequestLocale } from "next-intl/server";
import { getMessages } from "next-intl/server";
import { ComingSoon } from "@/components/coming-soon";
import { LandingJsonLd } from "@/components/landing-jsonld";
import { getSiteUrl } from "@/lib/site";

type Props = {
  params: Promise<{ locale: string }>;
};

type LandingMessages = {
  faq?: {
    items?: Array<{ q: string; a: string }>;
  };
};

type PageMessages = {
  metadata?: {
    title?: string;
    description?: string;
  };
  landing?: LandingMessages;
};

export default async function Home({ params }: Props) {
  const { locale } = await params;
  setRequestLocale(locale);
  const messages = await getMessages();
  const typedMessages = messages as unknown as PageMessages;
  const landing = typedMessages.landing;
  const meta = typedMessages.metadata || {};
  const siteUrl = getSiteUrl();
  const url = `${siteUrl}/${locale}`;

  return (
    <>
      <LandingJsonLd
        locale={locale}
        url={url}
        title={meta.title || "Brutally Honest"}
        description={meta.description || ""}
        faq={landing?.faq?.items || []}
      />
      <main id="main-content" className="min-h-screen bg-background">
        <ComingSoon />
      </main>
    </>
  );
}
