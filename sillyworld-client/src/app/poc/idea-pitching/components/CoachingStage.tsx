import React, { useState, useEffect } from 'react';
import { useAudio } from '../hooks/useAudio';
import { useTypewriter } from '../hooks/useTypewriter';
import { sampleInputs } from '../utils/sampleData';
import styles from '../idea-pitching.module.css';
import { calculateTextDuration, calculateTypewriterSpeed } from '../utils/audioUtils';

export default function CoachingStage({ content, businessData, updateBusinessData, onComplete }) {
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const { 
    isRecording, 
    isPlaying, 
    transcript, 
    setTranscript,
    playAudio, 
    startRecording, 
    stopRecording,
    setCurrentAudioKey
  } = useAudio();
  
  const {
    isTyping,
    displayText,
    voice,
    setVoice,
    startTypewriter
  } = useTypewriter();
  
  // Function to use sample input
  const useSample = () => {
    const field = Object.keys(sampleInputs)[currentQuestion];
    const samples = sampleInputs[field];
    const randomSample = samples[Math.floor(Math.random() * samples.length)];
    updateBusinessData(field, randomSample);
  };
  
  // Function to go to previous question
  const prevQuestion = () => {
    if (currentQuestion > 0) {
      setCurrentQuestion(currentQuestion - 1);
    }
  };
  
  // Function to go to next question
  const nextQuestion = () => {
    if (currentQuestion < 5) {
      // Update business data with current input
      if (getCurrentValue()) {
        updateBusinessData(Object.keys(businessData)[currentQuestion], getCurrentValue());
      }
      
      // Move to next question
      setCurrentQuestion(currentQuestion + 1);
    } else {
      onComplete();
    }
  };
  
  // Get current field name
  const getCurrentField = () => {
    const fields = ['businessIdea', 'problemSolution', 'valueProposition', 'teamBackground', 'fundingUsage', 'teamCulture'];
    return fields[currentQuestion];
  };
  
  // Get current field value
  const getCurrentValue = () => {
    return businessData[getCurrentField()];
  };
  
  // Current question data
  const currentQuestionData = content.questions[currentQuestion];
  
  return (
    <div className={styles.coachingStage}>
      <h2>{content.heading}</h2>
      
      <div className={styles.questionContainer}>
        <h3 className={styles.questionText}>
          {currentQuestionData.question}
        </h3>
        
        <textarea
          className={styles.inputField}
          placeholder={currentQuestionData.placeholder}
          value={getCurrentValue()}
          onChange={(e) => updateBusinessData(getCurrentField(), e.target.value)}
          rows={5}
        />
        
        <div className={styles.inputActions}>
          <button 
            className={styles.sampleButton}
            onClick={useSample}
          >
            {content.useSampleButton}
          </button>
        </div>
        
        {transcript && (
          <div className={styles.transcriptContainer}>
            <h4>Transcript:</h4>
            <p>{transcript}</p>
            <button 
              className={styles.useTranscriptButton}
              onClick={() => {
                updateBusinessData(getCurrentField(), transcript);
                setTranscript('');
              }}
            >
              Use This Text
            </button>
          </div>
        )}
        
        {getCurrentValue() && (
          <div className={styles.followUp}>
            <p className={styles.followUpText}>
              {currentQuestionData.followUp}
            </p>
          </div>
        )}
      </div>
      
      <div className={styles.navigationButtons}>
        <button 
          className={styles.navButton}
          onClick={prevQuestion}
          disabled={currentQuestion === 0}
        >
          {content.prevButton}
        </button>
        
        {currentQuestion < 5 ? (
          <button 
            className={styles.navButton}
            onClick={nextQuestion}
            disabled={!getCurrentValue()}
          >
            {content.nextButton}
          </button>
        ) : (
          <button 
            className={styles.actionButton}
            onClick={onComplete}
            disabled={!getCurrentValue()}
          >
            {content.continueButton}
          </button>
        )}
      </div>
      
      <button 
        className={styles.skipButton}
        onClick={() => {
          // Set default values if empty
          const fields = ['businessIdea', 'problemSolution', 'valueProposition', 'teamBackground', 'fundingUsage', 'teamCulture'];
          fields.forEach((field, index) => {
            if (!businessData[field]) {
              updateBusinessData(field, sampleInputs[field][0]);
            }
          });
          
          onComplete();
        }}
      >
        {content.skipButton}
      </button>
    </div>
  );
} 