"use client";

import React, { useState, useEffect } from 'react';
import WelcomeStage from './components/WelcomeStage';
import CoachingStage from './components/CoachingStage';
import DemoDayStage from './components/DemoDayStage';
import QAStage from './components/QAStage';
import ResultsStage from './components/ResultsStage';
import ProgressIndicator from './components/ProgressIndicator';
import { content } from './utils/contentData';
import styles from './idea-pitching.module.css';
import { preloadAudioFiles } from './utils/audioPreloader';

export default function IdeaPitchingPOC() {
  // Core state
  const [stage, setStage] = useState('welcome');
  const [language, setLanguage] = useState('en');
  
  // Business data state
  const [businessData, setBusinessData] = useState({
    businessIdea: '',
    problemSolution: '',
    valueProposition: '',
    teamBackground: '',
    fundingUsage: '',
    teamCulture: ''
  });
  
  // Add a loading state
  const [isLoading, setIsLoading] = useState(true);
  
  // Preload audio files when the component mounts
  useEffect(() => {
    preloadAudioFiles(() => {
      setIsLoading(false);
    });
  }, []);
  
  // Update business data
  const updateBusinessData = (field, value) => {
    setBusinessData(prev => ({
      ...prev,
      [field]: value
    }));
  };
  
  // Function to toggle language
  const toggleLanguage = () => {
    setLanguage(language === 'en' ? 'zh' : 'en');
  };
  
  // Function to move to next stage
  const nextStage = () => {
    switch (stage) {
      case 'welcome':
        setStage('coaching');
        break;
      case 'coaching':
        setStage('demoDay');
        break;
      case 'demoDay':
        setStage('qa');
        break;
      case 'qa':
        setStage('results');
        break;
    }
  };
  
  // Render the current stage
  const renderStage = () => {
    switch (stage) {
      case 'welcome':
        return <WelcomeStage 
          content={content[language].welcome} 
          onStart={nextStage} 
        />;
      
      case 'coaching':
        return <CoachingStage 
          content={content[language].coaching}
          businessData={businessData}
          updateBusinessData={updateBusinessData}
          onComplete={nextStage}
        />;
      
      case 'demoDay':
        return <DemoDayStage 
          content={content[language].demoDay}
          businessData={businessData}
          onComplete={nextStage}
        />;
      
      case 'qa':
        return <QAStage 
          content={content[language].qa}
          businessData={businessData}
          onComplete={nextStage}
        />;
      
      case 'results':
        return <ResultsStage 
          content={content[language].results}
          businessData={businessData}
        />;
      
      default:
        return <div>Unknown stage</div>;
    }
  };
  
  return (
    <div className={styles.container}>
      {/* Language Switcher */}
      <button 
        onClick={toggleLanguage} 
        className={styles.languageSwitcher}
      >
        {language === 'en' ? '中文' : 'English'}
      </button>
      
      {/* Header */}
      <header className={styles.header}>
        <h1 className={styles.title}>{content[language].title}</h1>
        <p className={styles.subtitle}>{content[language].subtitle}</p>
      </header>
      
      {/* Main Content */}
      <main className={styles.main}>
        {isLoading ? (
          <div className={styles.loadingContainer}>
            <div className={styles.loadingSpinner}></div>
            <p className={styles.loadingText}>Loading audio resources...</p>
          </div>
        ) : (
          renderStage()
        )}
      </main>
      
      {/* Progress Indicator */}
      {!isLoading && (
        <ProgressIndicator 
          currentStage={stage} 
          stages={['welcome', 'coaching', 'demoDay', 'qa', 'results']} 
        />
      )}
    </div>
  );
} 