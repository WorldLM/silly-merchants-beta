import type { Metadata, Viewport } from 'next'
import './globals.css'
import { inter, montserrat, veniteAdoremus } from './fonts'

export const metadata: Metadata = {
  title: 'SillyWorld',
  description: 'Build your AI game agentic empire ventures.',
}

// Separate viewport export as recommended by Next.js 14
export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
  maximumScale: 1,
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={`${inter.variable} ${montserrat.variable} ${veniteAdoremus.variable}`}>
        {children}
      </body>
    </html>
  )
}
