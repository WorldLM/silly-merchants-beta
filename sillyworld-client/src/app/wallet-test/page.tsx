'use client';

import { useState, useEffect } from 'react';
import WalletScriptHandler from '@/components/WalletScriptHandler';

export default function WalletTestPage() {
  const [walletAvailable, setWalletAvailable] = useState(false);
  const [walletConnected, setWalletConnected] = useState(false);
  const [walletAddress, setWalletAddress] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Check if wallet is available
    const checkWallet = setTimeout(() => {
      const available = typeof window !== 'undefined' && 'sonicWallet' in window;
      setWalletAvailable(available);
      console.log("Wallet available:", available);
      if (available) {
        console.log("Wallet type:", (window as any).sonicWallet.constructor.name);
      }
    }, 1500);

    return () => clearTimeout(checkWallet);
  }, []);

  const connectWallet = async () => {
    try {
      if (typeof window !== 'undefined' && 'sonicWallet' in window) {
        const wallet = (window as any).sonicWallet;
        await wallet.connect();
        setWalletConnected(true);
        
        const publicKey = await wallet.getPublicKey();
        setWalletAddress(publicKey);
      } else {
        setError("Wallet not available");
      }
    } catch (err) {
      console.error("Error connecting wallet:", err);
      setError(err instanceof Error ? err.message : "Unknown error");
    }
  };

  return (
    <div className="min-h-screen bg-gray-900 flex flex-col items-center justify-center p-4">
      <WalletScriptHandler />
      
      <div className="bg-gray-800 p-6 rounded-lg shadow-lg max-w-md w-full">
        <h1 className="text-2xl font-bold text-white mb-4">Wallet Test Page</h1>
        
        <div className="space-y-4">
          <div className="bg-gray-700 p-3 rounded">
            <p className="text-white">Wallet Available: <span className={walletAvailable ? "text-green-400" : "text-red-400"}>{walletAvailable ? "Yes" : "No"}</span></p>
          </div>
          
          {error && (
            <div className="bg-red-900 bg-opacity-50 p-3 rounded text-white text-sm">
              Error: {error}
            </div>
          )}
          
          {!walletConnected ? (
            <button
              onClick={connectWallet}
              className="w-full bg-indigo-600 hover:bg-indigo-700 text-white py-2 px-4 rounded"
            >
              Connect Wallet
            </button>
          ) : (
            <div className="bg-green-900 bg-opacity-50 p-3 rounded">
              <p className="text-white">Connected!</p>
              <p className="text-gray-300 text-sm break-all">{walletAddress}</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
} 