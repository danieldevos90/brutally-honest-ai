"use client";

import Link from "next/link";
import Image from "next/image";
import { useTranslations } from "next-intl";
import { Separator } from "@/components/ui/separator";
import { Github } from "lucide-react";

export function Footer() {
  const t = useTranslations("footer");

  const footerLinks = {
    product: [
      { label: t("features"), href: "#benefits" },
      { label: t("pricing"), href: "#pricing" },
      { label: t("howItWorks"), href: "#how-it-works" },
    ],
    company: [
      { label: t("about"), href: "https://altfawesome.com" },
      { label: t("contact"), href: "mailto:hello@brutallyhonest.io" },
    ],
    legal: [
      { label: t("privacy"), href: "#" },
      { label: t("terms"), href: "#" },
    ],
  };

  return (
    <footer className="border-t border-border bg-black">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div className="grid grid-cols-2 md:grid-cols-5 gap-8">
          {/* Brand */}
          <div className="col-span-2">
            <Link href="/" className="flex items-center gap-3 mb-4">
              <Image
                src="/logo.svg"
                alt="Brutally Honest"
                width={28}
                height={28}
                className="invert"
              />
              <span className="text-lg font-semibold">Brutally Honest</span>
            </Link>
            <p className="text-sm text-muted-foreground mb-6 max-w-xs">
              {t("tagline")}
            </p>
            
            {/* Newsletter */}
            <div className="flex gap-2 max-w-sm">
              <input
                type="email"
                placeholder={t("emailPlaceholder")}
                className="flex-1 px-4 py-2 rounded-full bg-secondary border border-border text-sm focus:outline-none focus:border-muted-foreground"
              />
              <button className="px-4 py-2 rounded-full bg-white text-black text-sm font-medium hover:bg-white/90 transition-colors">
                {t("subscribe")}
              </button>
            </div>
          </div>

          {/* Product Links */}
          <div>
            <h4 className="font-semibold mb-4">{t("product")}</h4>
            <ul className="space-y-3">
              {footerLinks.product.map((link, index) => (
                <li key={index}>
                  <Link
                    href={link.href}
                    className="text-sm text-muted-foreground hover:text-foreground transition-colors"
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Company Links */}
          <div>
            <h4 className="font-semibold mb-4">{t("company")}</h4>
            <ul className="space-y-3">
              {footerLinks.company.map((link, index) => (
                <li key={index}>
                  <Link
                    href={link.href}
                    className="text-sm text-muted-foreground hover:text-foreground transition-colors"
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Legal Links */}
          <div>
            <h4 className="font-semibold mb-4">{t("legal")}</h4>
            <ul className="space-y-3">
              {footerLinks.legal.map((link, index) => (
                <li key={index}>
                  <Link
                    href={link.href}
                    className="text-sm text-muted-foreground hover:text-foreground transition-colors"
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        </div>

        <Separator className="my-8 bg-border" />

        {/* Bottom Bar */}
        <div className="flex flex-col md:flex-row justify-between items-center gap-4">
          <p className="text-sm text-muted-foreground">
            © {new Date().getFullYear()} ALT F AWESOME. {t("rights")}
          </p>
          
          {/* Only show GitHub - it's the only one that works */}
          <div className="flex items-center gap-4">
            <Link
              href="https://github.com/altfawesome/brutally-honest-ai"
              className="text-muted-foreground hover:text-foreground transition-colors"
              target="_blank"
              rel="noopener noreferrer"
            >
              <Github className="w-5 h-5" />
            </Link>
          </div>
        </div>
      </div>
    </footer>
  );
}
