"use client";

import React, { useState } from 'react';
import Link from 'next/link';
import Image from 'next/image';
import styles from './world.module.css';

export default function WorldPage() {
  const [language, setLanguage] = useState('en');
  
  const content = {
    en: {
      title: "SillyWorld",
      subtitle: "Choose your adventure",
      sillyMerchants: {
        name: "Silly Merchants",
        location: "Grand Bazaar, Istanbul",
        intro: "Guide your AI agent, Marco Polo, as he haggles with the cunning Trader Joe in a high-stakes battle of wits. Outsmart your opponent through a series of unpredictable negotiations and strike the best deals to win the game!",
        entryCost: "Game entry: 10 $W",
        button: "RSVP",
        comingSoon: "coming soon"
      },
      ideaPitching: {
        name: "Idea Pitching",
        location: "Network School, Johor",
        intro: "Train your AI agent to perfect your project pitch, then present it to investors to secure funding and scale your vision.",
        entryCost: "Game entry: 300 $W",
        button: "RSVP",
        comingSoon: "coming soon"
      },
      backButton: "Back to Home"
    },
    zh: {
      title: "潦草世界",
      subtitle: "选择你的冒险",
      sillyMerchants: {
        name: "潦草商人",
        location: "大巴扎，伊斯坦布尔",
        intro: "指导你的AI代理马可·波罗，与狡猾的商人乔商人展开一场斗智斗勇的谈判较量。在一系列扑朔迷离的博弈中，占据上风，达成最佳交易，赢得胜利！",
        entryCost: "游戏入场: 10 $W",
        button: "预约",
        comingSoon: "即将上线"
      },
      ideaPitching: {
        name: "金点子融资",
        location: "网络学院，新山",
        intro: "指导你的AI代理打磨项目想法，并向投资机构进行精彩的路演，成功融资，推动项目发展。",
        entryCost: "游戏入场: 300 $W",
        button: "预约",
        comingSoon: "即将上线"
      },
      backButton: "返回首页"
    }
  };
  
  const toggleLanguage = () => {
    setLanguage(language === 'en' ? 'zh' : 'en');
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
      
      {/* World Map Background */}
      <div className={styles.mapBackground}>
        <Image 
          src="/images/worldmap_v1.webp" 
          alt="World Map" 
          fill 
          priority
          className={styles.mapImage}
        />
        
        {/* Dynamic Overlay */}
        <div className={styles.dynamicOverlay}></div>
      </div>
      
      <div className={styles.content}>
        <h1 className={styles.title}>
          {content[language].title}
        </h1>
        <h2 className={styles.subtitle}>{content[language].subtitle}</h2>
        
        <div className={styles.gameBoxes}>
          {/* Game Box 1: Silly Merchants - Istanbul */}
          <div className={styles.gameBox} style={{ top: '30%', left: '25%' }}>
            <div className={styles.gameBoxInner}>
              <h2 className={styles.gameName}>{content[language].sillyMerchants.name}</h2>
              <p className={styles.gameLocation}>{content[language].sillyMerchants.location}</p>
              <p className={styles.gameIntro}>{content[language].sillyMerchants.intro}</p>
              <p className={styles.entryCost}>{content[language].sillyMerchants.entryCost}</p>
              <a href="https://forms.gle/mYnJNB6bR2RgHf2c8" 
                 target="_blank" 
                 rel="noopener noreferrer" 
                 className={styles.gameButton}>
                {content[language].sillyMerchants.button}
              </a>
              <p className={styles.comingSoon}>{content[language].sillyMerchants.comingSoon}</p>
            </div>
            
            {/* Flying Line to Istanbul */}
            <div className={styles.flyingLine} style={{ 
              top: '100%', 
              left: '50%',
              height: '120px',
              transform: 'rotate(30deg)',
              transformOrigin: 'top left'
            }}>
              <div className={styles.flyingDot}></div>
            </div>
            
            {/* Location Marker for Istanbul */}
            <div className={styles.locationMarker} style={{ 
              top: 'calc(100% + 110px)', 
              left: 'calc(50% + 60px)'
            }}></div>
          </div>
          
          {/* Game Box 2: Idea Pitching - Johor */}
          <div className={styles.gameBox} style={{ top: '60%', left: '65%' }}>
            <div className={styles.gameBoxInner}>
              <h2 className={styles.gameName}>{content[language].ideaPitching.name}</h2>
              <p className={styles.gameLocation}>{content[language].ideaPitching.location}</p>
              <p className={styles.gameIntro}>{content[language].ideaPitching.intro}</p>
              <p className={styles.entryCost}>{content[language].ideaPitching.entryCost}</p>
              <a href="https://forms.gle/mYnJNB6bR2RgHf2c8" 
                 target="_blank" 
                 rel="noopener noreferrer" 
                 className={styles.gameButton}>
                {content[language].ideaPitching.button}
              </a>
              <p className={styles.comingSoon}>{content[language].ideaPitching.comingSoon}</p>
            </div>
            
            {/* Flying Line to Johor */}
            <div className={styles.flyingLine} style={{ 
              top: '100%', 
              left: '50%',
              height: '80px',
              transform: 'rotate(-20deg)',
              transformOrigin: 'top left'
            }}>
              <div className={styles.flyingDot}></div>
            </div>
            
            {/* Location Marker for Johor */}
            <div className={styles.locationMarker} style={{ 
              top: 'calc(100% + 75px)', 
              left: 'calc(50% - 30px)'
            }}></div>
          </div>
        </div>
        
        {/* Back to Home Button */}
        <Link href="/home" className={styles.backButton}>
          {content[language].backButton}
        </Link>
      </div>
    </div>
  );
} 