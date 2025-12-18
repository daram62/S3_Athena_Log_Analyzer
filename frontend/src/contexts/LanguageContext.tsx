import React, { createContext, useContext, useState, useEffect } from 'react';

type Language = 'ko' | 'en';

interface LanguageContextType {
  language: Language;
  setLanguage: (language: Language) => void;
  t: (key: string) => string;
}

const LanguageContext = createContext<LanguageContextType | undefined>(undefined);

// 번역 데이터
const translations = {
  ko: {
    // 메인 타이틀
    'app.title': 'S3-Athena Log Analyzer',
    'header.subtitle': 'S3 로그를 Athena에서 자동으로 분석합니다',
    'app.subtitle': 'S3에 저장된 로그 파일을 자동으로 분석하고 Athena 테이블을 생성합니다. 복잡한 설정 없이 몇 번의 클릭만으로 로그 분석을 시작할 수 있습니다.',
    
    // 단계
    'step.s3.selection': 'S3 버킷 선택',
    'step.log.verification': '로그 검증',
    'step.table.creation': '테이블 생성',
    
    // 카드 제목
    'card.s3.location': 'S3 Log Location',
    'card.database.config': 'Database Configuration',
    
    // 폼 라벨
    'form.database.name': 'Database Name',
    'form.table.name': 'Table Name',
    
    // 버튼
    'button.create.database': 'Create Database & Table',
    'button.start.querying': 'Start Querying',
    'button.try.ai': 'Try AI Analysis',
    'button.close': 'Close',
    'button.retry': 'Retry Creation',
    
    // 상태 메시지
    'status.aws.checking': 'AWS 연결 상태를 확인하고 있습니다...',
    'status.aws.connection.required': 'AWS 연결이 필요합니다',
    'status.aws.connection.description': 'AWS 자격 증명을 설정하고 다시 시도해주세요. SSO 로그인 또는 AWS CLI 설정이 필요합니다.',
    'button.aws.guide': 'AWS 설정 가이드 보기',
    
    // 모달
    'modal.creation.complete': 'Creation Complete!',
    'modal.creation.failed': 'Creation Failed',
    'modal.creating': 'Creating Database & Table',
    'modal.created.resources': 'Created Resources',
    'modal.next.steps': 'Next Steps',
    'modal.athena.ready': 'Your Athena table is ready! You can now:',
    'modal.query.console': 'Query your logs using the Athena console',
    'modal.ai.interface': 'Use natural language queries in our AI interface',
    'modal.automated.analysis': 'Set up automated analysis and monitoring',
    
    // 생성 단계
    'creation.database': 'Creating Database',
    'creation.table': 'Creating Table Schema',
    'creation.partitions': 'Setting up Partitions',
    'creation.validation': 'Validating Setup',
    
    // 완료 섹션
    'completion.title': 'Setup Complete!',
    'completion.description': 'Your Athena table has been successfully created and is ready for querying. You can now start analyzing your logs with powerful SQL queries or our AI-powered interface.',
    
    // 도움말
    'help.select.s3': '• S3 위치를 선택해주세요',
    'help.complete.database': '• 데이터베이스 설정을 완료해주세요',
    'help.complete.verification': '• 로그 검증을 완료해주세요',
    
    // 폼 플레이스홀더
    'placeholder.database.name': '데이터베이스 이름을 입력하세요',
    'placeholder.table.name': '테이블 이름을 입력하세요'
  },
  en: {
    // 메인 타이틀
    'app.title': 'S3-Athena Log Analyzer',
    'header.subtitle': 'Automatically analyze S3 logs with Athena',
    'app.subtitle': 'Automatically analyze log files stored in S3 and create Athena tables. Start log analysis with just a few clicks without complex setup.',
    
    // 단계
    'step.s3.selection': 'S3 Bucket Selection',
    'step.log.verification': 'Log Verification',
    'step.table.creation': 'Table Creation',
    
    // 카드 제목
    'card.s3.location': 'S3 Log Location',
    'card.database.config': 'Database Configuration',
    
    // 폼 라벨
    'form.database.name': 'Database Name',
    'form.table.name': 'Table Name',
    
    // 버튼
    'button.create.database': 'Create Database & Table',
    'button.start.querying': 'Start Querying',
    'button.try.ai': 'Try AI Analysis',
    'button.close': 'Close',
    'button.retry': 'Retry Creation',
    
    // 상태 메시지
    'status.aws.checking': 'Checking AWS connection status...',
    'status.aws.connection.required': 'AWS Connection Required',
    'status.aws.connection.description': 'Please set up AWS credentials and try again. SSO login or AWS CLI configuration is required.',
    'button.aws.guide': 'View AWS Setup Guide',
    
    // 모달
    'modal.creation.complete': 'Creation Complete!',
    'modal.creation.failed': 'Creation Failed',
    'modal.creating': 'Creating Database & Table',
    'modal.created.resources': 'Created Resources',
    'modal.next.steps': 'Next Steps',
    'modal.athena.ready': 'Your Athena table is ready! You can now:',
    'modal.query.console': 'Query your logs using the Athena console',
    'modal.ai.interface': 'Use natural language queries in our AI interface',
    'modal.automated.analysis': 'Set up automated analysis and monitoring',
    
    // 생성 단계
    'creation.database': 'Creating Database',
    'creation.table': 'Creating Table Schema',
    'creation.partitions': 'Setting up Partitions',
    'creation.validation': 'Validating Setup',
    
    // 완료 섹션
    'completion.title': 'Setup Complete!',
    'completion.description': 'Your Athena table has been successfully created and is ready for querying. You can now start analyzing your logs with powerful SQL queries or our AI-powered interface.',
    
    // 도움말
    'help.select.s3': '• Please select S3 location',
    'help.complete.database': '• Please complete database configuration',
    'help.complete.verification': '• Please complete log verification',
    
    // 폼 플레이스홀더
    'placeholder.database.name': 'Enter database name',
    'placeholder.table.name': 'Enter table name'
  }
};

export const LanguageProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [language, setLanguage] = useState<Language>('ko');

  // 로컬 스토리지에서 언어 설정 불러오기
  useEffect(() => {
    const savedLanguage = localStorage.getItem('language') as Language;
    if (savedLanguage && (savedLanguage === 'ko' || savedLanguage === 'en')) {
      setLanguage(savedLanguage);
    }
  }, []);

  // 언어 변경 시 로컬 스토리지에 저장
  const handleSetLanguage = (newLanguage: Language) => {
    setLanguage(newLanguage);
    localStorage.setItem('language', newLanguage);
  };

  // 번역 함수
  const t = (key: string): string => {
    const translation = translations[language] as Record<string, string>;
    return translation[key] || key;
  };

  return (
    <LanguageContext.Provider value={{ language, setLanguage: handleSetLanguage, t }}>
      {children}
    </LanguageContext.Provider>
  );
};

export const useLanguage = () => {
  const context = useContext(LanguageContext);
  if (context === undefined) {
    throw new Error('useLanguage must be used within a LanguageProvider');
  }
  return context;
};