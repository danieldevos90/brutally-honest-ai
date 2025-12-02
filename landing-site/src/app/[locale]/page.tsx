import { setRequestLocale } from "next-intl/server";
import { ComingSoon } from "@/components/coming-soon";

type Props = {
  params: Promise<{ locale: string }>;
};

export default async function Home({ params }: Props) {
  const { locale } = await params;
  setRequestLocale(locale);

  return (
    <main className="min-h-screen bg-background">
      <ComingSoon />
    </main>
  );
}
