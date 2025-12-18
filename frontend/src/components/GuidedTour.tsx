import React, { useState, useEffect, useCallback } from 'react';
import './GuidedTour.css';

interface TourStep {
  target: string;
  title: string;
  description: string;
  position: 'top' | 'bottom' | 'left' | 'right';
  page: 'setup' | 'tables' | 'workspace';
  scrollTo?: boolean;
  action?: () => void;
}

interface GuidedTourProps {
  isActive: boolean;
  onComplete: () => void;
  onPageChange?: (page: 'setup' | 'tables' | 'workspace') => void;
  currentPage?: 'setup' | 'tables' | 'workspace';
  onSelectBucket?: (bucket: string) => void;
}

const tourSteps: TourStep[] = [
  {
    target: '.s3-location-card',
    title: '1단계: S3 버킷 선택',
    description: '분석할 로그가 저장된 S3 버킷을 선택하세요. 여기서는 S3 Access Logs 버킷을 선택해볼게요.',
    position: 'right',
    page: 'setup'
  },
  {
    target: '.database-config-card',
    title: '2단계: 데이터베이스 설정',
    description: 'Athena 데이터베이스와 테이블 이름이 자동으로 설정됩니다. 필요시 수정할 수 있어요.',
    position: 'left',
    page: 'setup'
  },
  {
    target: '.creation-section',
    title: '3단계: 테이블 생성',
    description: 'Create Table 버튼을 클릭하면 Athena 테이블이 자동으로 생성됩니다.',
    position: 'top',
    page: 'setup',
    scrollTo: true
  },
  {
    target: '.table-management',
    title: '4단계: 테이블 관리',
    description: '생성된 테이블 목록을 확인하고, 분석하기 버튼으로 바로 분석을 시작할 수 있습니다.',
    position: 'bottom',
    page: 'tables',
    scrollTo: true
  },
  {
    target: '.query-input-section, .query-interface',
    title: '5단계: 자연어 로그 분석',
    description: '자연어로 질문하면 AI가 SQL을 생성하고 결과를 보여줍니다. 예: 오늘 에러가 가장 많은 시간대는?',
    position: 'bottom',
    page: 'workspace',
    scrollTo: true
  }
];

