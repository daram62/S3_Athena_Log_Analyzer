/**
 * 접근성 테스트 유틸리티
 * WCAG 2.1 AA 준수 확인을 위한 테스트 함수들
 */

interface ColorContrastResult {
  ratio: number;
  level: 'AAA' | 'AA' | 'FAIL';
  passes: boolean;
}

interface AccessibilityTestResult {
  colorContrast: ColorContrastResult[];
  focusManagement: boolean;
  keyboardNavigation: boolean;
  screenReaderSupport: boolean;
  touchTargets: boolean;
  errors: string[];
  warnings: string[];
}

/**
 * 색상 대비 비율 계산 (WCAG 기준)
 */
export function calculateColorContrast(foreground: string, background: string): ColorContrastResult {
  // RGB 값을 0-1 범위로 변환
  const getRGB = (color: string) => {
    const hex = color.replace('#', '');
    const r = parseInt(hex.substr(0, 2), 16) / 255;
    const g = parseInt(hex.substr(2, 2), 16) / 255;
    const b = parseInt(hex.substr(4, 2), 16) / 255;
    return { r, g, b };
  };

  // 상대 휘도 계산
  const getLuminance = (rgb: { r: number; g: number; b: number }) => {
    const { r, g, b } = rgb;
    const [rs, gs, bs] = [r, g, b].map(c => {
      return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
    });
    return 0.2126 * rs + 0.7152 * gs + 0.0722 * bs;
  };

  const fgRGB = getRGB(foreground);
  const bgRGB = getRGB(background);
  
  const fgLuminance = getLuminance(fgRGB);
  const bgLuminance = getLuminance(bgRGB);
  
  const lighter = Math.max(fgLuminance, bgLuminance);
  const darker = Math.min(fgLuminance, bgLuminance);
  
  const ratio = (lighter + 0.05) / (darker + 0.05);
  
  let level: 'AAA' | 'AA' | 'FAIL';
  let passes: boolean;
  
  if (ratio >= 7) {
    level = 'AAA';
    passes = true;
  } else if (ratio >= 4.5) {
    level = 'AA';
    passes = true;
  } else {
    level = 'FAIL';
    passes = false;
  }
  
  return { ratio, level, passes };
}

/**
 * 테마 색상 대비 테스트
 */
export function testThemeColorContrast(): ColorContrastResult[] {
  const results: ColorContrastResult[] = [];
  
  // 다크 테마 색상 테스트
  const darkThemeTests = [
    { name: 'Dark: Primary text on primary bg', fg: '#ffffff', bg: '#121212' },
    { name: 'Dark: Secondary text on primary bg', fg: '#e0e0e0', bg: '#121212' },
    { name: 'Dark: Muted text on primary bg', fg: '#a0a0a0', bg: '#121212' },
    { name: 'Dark: Primary text on secondary bg', fg: '#ffffff', bg: '#1e1e1e' },
    { name: 'Dark: Button text on accent', fg: '#ffffff', bg: '#ff5252' },
  ];
  
  // 라이트 테마 색상 테스트
  const lightThemeTests = [
    { name: 'Light: Primary text on primary bg', fg: '#212121', bg: '#ffffff' },
    { name: 'Light: Secondary text on primary bg', fg: '#424242', bg: '#ffffff' },
    { name: 'Light: Muted text on primary bg', fg: '#757575', bg: '#ffffff' },
    { name: 'Light: Primary text on secondary bg', fg: '#212121', bg: '#f5f5f5' },
    { name: 'Light: Button text on accent', fg: '#ffffff', bg: '#d32f2f' },
  ];
  
  [...darkThemeTests, ...lightThemeTests].forEach(test => {
    const result = calculateColorContrast(test.fg, test.bg);
    results.push({
      ...result,
      name: test.name
    } as ColorContrastResult & { name: string });
  });
  
  return results;
}

/**
 * 포커스 관리 테스트
 */
export function testFocusManagement(): boolean {
  const focusableElements = document.querySelectorAll(
    'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
  );
  
  let allHaveFocusStyles = true;
  
  focusableElements.forEach(element => {
    const styles = window.getComputedStyle(element, ':focus-visible');
    const hasOutline = styles.outline !== 'none' && styles.outline !== '';
    const hasBoxShadow = styles.boxShadow !== 'none' && styles.boxShadow !== '';
    
    if (!hasOutline && !hasBoxShadow) {
      allHaveFocusStyles = false;
      console.warn('Element lacks focus styles:', element);
    }
  });
  
  return allHaveFocusStyles;
}

/**
 * 키보드 네비게이션 테스트
 */
export function testKeyboardNavigation(): boolean {
  const interactiveElements = document.querySelectorAll(
    'button, [role="button"], input, select, textarea, a[href]'
  );
  
  let allAccessible = true;
  
  interactiveElements.forEach(element => {
    const tabIndex = element.getAttribute('tabindex');
    const isHidden = element.getAttribute('aria-hidden') === 'true';
    const isDisabled = element.hasAttribute('disabled') || 
                      element.getAttribute('aria-disabled') === 'true';
    
    // 숨겨지거나 비활성화된 요소가 아닌데 tabindex가 -1이면 문제
    if (!isHidden && !isDisabled && tabIndex === '-1') {
      allAccessible = false;
      console.warn('Interactive element not keyboard accessible:', element);
    }
  });
  
  return allAccessible;
}

