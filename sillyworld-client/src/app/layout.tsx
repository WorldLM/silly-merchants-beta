import type { Metadata } from 'next'
import './globals.css'
import { veniteAdoremus, montserrat, inter } from './fonts'

export const metadata: Metadata = {
  title: 'SillyWorld',
  description: 'Build your agent game empire ventures',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className={`${veniteAdoremus.variable} ${montserrat.variable} ${inter.variable}`}>
      <body className={inter.className}>{children}</body>
    </html>
  )
}
