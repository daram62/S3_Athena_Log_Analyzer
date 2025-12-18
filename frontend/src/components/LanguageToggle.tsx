import React from 'react';
import { useLanguage } from '../contexts/LanguageContext';
import './LanguageToggle.css';

export const LanguageToggle: React.FC = () => {
  const { language, setLanguage } = useLanguage();

  const toggleLanguage = () => {
    setLanguage(language === 'ko' ? 'en' : 'ko');
  };

  return (
    <button
      className={`language-toggle ${language}`}
      onClick={toggleLanguage}
      aria-label={`Switch to ${language === 'ko' ? 'English' : '한국어'}`}
      title={`Switch to ${language === 'ko' ? 'English' : '한국어'}`}
    >
      <div className="language-toggle-track">
        <div className="language-toggle-thumb">
          <span className="language-text">
            {language === 'ko' ? '한' : 'EN'}
          </span>
        </div>
        <div className="language-options">
          <span className={`language-option ${language === 'ko' ? 'active' : ''}`}>한</span>
          <span className={`language-option ${language === 'en' ? 'active' : ''}`}>EN</span>
        </div>
      </div>
    </button>
  );
};