'use client';

import React from 'react';

interface LoadingSpinnerProps {
  size?: 'small' | 'medium' | 'large';
  color?: string;
  text?: string;
}

const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  size = 'medium',
  color = '#6366f1', // indigo-500
  text = '加载中...'
}) => {
  // 根据size设置spinner尺寸
  const sizeMap = {
    small: 'w-5 h-5',
    medium: 'w-8 h-8',
    large: 'w-12 h-12'
  };

  // 根据size设置文字大小
  const textSizeMap = {
    small: 'text-xs',
    medium: 'text-sm',
    large: 'text-base'
  };

  return (
    <div className="flex flex-col items-center justify-center">
      <div className={`animate-spin rounded-full border-t-2 border-b-2 ${sizeMap[size]}`} 
           style={{ borderColor: color }}></div>
      {text && <p className={`mt-2 ${textSizeMap[size]} text-gray-300`}>{text}</p>}
    </div>
  );
};

export default LoadingSpinner; 