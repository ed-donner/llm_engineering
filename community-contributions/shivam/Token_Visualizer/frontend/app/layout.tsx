import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'Token Visualizer',
  description: 'Visualize LLM token prediction probabilities',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}