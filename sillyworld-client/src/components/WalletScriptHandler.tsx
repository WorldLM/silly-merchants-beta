'use client';

import { useEffect, useState } from 'react';

export default function WalletScriptHandler() {
  const [mockLoaded, setMockLoaded] = useState(false);
  const [loadAttempted, setLoadAttempted] = useState(false);

  useEffect(() => {
    // Check if Sonic wallet is already available (might be loaded by another component)
    if (typeof window !== 'undefined' && 'sonicWallet' in window) {
      console.log("Sonic wallet already available in window object");
      return;
    }

    // Check if wallet is available after a short delay
    const checkWalletTimeout = setTimeout(() => {
      setLoadAttempted(true);
      
      if (typeof window !== 'undefined' && !('sonicWallet' in window)) {
        console.warn("Sonic wallet not available after timeout, loading mock implementation");
        
        // Import the mock wallet
        import('../services/mockWallet')
          .then(() => {
            console.log("Mock wallet loaded successfully");
            setMockLoaded(true);
            
            // Verify the mock wallet was added to window
            if (typeof window !== 'undefined' && 'sonicWallet' in window) {
              console.log("Mock wallet successfully added to window object");
            } else {
              console.error("Mock wallet failed to add to window object");
            }
          })
          .catch(err => {
            console.error("Failed to load mock wallet:", err);
          });
      } else {
        console.log("Sonic wallet script loaded successfully");
      }
    }, 2000); // Give the script 2 seconds to load

    return () => clearTimeout(checkWalletTimeout);
  }, []);

  // This component doesn't render anything visible except a small indicator
  return mockLoaded ? (
    <div className="fixed bottom-0 left-0 bg-yellow-600 text-white text-xs p-1 z-50 opacity-70">
      Using mock wallet
    </div>
  ) : loadAttempted && !('sonicWallet' in window) ? (
    <div className="fixed bottom-0 left-0 bg-red-600 text-white text-xs p-1 z-50 opacity-70">
      Wallet loading failed
    </div>
  ) : null;
} 