import React from 'react';
import styles from '../idea-pitching.module.css';

export default function WelcomeStage({ content, onStart }) {
  return (
    <div className={styles.welcomeStage}>
      <h2>{content.heading}</h2>
      <p className={styles.description}>{content.description}</p>
      
      <div className={styles.flowChartContainer}>
        <div className={styles.flowChartTitle}>{content.processTitle}</div>
        
        <div className={styles.flowChart}>
          <div className={styles.flowStep}>
            <div className={styles.flowStepNumber}>1</div>
            <div className={styles.flowStepContent}>
              <h3>Coaching Session</h3>
              <p>Work with Alex to prepare your pitch by answering key questions about your business idea.</p>
              <div className={styles.flowStepIcon}>
                <svg width="40" height="40" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M12 16C14.2091 16 16 14.2091 16 12C16 9.79086 14.2091 8 12 8C9.79086 8 8 9.79086 8 12C8 14.2091 9.79086 16 12 16Z" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                  <path d="M3 16V8C3 5.23858 5.23858 3 8 3H16C18.7614 3 21 5.23858 21 8V16C21 18.7614 18.7614 21 16 21H8C5.23858 21 3 18.7614 3 16Z" stroke="white" strokeWidth="2"/>
                </svg>
              </div>
            </div>
          </div>
          
          <div className={styles.flowArrow}>→</div>
          
          <div className={styles.flowStep}>
            <div className={styles.flowStepNumber}>2</div>
            <div className={styles.flowStepContent}>
              <h3>Demo Day</h3>
              <p>Deliver your pitch to a panel of venture capital investors with Alex as your spokesperson.</p>
              <div className={styles.flowStepIcon}>
                <svg width="40" height="40" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M12 8V16M8 12H16M22 12C22 17.5228 17.5228 22 12 22C6.47715 22 2 17.5228 2 12C2 6.47715 6.47715 2 12 2C17.5228 2 22 6.47715 22 12Z" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              </div>
            </div>
          </div>
          
          <div className={styles.flowArrow}>→</div>
          
          <div className={styles.flowStep}>
            <div className={styles.flowStepNumber}>3</div>
            <div className={styles.flowStepContent}>
              <h3>Q&A Session</h3>
              <p>Answer challenging questions from investors to defend your business model and vision.</p>
              <div className={styles.flowStepIcon}>
                <svg width="40" height="40" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M8 10H8.01M12 10H12.01M16 10H16.01M9 16H5C3.89543 16 3 15.1046 3 14V6C3 4.89543 3.89543 4 5 4H19C20.1046 4 21 4.89543 21 6V14C21 15.1046 20.1046 16 19 16H14L9 21V16Z" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              </div>
            </div>
          </div>
          
          <div className={styles.flowArrow}>→</div>
          
          <div className={styles.flowStep}>
            <div className={styles.flowStepNumber}>4</div>
            <div className={styles.flowStepContent}>
              <h3>Investment Decision</h3>
              <p>Receive feedback and investment offers from the judges, then decide how to proceed.</p>
              <div className={styles.flowStepIcon}>
                <svg width="40" height="40" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M12 8V12M12 16H12.01M22 12C22 17.5228 17.5228 22 12 22C6.47715 22 2 17.5228 2 12C2 6.47715 6.47715 2 12 2C17.5228 2 22 6.47715 22 12Z" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <button 
        className={styles.actionButton}
        onClick={onStart}
      >
        {content.startButton}
      </button>
    </div>
  );
} 