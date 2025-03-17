'use client';

import Navbar from '@/components/Navbar';

export default function TestNavbarPage() {
  const handleWalletConnect = (publicKey: string) => {
    console.log('Wallet connected:', publicKey);
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      <Navbar onWalletConnect={handleWalletConnect} />
      
      <div className="pt-20 p-4">
        <h1 className="text-2xl font-bold">Navbar Test Page</h1>
        <p className="mt-4">This page is just for testing the navbar component.</p>
      </div>
    </div>
  );
} 