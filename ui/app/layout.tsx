import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'Revarie LM v1.0 | Project IMACE',
  description: 'Cognitive Emulation Research Instrument',
  icons: { icon: 'https://assets.imace.online/image/imaceicon.svg' },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-background">
        {children}
      </body>
    </html>
  );
}
