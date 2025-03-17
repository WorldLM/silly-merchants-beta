'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';

interface NavbarProps {
  onWalletConnect?: (publicKey: string) => void;
}

export default function Navbar({ onWalletConnect }: NavbarProps) {
  const [walletConnected, setWalletConnected] = useState(false);
  const [walletAddress, setWalletAddress] = useState<string | null>(null);
  const [connecting, setConnecting] = useState(false);
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const router = useRouter();

  // Add this at the beginning of the component
  useEffect(() => {
    console.log("Navbar mounted");
    console.log("sonicWallet available:", typeof window !== 'undefined' && 'sonicWallet' in window);
    if (typeof window !== 'undefined' && 'sonicWallet' in window) {
      console.log("sonicWallet type:", (window as any).sonicWallet.constructor.name);
    }
  }, []);

  // Check if wallet is already connected on component mount
  useEffect(() => {
    const checkWalletConnection = async () => {
      try {
        if (typeof window !== 'undefined' && 'sonicWallet' in window) {
          const wallet = (window as any).sonicWallet;
          
          const isConnected = await wallet.isConnected();
          if (isConnected) {
            const publicKey = await wallet.getPublicKey();
            setWalletAddress(publicKey.toString());
            setWalletConnected(true);
            
            if (onWalletConnect) {
              onWalletConnect(publicKey.toString());
            }
          }
        }
      } catch (err) {
        console.error('Error checking wallet connection:', err);
      }
    };

    checkWalletConnection();
  }, [onWalletConnect]);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = () => {
      setDropdownOpen(false);
    };

    document.addEventListener('click', handleClickOutside);
    return () => {
      document.removeEventListener('click', handleClickOutside);
    };
  }, []);

  const connectWallet = async () => {
    setConnecting(true);
    
    try {
      if (typeof window !== 'undefined' && 'sonicWallet' in window) {
        const wallet = (window as any).sonicWallet;
        
        try {
          await wallet.connect();
          const publicKey = await wallet.getPublicKey();
          
          setWalletAddress(publicKey.toString());
          setWalletConnected(true);
          
          if (onWalletConnect) {
            onWalletConnect(publicKey.toString());
          }
        } catch (err) {
          console.error('Error in wallet operations:', err);
          // Try to recover by using a mock wallet if the real one fails
          if (wallet.constructor.name !== 'MockSonicWallet') {
            console.log('Attempting to load mock wallet as fallback...');
            import('../services/mockWallet').then(async () => {
              if (typeof window !== 'undefined' && 'sonicWallet' in window) {
                const mockWallet = (window as any).sonicWallet;
                await mockWallet.connect();
                const publicKey = await mockWallet.getPublicKey();
                
                setWalletAddress(publicKey.toString());
                setWalletConnected(true);
                
                if (onWalletConnect) {
                  onWalletConnect(publicKey.toString());
                }
              }
            });
          }
        }
      } else {
        console.error('Wallet not available, loading mock wallet...');
        // Load mock wallet if no wallet is available
        import('../services/mockWallet').then(async () => {
          if (typeof window !== 'undefined' && 'sonicWallet' in window) {
            const mockWallet = (window as any).sonicWallet;
            await mockWallet.connect();
            const publicKey = await mockWallet.getPublicKey();
            
            setWalletAddress(publicKey.toString());
            setWalletConnected(true);
            
            if (onWalletConnect) {
              onWalletConnect(publicKey.toString());
            }
          }
        });
      }
    } catch (err) {
      console.error('Error connecting wallet:', err);
    } finally {
      setConnecting(false);
    }
  };

  const disconnectWallet = async (e: React.MouseEvent) => {
    e.stopPropagation(); // Prevent the click from closing the dropdown immediately
    
    try {
      if (typeof window !== 'undefined' && 'sonicWallet' in window) {
        const wallet = (window as any).sonicWallet;
        await wallet.disconnect();
        setWalletConnected(false);
        setWalletAddress(null);
      }
    } catch (err) {
      console.error('Error disconnecting wallet:', err);
    } finally {
      setDropdownOpen(false);
    }
  };

  const toggleDropdown = (e: React.MouseEvent) => {
    e.stopPropagation(); // Prevent the document click handler from immediately closing the dropdown
    setDropdownOpen(!dropdownOpen);
  };

  return (
    <nav className="fixed top-0 left-0 right-0 z-[9999] bg-gray-900 bg-opacity-80 backdrop-blur-md shadow-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex items-center">
            <Link href="/" className="flex-shrink-0 flex items-center">
              <span className="text-xl font-bold text-white">Agent Arena</span>
            </Link>
          </div>
          
          <div className="flex items-center">
            {walletConnected ? (
              <div className="relative">
                <button 
                  onClick={toggleDropdown}
                  className="bg-green-700 hover:bg-green-800 text-white py-2 px-4 rounded-lg flex items-center transition-colors"
                >
                  <span className="w-2 h-2 bg-green-400 rounded-full mr-2"></span>
                  {walletAddress ? 
                    `${walletAddress.slice(0, 4)}...${walletAddress.slice(-4)}` : 
                    'Connected'
                  }
                </button>
                
                {dropdownOpen && (
                  <div className="absolute right-0 mt-2 w-48 bg-gray-800 rounded-md shadow-lg py-1">
                    <button
                      onClick={disconnectWallet}
                      className="block w-full text-left px-4 py-2 text-sm text-white hover:bg-gray-700"
                    >
                      断开钱包连接
                    </button>
                  </div>
                )}
              </div>
            ) : (
              <button 
                onClick={connectWallet}
                disabled={connecting}
                className="bg-indigo-600 hover:bg-indigo-700 text-white py-2 px-4 rounded-lg flex items-center transition-colors disabled:opacity-50"
              >
                {connecting ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></div>
                    连接中...
                  </>
                ) : (
                  '连接钱包'
                )}
              </button>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
} 