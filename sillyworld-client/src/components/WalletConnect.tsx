'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';

interface WalletConnectProps {
  onConnect: (publicKey: string) => void;
}

const WalletConnect: React.FC<WalletConnectProps> = ({ onConnect }) => {
  const [connecting, setConnecting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isMockWallet, setIsMockWallet] = useState(false);
  const router = useRouter();

  // Check if wallet is available and if it's a mock
  useEffect(() => {
    if (typeof window !== 'undefined') {
      // Check if ethereum provider exists (MetaMask)
      if ('ethereum' in window) {
        const ethereum = (window as any).ethereum;
        if (ethereum.isMetaMask) {
          console.log("MetaMask detected");
          if ((window as any).ethereum._metamask?.isUnlocked === false) {
            setIsMockWallet(true);
            console.log("Using mock MetaMask for development");
          }
        }
      } else {
        console.error("MetaMask not available");
        setError("MetaMask not detected. Using mock implementation for development.");
        // Import the mock wallet
        import('../services/mockMetamask').then(() => {
          setIsMockWallet(true);
          console.log("Mock MetaMask loaded");
        });
      }
    }
  }, []);

  // Check if wallet is already connected on component mount
  useEffect(() => {
    const checkWalletConnection = async () => {
      try {
        // Check if MetaMask is available
        if (typeof window !== 'undefined' && 'ethereum' in window) {
          const ethereum = (window as any).ethereum;
          
          // Get accounts
          const accounts = await ethereum.request({ method: 'eth_accounts' });
          
          // If we have accounts, we're connected
          if (accounts && accounts.length > 0) {
            onConnect(accounts[0]);
          }
        }
      } catch (err) {
        console.error('Error checking wallet connection:', err);
      }
    };

    checkWalletConnection();
  }, [onConnect]);

  const connectWallet = async () => {
    setConnecting(true);
    setError(null);

    try {
      // Check if MetaMask is available
      if (typeof window !== 'undefined' && 'ethereum' in window) {
        const ethereum = (window as any).ethereum;
        
        // Request accounts
        const accounts = await ethereum.request({ method: 'eth_requestAccounts' });
        
        if (accounts && accounts.length > 0) {
          // Call the onConnect callback with the address
          onConnect(accounts[0]);
        } else {
          setError('Failed to get accounts from MetaMask');
        }
      } else {
        setError('MetaMask not detected. Please install the MetaMask extension.');
      }
    } catch (err) {
      console.error('Error connecting to wallet:', err);
      setError('Failed to connect to wallet. Please try again.');
    } finally {
      setConnecting(false);
    }
  };

  return (
    <div className="flex flex-col items-center">
      {error && (
        <div className="bg-red-600 text-white p-3 rounded-lg mb-4 text-sm">
          {error}
        </div>
      )}
      
      {isMockWallet && (
        <div className="bg-yellow-600 text-white p-3 rounded-lg mb-4 text-sm">
          Using mock wallet for development. In production, this would connect to the real MetaMask wallet.
        </div>
      )}
      
      <button
        onClick={connectWallet}
        disabled={connecting}
        className="bg-gradient-to-r from-orange-500 to-amber-600 hover:from-orange-600 hover:to-amber-700 text-white font-bold py-3 px-6 rounded-lg focus:outline-none focus:shadow-outline transition-all duration-300 disabled:opacity-50"
      >
        {connecting ? (
          <div className="flex items-center">
            <div className="w-5 h-5 border-t-2 border-b-2 border-white rounded-full animate-spin mr-2"></div>
            <span>Connecting...</span>
          </div>
        ) : (
          `Connect ${isMockWallet ? 'Mock' : ''} MetaMask`
        )}
      </button>
      
      <p className="mt-4 text-sm text-gray-400">
        {isMockWallet 
          ? 'Currently using mock MetaMask for development' 
          : 'MetaMask is required to participate in the game'}
      </p>
    </div>
  );
};

export default WalletConnect; 