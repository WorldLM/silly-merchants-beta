import React from 'react';
import styles from '../idea-pitching.module.css';

export default function ProgressIndicator({ currentStage, stages }) {
  return (
    <div className={styles.progressIndicator}>
      {stages.map((stage, index) => (
        <React.Fragment key={index}>
          <div 
            className={`
              ${styles.progressStep} 
              ${currentStage === stage ? styles.active : ''} 
              ${stages.indexOf(currentStage) > index ? styles.completed : ''}
            `}
          >
            {index + 1}
          </div>
          
          {index < stages.length - 1 && (
            <div className={styles.progressLine}></div>
          )}
        </React.Fragment>
      ))}
    </div>
  );
} 