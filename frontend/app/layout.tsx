import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import { ThemeProvider } from "@/components/theme-provider";
import { QueryProvider } from "@/components/query-provider";
import { Toaster } from "@/components/ui/toaster";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: {
    default: "Velora — Multi-Provider AI Inference Platform",
    template: "%s | Velora",
  },
  description:
    "Production-inspired AI gateway with intelligent routing, cost analytics, and a Routing Decision Inspector. Route across OpenAI, Anthropic, and Gemini from one unified API.",
  keywords: ["AI", "LLM", "inference", "routing", "OpenAI", "Anthropic", "Gemini", "API gateway"],
  authors: [{ name: "Hardik Gupta", url: "https://github.com/hardik2004gupta" }],
  openGraph: {
    type: "website",
    title: "Velora — Multi-Provider AI Inference Platform",
    description: "Route AI requests intelligently across OpenAI, Anthropic, and Gemini.",
    siteName: "Velora",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body
        className={`${geistSans.variable} ${geistMono.variable} font-sans antialiased`}
      >
        <ThemeProvider
          attribute="class"
          defaultTheme="dark"
          enableSystem
          disableTransitionOnChange
        >
          <QueryProvider>
            {children}
            <Toaster />
          </QueryProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
