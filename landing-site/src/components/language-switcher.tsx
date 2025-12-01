"use client";

import { useLocale } from "next-intl";
import { usePathname, useRouter } from "next/navigation";
import { locales, localeNames, localeFlags, type Locale } from "@/i18n/config";

export function LanguageSwitcher() {
  const locale = useLocale() as Locale;
  const router = useRouter();
  const pathname = usePathname();

  const switchLocale = (newLocale: Locale) => {
    // Remove current locale from pathname if present
    const segments = pathname.split('/').filter(Boolean);
    const currentLocaleInPath = locales.includes(segments[0] as Locale);
    
    let newPath: string;
    if (currentLocaleInPath) {
      segments[0] = newLocale;
      newPath = '/' + segments.join('/');
    } else {
      newPath = newLocale === 'en' ? pathname : `/${newLocale}${pathname}`;
    }
    
    router.push(newPath);
  };

  const otherLocale = locale === 'en' ? 'nl' : 'en';

  return (
    <button
      onClick={() => switchLocale(otherLocale)}
      className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-secondary/50 hover:bg-secondary border border-border transition-all text-sm font-medium"
      aria-label={`Switch to ${localeNames[otherLocale]}`}
    >
      <span className="text-lg leading-none">{localeFlags[otherLocale]}</span>
      <span className="hidden sm:inline text-muted-foreground">{localeNames[otherLocale]}</span>
    </button>
  );
}

