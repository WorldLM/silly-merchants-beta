import { useState, useEffect, useRef } from 'react';

export function useTypewriter(initialSpeed = 30) {
  const [isTyping, setIsTyping] = useState(false);
  const [displayText, setDisplayText] = useState('');
  const [voice, setVoice] = useState('');
  const [speed, setSpeed] = useState(initialSpeed);
  const intervalRef = useRef(null);
  
  // Start typewriter effect
  const startTypewriter = (text, customSpeed = null) => {
    // Clear any existing interval
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
    }
    
    // Use custom speed if provided, otherwise use the current speed
    const typingSpeed = customSpeed !== null ? customSpeed : speed;
    
    // Reset state
    setIsTyping(true);
    setDisplayText('');
    
    let i = 0;
    const typeInterval = setInterval(() => {
      if (i < text.length) {
        setDisplayText(text.substring(0, i + 1));
        i++;
      } else {
        clearInterval(typeInterval);
        setIsTyping(false);
      }
    }, typingSpeed);
    
    // Store the interval reference
    intervalRef.current = typeInterval;
    
    // Cleanup function
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  };
  
  // Clean up on unmount
  useEffect(() => {
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, []);
  
  return {
    isTyping,
    displayText,
    voice,
    setVoice,
    startTypewriter,
    setSpeed
  };
} 