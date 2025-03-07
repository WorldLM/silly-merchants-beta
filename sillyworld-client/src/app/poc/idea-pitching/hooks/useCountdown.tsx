import { useState, useEffect } from 'react';

export function useCountdown(initialValue = 5, onComplete) {
  const [showCountdown, setShowCountdown] = useState(false);
  const [countdownValue, setCountdownValue] = useState(initialValue);
  
  // Start countdown
  const startCountdown = () => {
    setShowCountdown(true);
    setCountdownValue(initialValue);
    
    const countdownInterval = setInterval(() => {
      setCountdownValue(prev => {
        if (prev <= 1) {
          clearInterval(countdownInterval);
          setShowCountdown(false);
          if (onComplete) onComplete();
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
    
    return () => clearInterval(countdownInterval);
  };
  
  return {
    showCountdown,
    countdownValue,
    startCountdown
  };
} 