import type { Metadata } from "next";
import { Inter, Manrope, Newsreader } from "next/font/google";
import "./globals.css";
import "katex/dist/katex.min.css";
import PageTransition from "../components/PageTransition";
import AppShell from "../components/AppShell";
import { LibraryProvider } from "../components/LibraryContext";
import { Toaster } from "sonner";
import CommandPalette from "../components/CommandPalette";
import { ServiceWorkerRegister } from "../components/ServiceWorkerRegister";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });
const manrope = Manrope({ subsets: ["latin"], variable: "--font-manrope" });
const newsreader = Newsreader({
  subsets: ["latin"],
  weight: ["200", "300", "400", "500", "600", "700", "800"],
  style: ["normal", "italic"],
  display: "swap",
  variable: "--font-newsreader",
});

export const metadata: Metadata = {
  title: "arXiv AI Assistant",
  description: "Your personal AI research assistant",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`${inter.variable} ${manrope.variable} ${newsreader.variable} font-sans antialiased bg-background text-foreground`}>
        <LibraryProvider>
          <AppShell>
            <PageTransition>
              {children}
            </PageTransition>
          </AppShell>
          <CommandPalette />
          <ServiceWorkerRegister />
          <Toaster
            position="bottom-right"
            toastOptions={{
              style: {
                background: 'var(--color-surface-card)',
                color: 'var(--color-foreground)',
                border: 'none',
                boxShadow: '0 4px 24px rgba(60,40,20,0.08)',
              },
            }}
          />
          <div className="fixed bottom-2 right-2 text-[10px] text-zinc-600 opacity-50 pointer-events-none z-50">
            v1.0.3 (Clean Build: 2026-01-26 13:10)
          </div>
        </LibraryProvider>
      </body>
    </html>
  );
}
