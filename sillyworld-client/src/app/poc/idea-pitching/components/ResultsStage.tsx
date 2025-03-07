import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useAudio } from '../hooks/useAudio';
import { useTypewriter } from '../hooks/useTypewriter';
import styles from '../idea-pitching.module.css';
import { calculateTextDuration, calculateTypewriterSpeed } from '../utils/audioUtils';

// Judges data with real names and titles - same as in QAStage
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

// Sample feedback responses - including one critical feedback
const judgeFeedback = [
  "I'm genuinely impressed with your innovative approach to solving a real market need. Your metrics are compelling and I can see the potential for rapid growth. What particularly stood out to me was your exceptional team background. However, I'd like to see more detail on your platform defensibility against larger competitors. Overall, I'm excited about your potential and would like to support your journey.",
  
  "I appreciate your enthusiasm, but I'm not convinced this is the right opportunity for our fund. The market you're targeting seems saturated, and your differentiation isn't strong enough to overcome established competitors. Your customer acquisition costs appear unsustainable, and the path to profitability isn't clear. The team lacks experience in this specific domain, which is concerning. I recommend refining your business model and gaining more traction before seeking investment at this level.",
  
  "Thank you for your pitch. I'm impressed by the clarity of your vision and the depth of your understanding of the customer problem. Your unit economics look promising, though I'd want to see more validation of the customer acquisition costs. The team's background is strong, which is crucial for execution. I have some concerns about the timeline to profitability, but overall, I see this as an attractive opportunity with substantial upside potential."
];

// Sample investment offers - including one rejection
const investmentOffers = [
  "$300,000 for 5% equity",
  "No investment offer at this time",
  "$400,000 for 6% equity"
];

