import './globals.css'
import type { Metadata } from 'next'
import { Inter } from 'next/font/google'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'SillyWorld - AI代理对抗游戏',
  description: '让不同个性的AI在竞技场中进行策略对决',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="zh">
      <head>
        {/* We're not loading the Sonic wallet script anymore, using mock implementation instead */}
      </head>
      <body className={inter.className}>
        <main className="min-h-screen bg-gray-900 text-white">
          {children}
        </main>
      </body>
    </html>
  )
}
