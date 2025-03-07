import React, { useState, useEffect, useRef } from 'react';
import { useAudio } from '../hooks/useAudio';
import { useTypewriter } from '../hooks/useTypewriter';
import { getAnswerForQuestion } from '../utils/responseGenerator';
import styles from '../idea-pitching.module.css';
import { calculateTextDuration, calculateTypewriterSpeed } from '../utils/audioUtils';

// Judges data with real names and titles
const judges = [
  {
    name: "Jeff Bonoz",
    title: "GM of NFTMax Ventures",
    color: "#e74c3c",
    avatar: "/images/judge_1.webp"
  },
  {
    name: "Cabin Zhao",
    title: "Investment Manager of Dinance Venture",
    color: "#9b59b6",
    avatar: "/images/judge_2.webp"
  },
  {
    name: "Sarah Chen",
    title: "Partner at Blockchain Capital",
    color: "#2ecc71",
    avatar: "/images/judge_3.webp"
  }
];

// Random VC names and investor names for the "hands up" prompt
const vcFirms = [
  "Sequoia Capital", "Andreessen Horowitz", "Accel Partners", 
  "Benchmark Capital", "Founders Fund", "Lightspeed Ventures",
  "Greylock Partners", "Kleiner Perkins", "NEA", "Tiger Global"
];

const investorNames = [
  "Sarah", "Michael", "David", "Jennifer", "Robert", "Emily", 
  "James", "Jessica", "Daniel", "Michelle", "Andrew", "Lisa"
];

