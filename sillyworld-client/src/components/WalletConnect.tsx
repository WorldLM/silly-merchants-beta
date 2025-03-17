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
      // Check if sonicWallet exists
      if ('sonicWallet' in window) {
        // Check if it's a mock by looking for a specific property
        const wallet = (window as any).sonicWallet;
        if (wallet.constructor.name === 'MockSonicWallet') {
          setIsMockWallet(true);
          console.log("Using mock Sonic wallet for development");
        }
      } else {
        console.error("Sonic wallet not available");
        setError("Sonic Wallet not detected. Using mock implementation for development.");
        // Import the mock wallet
        import('../services/mockWallet').then(() => {
          setIsMockWallet(true);
          console.log("Mock wallet loaded");
        });
      }
    }
  }, []);

  // Check if wallet is already connected on component mount
  useEffect(() => {
    const checkWalletConnection = async () => {
      try {
        // Check if Sonic wallet is available
        if (typeof window !== 'undefined' && 'sonicWallet' in window) {
          const wallet = (window as any).sonicWallet;
          
          // Check if already connected
          const isConnected = await wallet.isConnected();
          if (isConnected) {
            const publicKey = await wallet.getPublicKey();
            onConnect(publicKey.toString());
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
      // Check if Sonic wallet is available
      if (typeof window !== 'undefined' && 'sonicWallet' in window) {
        const wallet = (window as any).sonicWallet;
        
        // Connect to wallet
        await wallet.connect();
        const publicKey = await wallet.getPublicKey();
        
        // Call the onConnect callback with the public key
        onConnect(publicKey.toString());
      } else {
        setError('Sonic Wallet not detected. Please install the Sonic Wallet extension.');
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
          Using mock wallet for development. In production, this would connect to the real Sonic wallet.
        </div>
      )}
      
      <button
        onClick={connectWallet}
        disabled={connecting}
        className="bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 text-white font-bold py-3 px-6 rounded-lg focus:outline-none focus:shadow-outline transition-all duration-300 disabled:opacity-50"
      >
        {connecting ? (
          <div className="flex items-center">
            <div className="w-5 h-5 border-t-2 border-b-2 border-white rounded-full animate-spin mr-2"></div>
            <span>连接中...</span>
          </div>
        ) : (
          `连接 ${isMockWallet ? '模拟' : 'Sonic'} 钱包`
        )}
      </button>
      
      <p className="mt-4 text-sm text-gray-400">
        {isMockWallet 
          ? '当前使用模拟钱包进行开发测试' 
          : '需要安装 Sonic 钱包才能参与游戏'}
      </p>
    </div>
  );
};

export default WalletConnect; 