import './globals.css'
import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import WalletScriptHandler from '../components/WalletScriptHandler'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'SillyWorld - Agent Arena Game',
  description: 'Strategic competition between AI agents with different personalities',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <head>
        {/* We're using mock MetaMask implementation */}
      </head>
      <body className={inter.className}>
        <WalletScriptHandler />
        <main className="min-h-screen bg-gray-900 text-white">
          {children}
        </main>
      </body>
    </html>
  )
}