/**
 * 스크린 리더 지원 테스트
 */
export function testScreenReaderSupport(): boolean {
  const errors: string[] = [];
  
  // 이미지에 alt 속성 확인
  const images = document.querySelectorAll('img');
  images.forEach(img => {
    if (!img.hasAttribute('alt')) {
      errors.push(`Image missing alt attribute: ${img.src}`);
    }
  });
  
  // 버튼에 접근 가능한 이름 확인
  const buttons = document.querySelectorAll('button, [role="button"]');
  buttons.forEach(button => {
    const hasText = button.textContent?.trim();
    const hasAriaLabel = button.hasAttribute('aria-label');
    const hasAriaLabelledby = button.hasAttribute('aria-labelledby');
    
    if (!hasText && !hasAriaLabel && !hasAriaLabelledby) {
      errors.push('Button lacks accessible name');
    }
  });
  
  // 폼 컨트롤에 레이블 확인
  const formControls = document.querySelectorAll('input, select, textarea');
  formControls.forEach(control => {
    const id = control.id;
    const hasLabel = id && document.querySelector(`label[for="${id}"]`);
    const hasAriaLabel = control.hasAttribute('aria-label');
    const hasAriaLabelledby = control.hasAttribute('aria-labelledby');
    
    if (!hasLabel && !hasAriaLabel && !hasAriaLabelledby) {
      errors.push('Form control lacks label');
    }
  });
  
  return errors.length === 0;
}

/**
 * 터치 타겟 크기 테스트 (최소 44x44px)
 */
export function testTouchTargets(): boolean {
  const interactiveElements = document.querySelectorAll(
    'button, [role="button"], input[type="button"], input[type="submit"], a[href]'
  );
  
  let allMeetMinimumSize = true;
  
  interactiveElements.forEach(element => {
    const rect = element.getBoundingClientRect();
    const minSize = window.innerWidth <= 768 ? 48 : 44; // 모바일에서는 48px
    
    if (rect.width < minSize || rect.height < minSize) {
      allMeetMinimumSize = false;
      console.warn(`Touch target too small (${rect.width}x${rect.height}):`, element);
    }
  });
  
  return allMeetMinimumSize;
}

/**
 * 종합 접근성 테스트 실행
 */
export function runAccessibilityTest(): AccessibilityTestResult {
  const errors: string[] = [];
  const warnings: string[] = [];
  
  try {
    const colorContrast = testThemeColorContrast();
    const focusManagement = testFocusManagement();
    const keyboardNavigation = testKeyboardNavigation();
    const screenReaderSupport = testScreenReaderSupport();
    const touchTargets = testTouchTargets();
    
    // 실패한 색상 대비 테스트 수집
    colorContrast.forEach(result => {
      if (!result.passes) {
        errors.push(`Color contrast failure: ${(result as any).name} (ratio: ${result.ratio.toFixed(2)})`);
      } else if (result.level === 'AA') {
        warnings.push(`Color contrast warning: ${(result as any).name} meets AA but not AAA (ratio: ${result.ratio.toFixed(2)})`);
      }
    });
    
    return {
      colorContrast,
      focusManagement,
      keyboardNavigation,
      screenReaderSupport,
      touchTargets,
      errors,
      warnings
    };
  } catch (error) {
    errors.push(`Test execution error: ${error}`);
    
    return {
      colorContrast: [],
      focusManagement: false,
      keyboardNavigation: false,
      screenReaderSupport: false,
      touchTargets: false,
      errors,
      warnings
    };
  }
}

/**
 * 접근성 테스트 결과를 콘솔에 출력
 */
export function logAccessibilityTestResults(results: AccessibilityTestResult): void {
  console.group('🔍 접근성 테스트 결과');
  
  console.log('✅ 색상 대비:', results.colorContrast.filter(r => r.passes).length, '/', results.colorContrast.length, '통과');
  console.log('✅ 포커스 관리:', results.focusManagement ? '통과' : '실패');
  console.log('✅ 키보드 네비게이션:', results.keyboardNavigation ? '통과' : '실패');
  console.log('✅ 스크린 리더 지원:', results.screenReaderSupport ? '통과' : '실패');
  console.log('✅ 터치 타겟 크기:', results.touchTargets ? '통과' : '실패');
  
  if (results.errors.length > 0) {
    console.group('❌ 오류');
    results.errors.forEach(error => console.error(error));
    console.groupEnd();
  }
  
  if (results.warnings.length > 0) {
    console.group('⚠️ 경고');
    results.warnings.forEach(warning => console.warn(warning));
    console.groupEnd();
  }
  
  console.groupEnd();
}

// 개발 모드에서 자동 테스트 실행
if (process.env.NODE_ENV === 'development') {
  // DOM이 로드된 후 테스트 실행
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
      setTimeout(() => {
        const results = runAccessibilityTest();
        logAccessibilityTestResults(results);
      }, 1000);
    });
  } else {
    setTimeout(() => {
      const results = runAccessibilityTest();
      logAccessibilityTestResults(results);
    }, 1000);
  }
}