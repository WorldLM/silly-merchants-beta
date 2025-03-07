import React, { useState, useEffect } from 'react';
import { useAudio } from '../hooks/useAudio';
import { useTypewriter } from '../hooks/useTypewriter';
import { useCountdown } from '../hooks/useCountdown';
import styles from '../idea-pitching.module.css';
import { calculateTextDuration, calculateTypewriterSpeed } from '../utils/audioUtils';

export default function DemoDayStage({ content, businessData, onComplete }) {
  const { isPlaying, playAudio, audioRef } = useAudio();
  const { isTyping, displayText, voice, setVoice, startTypewriter } = useTypewriter();
  const { showCountdown, countdownValue, startCountdown } = useCountdown(5, startPitch);
  
  const [pitchStarted, setPitchStarted] = useState(false);
  const [pitchCompleted, setPitchCompleted] = useState(false);
  
  // Start countdown when component mounts
  useEffect(() => {
    startCountdown();
  }, []);
  
  // Function to determine which pitch audio to use
  const getPitchAudioKey = (businessData) => {
    const { businessIdea } = businessData;
    
    if (businessIdea.includes('AI') || businessIdea.includes('artificial intelligence')) {
      return 'pitch_ai';
    } else if (businessIdea.includes('blockchain')) {
      return 'pitch_blockchain';
    } else {
      return 'pitch_wearable';
    }
  };
  
  // Function to play audio with typewriter effect
  const playAudioWithTypewriter = (text, voiceType, pitchKey = '') => {
    setVoice(voiceType);
    startTypewriter(text);
    
    if (voiceType === 'pitch' && pitchKey) {
      // Use the specific pitch audio file
      playAudio(text, voiceType, 0, 0, pitchKey);
    } else {
      playAudio(text, voiceType);
    }
  };
  
  // Function to start the pitch after countdown
  function startPitch() {
    setPitchStarted(true);
    
    // Generate pitch text based on business data
    const pitchText = generatePitchText(businessData);
    const pitchKey = getPitchAudioKey(businessData);
    
    // Play the pitch with typewriter effect
    setTimeout(() => {
      playAudioWithTypewriter(pitchText, 'pitch', pitchKey);
    }, 500);
  }
  
  // Function to generate pitch text based on business data
  function generatePitchText(data) {
    const { businessIdea, problemSolution, valueProposition, teamBackground, fundingUsage, teamCulture } = data;
    
    return `Hello investors, I'm Alex representing our startup ${
      businessIdea.includes('AI') 
        ? 'leveraging artificial intelligence' 
        : businessIdea.includes('blockchain') 
          ? 'using blockchain technology' 
          : 'with an innovative approach'
    } to ${
      problemSolution.split('.')[0].toLowerCase()
    }. Our solution ${
      valueProposition.includes('reduces') 
        ? 'significantly reduces costs and improves efficiency' 
        : 'creates substantial value for our customers'
    }. The market opportunity is ${
      valueProposition.includes('$') 
        ? valueProposition.match(/\$\d+[BM]/) 
          ? valueProposition.match(/\$\d+[BM]/)[0] 
          : 'substantial' 
        : 'growing rapidly'
    }. Our exceptional team includes ${
      teamBackground.includes('Google') 
        ? 'former Google engineers' 
        : teamBackground.includes('founder') 
          ? 'successful founders' 
          : 'industry experts'
    }. With your investment of $1.5M, we'll ${
      fundingUsage.includes('engineering') 
        ? 'accelerate product development and go-to-market' 
        : 'expand our market reach and scale our operations'
    }. Our team culture ${
      teamCulture.includes('innovation') 
        ? 'fosters innovation and customer obsession' 
        : 'values excellence and sustainable growth'
    }. Thank you for your consideration.`;
  }
  
  // Handle pitch completion
  useEffect(() => {
    if (pitchStarted && !isTyping && !isPlaying) {
      setPitchCompleted(true);
    }
  }, [pitchStarted, isTyping, isPlaying]);
  
  return (
    <div className={styles.demoDayStage}>
      {showCountdown ? (
        <div className={styles.countdownContainer}>
          <div className={styles.countdownNumber}>{countdownValue}</div>
        </div>
      ) : (
        <>
          <h2>{content.heading}</h2>
          
          <div className={styles.pitchContainer}>
            <div className={styles.alexAvatar}>
              <svg width="100" height="100" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
                <circle cx="50" cy="50" r="50" fill="#3498db" />
                <text x="50" y="55" fontSize="20" textAnchor="middle" fill="white" fontFamily="Arial">Alex</text>
              </svg>
            </div>
            
            <div className={styles.pitchContent}>
              <p className={styles.pitchText}>
                {isTyping ? displayText : generatePitchText(businessData)}
              </p>
              
              {pitchCompleted && (
                <button 
                  className={styles.actionButton}
                  onClick={onComplete}
                >
                  {content.continueButton}
                </button>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
} 