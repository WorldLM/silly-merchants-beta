import { useEffect } from 'react';
import type { AppProps } from 'next/app';
import '../app/globals.css';

function MyApp({ Component, pageProps }: AppProps) {
  useEffect(() => {
    // Check if Sonic wallet is available, if not, load the mock
    if (typeof window !== 'undefined' && !('sonicWallet' in window)) {
      console.log("Sonic wallet not detected, loading mock implementation");
      import('../services/mockWallet');
    }
  }, []);

  return <Component {...pageProps} />;
}

export default MyApp; 