export default function QAStage({ content, businessData, onComplete }) {
  const [currentJudge, setCurrentJudge] = useState(0);
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [showAnswer, setShowAnswer] = useState(false);
  const [isThinking, setIsThinking] = useState(false);
  const [nextInvestor, setNextInvestor] = useState({ name: "", firm: "" });
  
  const { isPlaying, playAudio, audioRef } = useAudio();
  const { isTyping, displayText, voice, setVoice, startTypewriter } = useTypewriter();
  
  const thinkingTimerRef = useRef(null);
  
  // Judge questions
  const judgeQuestions = [
    [
      "How do you plan to acquire your first 100 customers?",
      "What's your customer acquisition cost and lifetime value?",
      "What makes your solution different from existing alternatives?"
    ],
    [
      "Can you elaborate on your go-to-market strategy?",
      "How scalable is your technical infrastructure?",
      "What are the biggest risks to your business model?"
    ],
    [
      "Tell me more about your team's background and why you're the right people to solve this problem.",
      "What's your revenue model and pricing strategy?",
      "How do you plan to use the investment capital specifically?"
    ]
  ];
  
  // Generate random investor for next question
  const generateNextInvestor = () => {
    const randomName = investorNames[Math.floor(Math.random() * investorNames.length)];
    const randomFirm = vcFirms[Math.floor(Math.random() * vcFirms.length)];
    setNextInvestor({ name: randomName, firm: randomFirm });
  };
  
  // Auto-play first question when component mounts
  useEffect(() => {
    playAudioWithTypewriter(judgeQuestions[currentJudge][currentQuestion], 'judge', currentJudge, currentQuestion);
    generateNextInvestor();
    
    // Auto-answer after question is played
    const questionDuration = calculateTextDuration(judgeQuestions[currentJudge][currentQuestion]);
    thinkingTimerRef.current = setTimeout(() => {
      handleShowAnswer();
    }, (questionDuration * 1000) + 3000); // Question duration + 3s thinking time
    
    return () => {
      if (thinkingTimerRef.current) {
        clearTimeout(thinkingTimerRef.current);
      }
    };
  }, []);
  
  // Function to get the appropriate answer for a question
  const getAnswerKey = (judgeIndex, questionIndex) => {
    const answerMap = {
      '0_0': 'alex_answer_customers',
      '0_1': 'alex_answer_cac_ltv',
      '0_2': 'alex_answer_differentiation',
      '1_0': 'alex_answer_go_to_market',
      '1_1': 'alex_answer_scalability',
      '1_2': 'alex_answer_risks',
      '2_0': 'alex_answer_team',
      '2_1': 'alex_answer_revenue',
      '2_2': 'alex_answer_funding'
    };
    
    return answerMap[`${judgeIndex}_${questionIndex}`] || 'alex_answer_customers';
  };
  
  // Function to show answer
  const handleShowAnswer = () => {
    setIsThinking(false);
    setShowAnswer(true);
    const answer = getAnswerForQuestion(judgeQuestions[currentJudge][currentQuestion], businessData);
    const answerKey = getAnswerKey(currentJudge, currentQuestion);
    
    // Play the answer with typewriter effect
    playAudioWithTypewriter(answer, 'alex', currentJudge, currentQuestion, answerKey);
  };
  
  // Updated function to play audio with typewriter effect
  const playAudioWithTypewriter = (text, voiceType, judgeIndex = 0, questionIndex = 0, answerKey = '') => {
    setVoice(voiceType);
    startTypewriter(text);
    
    if (voiceType === 'alex' && answerKey) {
      // Use the specific answer audio file
      playAudio(text, 'alex', judgeIndex, questionIndex, answerKey);
    } else {
      playAudio(text, voiceType, judgeIndex, questionIndex);
    }
  };
  
  // Function to skip current question/answer
  const handleSkip = () => {
    // Stop any playing audio
    if (audioRef.current) {
      audioRef.current.pause();
    }
    
    // Clear any pending timers
    if (thinkingTimerRef.current) {
      clearTimeout(thinkingTimerRef.current);
    }
    
    // Move to next question or judge
    handleNext();
  };
  
  // Function to move to next question or judge
  const handleNext = () => {
    // Reset state
    setShowAnswer(false);
    setIsThinking(false);
    generateNextInvestor();
    
    // If there are more questions for this judge
    if (currentQuestion < 2) {
      setCurrentQuestion(currentQuestion + 1);
      // Play next question
      setTimeout(() => {
        playAudioWithTypewriter(
          judgeQuestions[currentJudge][currentQuestion + 1], 
          'judge', 
          currentJudge, 
          currentQuestion + 1
        );
        
        // Auto-answer after question is played
        const questionDuration = calculateTextDuration(judgeQuestions[currentJudge][currentQuestion + 1]);
        setIsThinking(true);
        thinkingTimerRef.current = setTimeout(() => {
          handleShowAnswer();
        }, (questionDuration * 1000) + 3000); // Question duration + 3s thinking time
      }, 500);
    } 
    // If there are more judges
    else if (currentJudge < 2) {
      setCurrentJudge(currentJudge + 1);
      setCurrentQuestion(0);
      // Play first question from next judge
      setTimeout(() => {
        playAudioWithTypewriter(
          judgeQuestions[currentJudge + 1][0], 
          'judge', 
          currentJudge + 1, 
          0
        );
        
        // Auto-answer after question is played
        const questionDuration = calculateTextDuration(judgeQuestions[currentJudge + 1][0]);
        setIsThinking(true);
        thinkingTimerRef.current = setTimeout(() => {
          handleShowAnswer();
        }, (questionDuration * 1000) + 3000); // Question duration + 3s thinking time
      }, 500);
    } 
    // If all judges and questions are done
    else {
      onComplete();
    }
  };
  
  // Function to skip all Q&A and go directly to results
  const handleSkipAll = () => {
    // Stop any playing audio
    if (audioRef.current) {
      audioRef.current.pause();
    }
    
    // Clear any pending timers
    if (thinkingTimerRef.current) {
      clearTimeout(thinkingTimerRef.current);
    }
    
    // Go directly to results
    onComplete();
  };
  
  return (
    <div className={styles.qaStage}>
      <h2>{content.heading}</h2>
      
      <div className={styles.skipAllContainer}>
        <button 
          className={styles.skipAllButton}
          onClick={handleSkipAll}
        >
          Skip to Results
        </button>
      </div>
      
      <div className={styles.conversationContainer}>
        <div className={styles.judgeProfile}>
          <div className={styles.judgeAvatar} style={{ backgroundColor: judges[currentJudge].color }}>
            <img 
              src={judges[currentJudge].avatar} 
              alt={judges[currentJudge].name}
              className={styles.avatarImage}
            />
          </div>
          <div className={styles.judgeInfo}>
            <h3>{judges[currentJudge].name}</h3>
            <p>{judges[currentJudge].title}</p>
          </div>
        </div>
        
        <div className={styles.questionBubble}>
          <p className={styles.questionText}>
            {isTyping && voice === 'judge' ? displayText : judgeQuestions[currentJudge][currentQuestion]}
          </p>
        </div>
        
        {isThinking && !showAnswer && (
          <div className={styles.thinkingIndicator}>
            <div className={styles.thinkingDot}></div>
            <div className={styles.thinkingDot}></div>
            <div className={styles.thinkingDot}></div>
            <p>Alex is thinking...</p>
          </div>
        )}
        
        {showAnswer && (
          <div className={styles.answerContainer}>
            <div className={styles.answerBubble}>
              <p className={styles.answerText}>
                {isTyping && voice === 'alex' 
                  ? displayText 
                  : getAnswerForQuestion(judgeQuestions[currentJudge][currentQuestion], businessData)
                }
              </p>
            </div>
            
            <div className={styles.alexProfile}>
              <div className={styles.alexInfo}>
                <h3>Alex</h3>
                <p>AI Co-founder</p>
              </div>
              <div className={styles.alexAvatar}>
                <img 
                  src="/images/alex.webp" 
                  alt="Alex"
                  className={styles.avatarImage}
                />
              </div>
            </div>
          </div>
        )}
      </div>
      
      <div className={styles.qaControlsContainer}>
        {/* Skip current question button - always visible */}
        <button 
          className={styles.skipButton}
          onClick={handleSkip}
        >
          Skip Question
        </button>
        
        {/* Next question button - visible after answer is shown */}
        {showAnswer && !isTyping && !isPlaying && (
          <button 
            className={styles.nextQuestionButton}
            onClick={handleNext}
          >
            {currentJudge < 2 || currentQuestion < 2 ? (
              <>
                <div className={styles.nextInvestorCard}>
                  <div className={styles.wavingHand}>👋</div>
                  <div className={styles.nextInvestorInfo}>
                    <h4>{nextInvestor.name}</h4>
                    <p>{nextInvestor.firm}</p>
                  </div>
                </div>
                <span>has a question</span>
              </>
            ) : (
              content.continueButton
            )}
          </button>
        )}
      </div>
    </div>
  );
} 