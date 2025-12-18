import React from 'react';
import { Sun, Moon } from 'lucide-react';
import { useTheme } from '../contexts/ThemeContext';
import './ThemeToggle.css';

export const ThemeToggle: React.FC = () => {
  const { theme, setTheme, resolvedTheme } = useTheme();

  const handleToggle = () => {
    // 라이트와 다크 모드만 토글
    const newTheme = resolvedTheme === 'dark' ? 'light' : 'dark';
    setTheme(newTheme);
  };

  const getCurrentIcon = () => {
    return resolvedTheme === 'dark' ? Moon : Sun;
  };

  const getCurrentLabel = () => {
    return resolvedTheme === 'dark' ? '다크 모드' : '라이트 모드';
  };

  const getNextLabel = () => {
    return resolvedTheme === 'dark' ? '라이트 모드로 변경' : '다크 모드로 변경';
  };

  const CurrentIcon = getCurrentIcon();

  return (
    <div className="theme-toggle">
      <button
        className="theme-toggle-button"
        onClick={handleToggle}
        aria-label={`현재: ${getCurrentLabel()}. ${getNextLabel()}. 키보드 단축키: Ctrl+Shift+T`}
        title={`${getCurrentLabel()} (클릭하여 ${getNextLabel()})`}
      >
        <CurrentIcon size={20} aria-hidden="true" />
        <span className="theme-indicator" data-theme={resolvedTheme} aria-hidden="true">
          {resolvedTheme === 'dark' ? '🌙' : '☀️'}
        </span>
        <span className="sr-only">
          {getCurrentLabel()}
        </span>
      </button>
    </div>
  );
};