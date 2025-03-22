'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

export default function HomeRedirect() {
  const router = useRouter();
  
  useEffect(() => {
    // 立即重定向到根路径
    router.replace('/');
  }, [router]);
  
  return (
    <div className="min-h-screen flex items-center justify-center">
      <p className="text-gray-400">正在重定向...</p>
    </div>
  );
} 