export const GuidedTour: React.FC<GuidedTourProps> = ({ 
  isActive, 
  onComplete,
  onPageChange,
  currentPage,
  onSelectBucket
}) => {
  const [currentStep, setCurrentStep] = useState(0); // 바로 첫 단계 시작
  const [targetRect, setTargetRect] = useState<DOMRect | null>(null);
  const [tooltipStyle, setTooltipStyle] = useState<React.CSSProperties>({});
  const [isTransitioning, setIsTransitioning] = useState(false);
  const [showCompletion, setShowCompletion] = useState(false);

  const scrollToElement = useCallback((element: Element) => {
    element.scrollIntoView({ behavior: 'smooth', block: 'center' });
  }, []);

  const updateTargetPosition = useCallback(() => {
    const step = tourSteps[currentStep];
    const element = document.querySelector(step.target);
    
    if (element) {
      if (step.scrollTo) {
        scrollToElement(element);
      }

      // 약간의 딜레이 후 위치 계산 (스크롤 완료 대기)
      setTimeout(() => {
        const rect = element.getBoundingClientRect();
        setTargetRect(rect);
        
        const padding = 20;
        const tooltipHeight = 220; // 예상 툴팁 높이
        const tooltipWidth = 360; // 예상 툴팁 너비
        let style: React.CSSProperties = {};
        
        // 화면 밖으로 나가는지 체크하고 위치 자동 조정
        let position = step.position;
        
        // top 위치가 화면 밖이면 bottom으로 변경
        if (position === 'top' && rect.top - tooltipHeight - padding < 0) {
          position = 'bottom';
        }
        // bottom 위치가 화면 밖이면 top으로 변경
        if (position === 'bottom' && rect.bottom + tooltipHeight + padding > window.innerHeight) {
          position = 'top';
        }
        
        // 항상 화면 안에 표시되도록 계산
        const minTop = 100; // 헤더 아래
        const maxTop = window.innerHeight - tooltipHeight - 100; // 하단 여백
        
        switch (position) {
          case 'top':
            style = {
              left: Math.max(tooltipWidth / 2, Math.min(rect.left + rect.width / 2, window.innerWidth - tooltipWidth / 2)),
              top: Math.max(minTop, Math.min(rect.top - padding - tooltipHeight, maxTop)),
              transform: 'translate(-50%, 0)'
            };
            break;
          case 'bottom':
            style = {
              left: Math.max(tooltipWidth / 2, Math.min(rect.left + rect.width / 2, window.innerWidth - tooltipWidth / 2)),
              top: Math.max(minTop, Math.min(rect.bottom + padding, maxTop)),
              transform: 'translate(-50%, 0)'
            };
            break;
          case 'left':
            style = {
              left: Math.max(tooltipWidth + padding, rect.left - padding),
              top: Math.max(minTop, Math.min(rect.top + rect.height / 2 - tooltipHeight / 2, maxTop)),
              transform: 'translate(-100%, 0)'
            };
            break;
          case 'right':
            style = {
              left: Math.min(rect.right + padding, window.innerWidth - tooltipWidth - padding),
              top: Math.max(minTop, Math.min(rect.top + rect.height / 2 - tooltipHeight / 2, maxTop)),
              transform: 'translate(0, 0)'
            };
            break;
        }
        
        setTooltipStyle(style);
      }, step.scrollTo ? 300 : 50);
    } else {
      setTargetRect(null);
    }
  }, [currentStep, scrollToElement]);

  // 투어 시작 시 바로 첫 단계로
  useEffect(() => {
    if (isActive) {
      setCurrentStep(0);
      setShowCompletion(false);
      // 첫 페이지로 이동
      const firstStep = tourSteps[0];
      if (firstStep.page !== currentPage && onPageChange) {
        onPageChange(firstStep.page);
      }
      // DOM 준비 후 위치 업데이트
      setTimeout(() => {
        updateTargetPosition();
      }, 800);
    }
  }, [isActive]);

  // 투어 시작 시 S3 버킷 자동 선택
  useEffect(() => {
    if (isActive && currentStep === 0 && onSelectBucket) {
      // 첫 번째 S3 버킷 자동 선택
      setTimeout(() => {
        onSelectBucket('1.s3-access-logs-777786711649');
      }, 500);
    }
  }, [isActive, currentStep, onSelectBucket]);

  // 스텝 변경 시 페이지 이동 및 위치 업데이트
  useEffect(() => {
    if (!isActive || currentStep < 0 || showCompletion) return;

    const step = tourSteps[currentStep];
    
    if (step.page !== currentPage && onPageChange) {
      setIsTransitioning(true);
      onPageChange(step.page);
      
      setTimeout(() => {
        updateTargetPosition();
        setIsTransitioning(false);
      }, 400);
    } else {
      updateTargetPosition();
    }
  }, [currentStep, isActive, currentPage, onPageChange, updateTargetPosition, showCompletion]);

  // 리사이즈/스크롤 이벤트
  useEffect(() => {
    if (!isActive) return;
    
    const handleUpdate = () => {
      if (!isTransitioning) {
        updateTargetPosition();
      }
    };
    
    window.addEventListener('resize', handleUpdate);
    window.addEventListener('scroll', handleUpdate, true);
    
    return () => {
      window.removeEventListener('resize', handleUpdate);
      window.removeEventListener('scroll', handleUpdate, true);
    };
  }, [isActive, isTransitioning, updateTargetPosition]);

  // 투어 시작 시 첫 페이지로 이동
  useEffect(() => {
    if (isActive && currentStep === 0) {
      const firstStep = tourSteps[0];
      if (firstStep.page !== currentPage && onPageChange) {
        onPageChange(firstStep.page);
      }
      setTimeout(updateTargetPosition, 500);
    }
  }, [isActive]);

  const handleNext = () => {
    if (currentStep < tourSteps.length - 1) {
      setCurrentStep(currentStep + 1);
    } else {
      setShowCompletion(true);
    }
  };

  const handlePrev = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleComplete = () => {
    setCurrentStep(0);
    setShowCompletion(false);
    if (onPageChange) {
      onPageChange('setup');
    }
    onComplete();
  };

  const handleSkip = () => {
    handleComplete();
  };

  if (!isActive) return null;
  
  if (isTransitioning) {
    return (
      <div className="guided-tour-overlay">
        <div className="tour-loading">페이지 이동 중...</div>
      </div>
    );
  }

  // 완료 화면
  if (showCompletion) {
    return (
      <div className="guided-tour-overlay">
        <div className="tour-intro-card tour-completion-card">
          <div className="tour-intro-icon">🎉</div>
          <h2 className="tour-intro-title">가이드 완료!</h2>
          <p className="tour-intro-description">
            이제 Gen-AI Log Analyzer를 사용할 준비가 되었어요!<br />
            자연어로 질문하면 AI가 로그를 분석해드립니다.<br />
            궁금한 점이 있으면 언제든 다시 가이드를 실행하세요.
          </p>
          <div className="tour-intro-actions">
            <button className="tour-btn tour-btn-primary" onClick={handleComplete}>
              시작하기 🚀
            </button>
          </div>
        </div>
      </div>
    );
  }

  const step = tourSteps[currentStep];

  return (
    <div className="guided-tour-overlay">
      {targetRect && targetRect.width > 0 && targetRect.height > 0 && (
        <div 
          className="tour-spotlight"
          style={{
            top: targetRect.top - 12,
            left: targetRect.left - 12,
            width: targetRect.width + 24,
            height: targetRect.height + 24,
          }}
        />
      )}
      
      {targetRect && (
        <div className="tour-tooltip" style={tooltipStyle}>
          <div className={`tooltip-arrow tooltip-arrow-${step.position}`} />
          <div className="tooltip-content">
            <div className="tooltip-header">
              <span className="tooltip-step">{currentStep + 1} / {tourSteps.length}</span>
              <button className="tooltip-close" onClick={handleSkip}>×</button>
            </div>
            <h3 className="tooltip-title">{step.title}</h3>
            <p className="tooltip-description">{step.description}</p>
            <div className="tooltip-actions">
              {currentStep > 0 && (
                <button className="tour-btn tour-btn-secondary" onClick={handlePrev}>
                  ← 이전
                </button>
              )}
              <button className="tour-btn tour-btn-skip" onClick={handleSkip}>
                건너뛰기
              </button>
              <button className="tour-btn tour-btn-primary" onClick={handleNext}>
                {currentStep === tourSteps.length - 1 ? '완료' : '다음 →'}
              </button>
            </div>
          </div>
        </div>
      )}

      <div className="tour-progress">
        {tourSteps.map((s, idx) => (
          <div 
            key={idx} 
            className={`progress-dot ${idx === currentStep ? 'active' : ''} ${idx < currentStep ? 'completed' : ''}`}
            title={s.title}
          />
        ))}
      </div>
    </div>
  );
};

export default GuidedTour;
