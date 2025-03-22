'use client';

import { useEffect } from 'react';

export default function WalletScriptHandler() {
  useEffect(() => {
    // Load mock MetaMask for development
    if (typeof window !== 'undefined' && !('ethereum' in window)) {
      import('../services/mockMetamask').then(() => {
        console.log('Mock MetaMask loaded by WalletScriptHandler');
      });
    }
  }, []);

  // This component doesn't render anything
  return null;
} 