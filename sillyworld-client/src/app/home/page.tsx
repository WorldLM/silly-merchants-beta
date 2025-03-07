"use client";

import React, { useState } from 'react';
import Link from 'next/link';
import Image from 'next/image';
import styles from './home.module.css';

export default function HomePage() {
  const [language, setLanguage] = useState('en');
  
  const content = {
    en: {
      title: "SillyWorld LM",
      subtitle: "Build your AI game agentic empire ventures.",
      startButton: "START BUILD",
      contactUs: "Contact Us",
      email: "Email: game@nsns.world",
      copyright: `© ${new Date().getFullYear()} SillyWorld. All rights reserved.`
    },
    zh: {
      title: "潦草世界 LM",
      subtitle: "构建你的AI游戏代理帝国冒险。",
      startButton: "开始建造",
      contactUs: "联系我们",
      email: "邮箱: game@nsns.world",
      copyright: `© ${new Date().getFullYear()} 潦草世界。版权所有。`
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
      
      {/* World Map Section */}
      <section className={styles.worldMapSection}>
        <div className={styles.mapBackground}>
          {/* World Map Background Image */}
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
        
        <div className={styles.contentContainer}>
          <h1 className={styles.title}>{content[language].title}</h1>
          <h2 className={styles.subtitle}>{content[language].subtitle}</h2>
          
          <Link href="/world" className={styles.startButton}>
            {content[language].startButton}
          </Link>
        </div>
      </section>
      
      {/* Footer Section */}
      <footer className={styles.footer}>
        <div className={styles.footerContent}>
          <div className={styles.footerSection}>
            <h3>{content[language].contactUs}</h3>
            <p>{content[language].email}</p>
          </div>
        </div>
        
        <div className={styles.copyright}>
          {content[language].copyright}
        </div>
      </footer>
    </div>
  );
} 