export default function ResultsStage({ content, businessData }) {
  const [showingResults, setShowingResults] = useState(false);
  const [currentResultIndex, setCurrentResultIndex] = useState(0);
  const [showConfetti, setShowConfetti] = useState(false);
  const [finalDecision, setFinalDecision] = useState('');
  const [valuation, setValuation] = useState(0);
  const [feedbackComplete, setFeedbackComplete] = useState(false);
  
  const { isPlaying, playAudio } = useAudio();
  const { isTyping, displayText, voice, setVoice, startTypewriter } = useTypewriter();
  
  // Generate judge responses with hardcoded feedback to avoid undefined errors
  const judgeResponses = judges.map((judge, index) => ({
    name: judge.name,
    title: judge.title,
    feedback: judgeFeedback[index],
    investment: investmentOffers[index]
  }));
  
  // Function to play audio with typewriter effect
  const playAudioWithTypewriter = (text, voiceType, judgeIndex = 0) => {
    setVoice(voiceType);
    startTypewriter(text);
    setFeedbackComplete(false);
    
    // Use judge-feedback voice type for feedback
    if (voiceType === 'judge') {
      playAudio(text, 'judge-feedback', judgeIndex);
    } else {
      playAudio(text, voiceType, judgeIndex);
    }
  };
  
  // Auto-play first judge feedback when component mounts
  useEffect(() => {
    setTimeout(() => {
      playAudioWithTypewriter(judgeResponses[0].feedback, 'judge', 0);
    }, 500);
  }, []);
  
  // Set feedback complete when audio and typing finish
  useEffect(() => {
    if (!isTyping && !isPlaying && voice === 'judge') {
      setFeedbackComplete(true);
    }
  }, [isTyping, isPlaying, voice]);
  
  // Function to move to next result or show summary
  const nextStage = () => {
    if (currentResultIndex < 2) {
      setCurrentResultIndex(currentResultIndex + 1);
      setFeedbackComplete(false);
      // Auto-play next judge feedback
      setTimeout(() => {
        playAudioWithTypewriter(judgeResponses[currentResultIndex + 1].feedback, 'judge', currentResultIndex + 1);
      }, 500);
    } else {
      setShowingResults(true);
      calculateValuation();
    }
  };
  
  // Calculate valuation based on inputs
  const calculateValuation = () => {
    // Only count non-rejection offers
    const totalInvestment = judgeResponses.reduce((sum, judge) => {
      if (judge.investment.includes("No investment")) {
        return sum;
      }
      return sum + parseInt(judge.investment.replace(/[^0-9]/g, ''));
    }, 0);
    
    const calculatedValuation = Math.round(
      totalInvestment * (
        (businessData.businessIdea.includes('AI') ? 5 : 
          businessData.businessIdea.includes('blockchain') ? 4 : 
            businessData.businessIdea.includes('platform') ? 4.5 : 3) + 
        (businessData.valueProposition.length > 100 ? 1 : 0) + 
        (businessData.teamBackground.includes('Google') || businessData.teamBackground.includes('Meta') ? 1 : 0)
      ) / 1000000
    ) * 1000000;
    
    setValuation(calculatedValuation);
  };
  
  // Handle final decision
  const handleDecision = (decision) => {
    setFinalDecision(decision);
    
    // Play appropriate audio based on decision
    setTimeout(() => {
      playAudioWithTypewriter(
        decision === 'accept' 
          ? content.acceptMessage 
          : decision === 'negotiate' 
            ? content.negotiateMessage 
            : content.rejectMessage, 
        'system'
      );
    }, 500);
    
    // Show confetti for accept or negotiate
    if (decision === 'accept' || decision === 'negotiate') {
      setShowConfetti(true);
    }
  };
  
  return (
    <div className={styles.resultsStage}>
      <h2>{content.heading}</h2>
      
      {!showingResults ? (
        <div className={styles.feedbackContainer}>
          <div className={styles.judgeProfile}>
            <div className={styles.judgeAvatar} style={{ backgroundColor: judges[currentResultIndex].color }}>
              <img 
                src={judges[currentResultIndex].avatar} 
                alt={judges[currentResultIndex].name}
                className={styles.avatarImage}
              />
            </div>
            <div className={styles.judgeInfo}>
              <h3>{judges[currentResultIndex].name}</h3>
              <p>{judges[currentResultIndex].title}</p>
            </div>
          </div>
          
          <div className={styles.envelopeFeedback}>
            <div className={styles.envelopeHeader}>
              <div className={styles.envelopeIcon}>
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M22 6C22 4.9 21.1 4 20 4H4C2.9 4 2 4.9 2 6V18C2 19.1 2.9 20 4 20H20C21.1 20 22 19.1 22 18V6ZM20 6L12 11L4 6H20ZM20 18H4V8L12 13L20 8V18Z" fill="white"/>
                </svg>
              </div>
              <div className={styles.envelopeTitle}>Investor Feedback</div>
            </div>
            
            <div className={styles.feedbackBubble}>
              <p className={styles.feedbackText}>
                {isTyping && voice === 'judge' ? displayText : judgeResponses[currentResultIndex].feedback}
              </p>
            </div>
            
            <div className={styles.investmentOffer}>
              <p>{content.offerLabel}: 
                <span className={
                  judgeResponses[currentResultIndex].investment.includes("No investment")
                    ? styles.rejectionAmount
                    : styles.investmentAmount
                }>
                  {judgeResponses[currentResultIndex].investment}
                </span>
              </p>
            </div>
          </div>
          
          {feedbackComplete && (
            <button 
              className={styles.nextButton}
              onClick={nextStage}
            >
              {currentResultIndex < 2 ? content.nextFeedbackButton : content.showResultsButton}
            </button>
          )}
        </div>
      ) : (
        <div className={styles.resultsContainer}>
          {finalDecision === '' ? (
            <>
              <div className={styles.valuationContainer}>
                <h3>{content.valuationLabel}</h3>
                <p className={styles.valuationAmount}>${(valuation / 1000000).toFixed(1)}M</p>
                <p className={styles.valuationExplanation}>{content.valuationExplanation}</p>
              </div>
              
              <div className={styles.investmentSummary}>
                <h3>{content.investmentSummaryLabel}</h3>
                <div className={styles.investmentList}>
                  {judgeResponses.map((response, index) => (
                    <div key={index} className={styles.investmentItem}>
                      <div className={styles.judgeAvatar} style={{ backgroundColor: judges[index].color }}>
                        <img 
                          src={judges[index].avatar} 
                          alt={judges[index].name}
                          className={styles.avatarImage}
                        />
                      </div>
                      <div className={styles.judgeInvestmentInfo}>
                        <h4>{judges[index].name}</h4>
                        <p className={
                          response.investment.includes("No investment")
                            ? styles.rejectionAmount
                            : styles.investmentAmount
                        }>
                          {response.investment}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
              
              <div className={styles.decisionPrompt}>
                <h3>{content.decisionPromptLabel}</h3>
                <p>{content.decisionPromptText}</p>
              </div>
              
              <div className={styles.decisionButtons}>
                <button 
                  className={styles.acceptButton}
                  onClick={() => handleDecision('accept')}
                >
                  {content.acceptButton}
                </button>
                <button 
                  className={styles.negotiateButton}
                  onClick={() => handleDecision('negotiate')}
                >
                  {content.negotiateButton}
                </button>
                <button 
                  className={styles.rejectButton}
                  onClick={() => handleDecision('reject')}
                >
                  {content.rejectButton}
                </button>
              </div>
            </>
          ) : (
            <div className={styles.outcomeContainer}>
              <h3 className={styles.outcomeHeading}>
                {finalDecision === 'accept' 
                  ? content.acceptHeading 
                  : finalDecision === 'negotiate' 
                    ? content.negotiateHeading 
                    : content.rejectHeading}
              </h3>
              <p className={styles.outcomeMessage}>
                {isTyping 
                  ? displayText 
                  : finalDecision === 'accept' 
                    ? content.acceptMessage 
                    : finalDecision === 'negotiate' 
                      ? content.negotiateMessage 
                      : content.rejectMessage}
              </p>
              <Link href="/poc" className={styles.returnButton}>
                {content.returnButton}
              </Link>
            </div>
          )}
        </div>
      )}
      
      {showConfetti && (
        <div className={styles.confetti}>
          {/* Confetti animation would go here */}
        </div>
      )}
    </div>
  );
} 