"use client";

import React, { useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Mail, ArrowRight, CheckCircle, Loader2 } from "lucide-react";

export function ComingSoon() {
  const [email, setEmail] = useState("");
  const [status, setStatus] = useState<"idle" | "loading" | "success" | "error">("idle");
  const [message, setMessage] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email) return;

    setStatus("loading");

    try {
      const response = await fetch("/api/contact", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, type: "waitlist" }),
      });

      if (response.ok) {
        setStatus("success");
        setMessage("You're on the list! We'll be in touch soon.");
        setEmail("");
      } else {
        throw new Error("Failed to submit");
      }
    } catch {
      setStatus("error");
      setMessage("Something went wrong. Please try again.");
    }
  };

  return (
    <section className="py-16 lg:min-h-screen bg-white text-gray-900">
      <div className="container h-full">
        <div className="grid h-full min-h-[calc(100vh-8rem)] grid-cols-1 gap-12 lg:grid-cols-2 lg:gap-0">
          {/* Left Column */}
          <div className="col-span-1 flex h-full flex-col items-start justify-between gap-12 lg:pr-12">
            {/* Logo */}
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-gray-900 flex items-center justify-center">
                <svg width="24" height="24" viewBox="0 0 96 95" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M86.2228 19.9976C80.6228 12.0976 72.7228 6.09758 63.6228 2.79758C45.0228 -4.00242 23.4228 1.89758 10.9228 17.1976C4.62282 24.7976 0.822819 34.1976 0.122819 43.9976C-0.577181 53.6976 1.72282 63.6976 6.82282 72.0976C11.7228 80.0976 19.1228 86.7976 27.7228 90.6976C36.9228 94.8976 47.2228 95.9976 57.1228 93.9976C76.1228 90.1976 91.4228 74.1976 94.4228 55.0976C94.8228 52.5976 95.0228 50.0976 95.0228 47.4976C94.9228 37.6976 91.9228 27.9976 86.2228 19.9976ZM62.2228 87.2976C53.8228 90.3976 44.5228 90.7976 35.9228 88.2976C27.6228 85.9976 20.2228 81.0976 14.7228 74.3976C3.32282 60.6976 1.92282 40.5976 11.1228 25.3976C20.2228 10.3976 38.4228 2.29758 55.8228 5.79758C73.1228 9.29758 86.6228 23.3976 89.5228 40.8976C89.8228 43.0976 90.0228 45.2976 90.0228 47.4976C89.9228 64.9976 78.8228 81.2976 62.2228 87.2976Z" fill="white"/>
                  <path d="M47.5226 75.4975C52.714 75.4975 56.9226 71.289 56.9226 66.0975C56.9226 60.906 52.714 56.6975 47.5226 56.6975C42.3311 56.6975 38.1226 60.906 38.1226 66.0975C38.1226 71.289 42.3311 75.4975 47.5226 75.4975Z" fill="white"/>
                  <path d="M43 44.0463V21.9537C43 19.9022 41.08 17.8508 39 18.0086C36.92 18.1664 35 19.7444 35 21.9537V44.0463C35 46.0978 36.92 48.1492 39 47.9914C41.08 47.8336 43 46.2556 43 44.0463Z" fill="white"/>
                  <path d="M56.1001 18.0086C54.0201 18.1664 52.1001 19.7444 52.1001 21.9537V44.0463C52.1001 46.0978 54.0201 48.1492 56.1001 47.9914C58.1801 47.8336 60.1001 46.2556 60.1001 44.0463V21.9537C60.1001 19.9022 58.3401 17.8508 56.1001 18.0086Z" fill="white"/>
                </svg>
              </div>
              <span className="text-xl font-semibold tracking-tight">Brutally Honest</span>
            </div>

            {/* Main Content */}
            <div className="flex max-w-sm flex-col gap-4 sm:max-w-full lg:max-w-md">
              <Badge variant="outline" className="w-fit border-gray-300 text-gray-600">
                COMING SOON — Q1 2026
              </Badge>

              <h1 className="text-3xl font-semibold lg:text-4xl text-gray-900">
                Truth in every conversation
              </h1>

              <p className="text-gray-500 max-w-md">
                Real-time AI fact-checking for interviews, meetings, and negotiations. 
                Know what's true—and what's not—the moment it's said.
              </p>

              {/* Email Form */}
              <div className="mt-2 flex flex-col gap-4">
                {status === "success" ? (
                  <div className="flex items-center gap-2 text-green-600 bg-green-50 rounded-lg px-4 py-3">
                    <CheckCircle className="w-5 h-5" />
                    <span>{message}</span>
                  </div>
                ) : (
                  <form onSubmit={handleSubmit} className="flex gap-2">
                    <Input
                      type="email"
                      required
                      placeholder="name@domain.com"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      className="border-gray-300 bg-white text-gray-900 placeholder:text-gray-400"
                    />
                    <Button 
                      type="submit" 
                      disabled={status === "loading"}
                      className="bg-gray-900 text-white hover:bg-gray-800"
                    >
                      {status === "loading" ? (
                        <Loader2 className="w-4 h-4 animate-spin" />
                      ) : (
                        "Join now"
                      )}
                    </Button>
                  </form>
                )}

                {status === "error" && (
                  <p className="text-red-500 text-sm">{message}</p>
                )}

                {/* Action Buttons */}
                <div className="flex flex-col sm:flex-row gap-3 mt-4">
                  <Button
                    variant="outline"
                    className="border-gray-300 bg-gray-900 text-white hover:bg-gray-800"
                    onClick={() => window.open("mailto:daniel@altfawesome.nl", "_blank")}
                  >
                    <Mail className="w-4 h-4 mr-2" />
                    Contact Us
                  </Button>
                  <Button
                    className="bg-gray-900 text-white hover:bg-gray-800"
                    onClick={() => window.open("https://app.brutallyhonest.io", "_blank")}
                  >
                    Try Early Access
                    <ArrowRight className="w-4 h-4 ml-1" />
                  </Button>
                </div>
              </div>
            </div>

            {/* Footer */}
            <p className="text-gray-400 text-xs">
              © {new Date().getFullYear()} —{" "}
              <a
                href="https://altfawesome.nl"
                target="_blank"
                className="text-gray-900 underline"
              >
                ALT F AWESOME
              </a>{" "}
              — All rights reserved.
            </p>
          </div>

          {/* Right Column - Image */}
          <div className="col-span-1 flex h-full flex-col items-start justify-between overflow-hidden rounded-xl lg:rounded-none">
            <img
              src="/hero.png"
              alt="Brutally Honest AI"
              className="h-full min-h-[400px] lg:min-h-[600px] w-full object-cover rounded-xl"
            />
          </div>
        </div>
      </div>
    </section>
  );
}
