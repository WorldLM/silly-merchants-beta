import { Inter, Montserrat } from 'next/font/google'
import localFont from 'next/font/local'

// Google fonts
export const inter = Inter({ 
  subsets: ['latin'], 
  variable: '--font-inter',
  display: 'swap'
})

export const montserrat = Montserrat({ 
  subsets: ['latin'], 
  variable: '--font-montserrat',
  display: 'swap'
})

// Local fonts - using the correct file paths
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