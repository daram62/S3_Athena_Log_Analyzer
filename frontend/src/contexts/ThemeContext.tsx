import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';

type Theme = 'light' | 'dark';

interface ThemeContextType {
  theme: Theme;
  setTheme: (theme: Theme) => void;
  resolvedTheme: 'light' | 'dark';
  toggleTheme: () => void;
  announceThemeChange: (theme: Theme) => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
};

interface ThemeProviderProps {
  children: React.ReactNode;
}

export const ThemeProvider: React.FC<ThemeProviderProps> = ({ children }) => {
  const [theme, setTheme] = useState<Theme>(() => {
    // 로컬 스토리지에서 저장된 테마 불러오기, 없으면 시스템 설정 확인
    const savedTheme = localStorage.getItem('theme') as Theme;
    if (savedTheme === 'light' || savedTheme === 'dark') {
      return savedTheme;
    }
    
    // 시스템 설정 확인
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    return mediaQuery.matches ? 'dark' : 'light';
  });

  // 접근성을 위한 테마 변경 알림 함수
  const announceThemeChange = useCallback((newTheme: Theme) => {
    const announcement = document.createElement('div');
    announcement.setAttribute('aria-live', 'polite');
    announcement.setAttribute('aria-atomic', 'true');
    announcement.className = 'sr-only';
    
    const themeNames = {
      light: '라이트 모드',
      dark: '다크 모드'
    };
    
    announcement.textContent = `테마가 ${themeNames[newTheme]}로 변경되었습니다.`;
    document.body.appendChild(announcement);
    
    // 2초 후 제거
    setTimeout(() => {
      if (document.body.contains(announcement)) {
        document.body.removeChild(announcement);
      }
    }, 2000);
  }, []);

  // 테마 토글 함수 (키보드 단축키용)
  const toggleTheme = useCallback(() => {
    const newTheme = theme === 'dark' ? 'light' : 'dark';
    setTheme(newTheme);
    announceThemeChange(newTheme);
  }, [theme, announceThemeChange]);

  // 테마 변경 시 처리
  useEffect(() => {
    // 로컬 스토리지에 저장
    try {
      localStorage.setItem('theme', theme);
    } catch (error) {
      console.warn('Failed to save theme to localStorage:', error);
    }
  }, [theme]);

  // DOM에 테마 적용 및 접근성 속성 설정
  useEffect(() => {
    const root = document.documentElement;
    root.setAttribute('data-theme', theme);
    
    // 색상 구성표 메타 태그 업데이트
    let colorSchemeTag = document.querySelector('meta[name="color-scheme"]');
    if (!colorSchemeTag) {
      colorSchemeTag = document.createElement('meta');
      colorSchemeTag.setAttribute('name', 'color-scheme');
      document.head.appendChild(colorSchemeTag);
    }
    colorSchemeTag.setAttribute('content', theme);

    // 테마 색상 메타 태그 업데이트
    let themeColorTag = document.querySelector('meta[name="theme-color"]');
    if (!themeColorTag) {
      themeColorTag = document.createElement('meta');
      themeColorTag.setAttribute('name', 'theme-color');
      document.head.appendChild(themeColorTag);
    }
    
    const themeColor = theme === 'dark' ? '#121212' : '#ffffff';
    themeColorTag.setAttribute('content', themeColor);
  }, [theme]);

  // 키보드 단축키 등록 (Ctrl/Cmd + Shift + T)
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if ((event.ctrlKey || event.metaKey) && event.shiftKey && event.key === 'T') {
        event.preventDefault();
        toggleTheme();
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [toggleTheme]);

  const handleSetTheme = useCallback((newTheme: Theme) => {
    setTheme(newTheme);
    announceThemeChange(newTheme);
  }, [announceThemeChange]);

  const value = {
    theme,
    setTheme: handleSetTheme,
    resolvedTheme: theme, // 이제 theme과 resolvedTheme이 같음
    toggleTheme,
    announceThemeChange,
  };

  return (
    <ThemeContext.Provider value={value}>
      {children}
    </ThemeContext.Provider>
  );
};