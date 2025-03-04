"use client";

import React from 'react';
import Link from 'next/link';

export default function SillyMerchantsGame() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center p-24 bg-gray-900 text-white">
      <h1 className="text-4xl font-bold mb-6 font-title">Silly Merchants Game</h1>
      <p className="mb-8 text-xl">Coming soon...</p>
      <Link href="/world" className="px-6 py-3 bg-gradient-to-r from-red-500 to-orange-500 rounded-full hover:translate-y-[-5px] transition-transform duration-300">
        Back to World
      </Link>
    </div>
  );
} 