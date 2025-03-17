import localFont from 'next/font/local'
import { Inter, Montserrat } from 'next/font/google'

// Load the Venite Adoremus font for titles
export const veniteAdoremus = localFont({
  src: [
    {
      path: '../../public/fonts/venite-adoremus-font/VeniteAdoremus-rgRBA.ttf',
      weight: '400',
      style: 'normal',
    },
    {
      path: '../../public/fonts/venite-adoremus-font/VeniteAdoremusStraight-Yzo6v.ttf',
      weight: '700',
      style: 'normal',
    }
  ],
  display: 'swap',
  variable: '--font-venite-adoremus',
})

// Load Montserrat for subtitles
export const montserrat = Montserrat({
  subsets: ['latin'],
  display: 'swap',
  variable: '--font-montserrat',
})

// Load Inter for general text
export const inter = Inter({
  subsets: ['latin'],
  display: 'swap',
  variable: '--font-inter',
}) 