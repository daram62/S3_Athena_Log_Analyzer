import React, { useState, useEffect, useRef } from 'react';
import { useLanguage } from '../contexts/LanguageContext';
import './DatabaseConfiguration.css';

interface DatabaseConfigurationProps {
  selectedBucket?: string;
  detectedLogType?: string; // 감지된 로그 타입
  onConfigurationChange?: (config: DatabaseConfig) => void;
  disabled?: boolean;
}

interface DatabaseConfig {
  databaseName: string;
  tableName: string;
  isValid: boolean;
  errors: {
    databaseName?: string;
    tableName?: string;
  };
}

interface ValidationResult {
  isValid: boolean;
  error?: string;
}

export const DatabaseConfiguration: React.FC<DatabaseConfigurationProps> = ({
  selectedBucket,
  detectedLogType,
  onConfigurationChange,
  disabled = false
}) => {
  const { t } = useLanguage();
  const [databaseName, setDatabaseName] = useState<string>('');
  const [tableName, setTableName] = useState<string>('');
  const [errors, setErrors] = useState<{ databaseName?: string; tableName?: string }>({});
  const [isEditingDatabase, setIsEditingDatabase] = useState<boolean>(false);
  const [isEditingTable, setIsEditingTable] = useState<boolean>(false);
  const [showPreview, setShowPreview] = useState<boolean>(false);
  
  const databaseInputRef = useRef<HTMLInputElement>(null);
  const tableInputRef = useRef<HTMLInputElement>(null);
  const previewTimeoutRef = useRef<NodeJS.Timeout>();

  // Generate auto database name based on bucket
  const generateDatabaseName = (bucketName?: string): string => {
    if (!bucketName) return 's3_logs_analytics';
    
    // 버킷명을 그대로 데이터베이스 이름으로 사용 (규칙에 맞게 정리)
    const cleanName = bucketName
      .toLowerCase()
      .replace(/[^a-z0-9]/g, '_')
      .replace(/_{2,}/g, '_')
      .replace(/^_|_$/g, '');
    
    // 숫자로 시작하면 앞에 db_ 추가
    if (/^\d/.test(cleanName)) {
      return `db_${cleanName}`;
    }
    
    return cleanName;
  };

  // Generate auto table name based on detected log type or bucket name
  const generateTableName = (logType?: string, bucketName?: string): string => {
    // 감지된 로그 타입이 있으면 우선 사용
    if (logType) {
      const logTypeMap: Record<string, string> = {
        's3_access': 's3_access_logs',
        'cloudfront': 'cloudfront_logs',
        'alb': 'alb_logs',
        'vpc_flow': 'vpc_flow_logs',
        'cloudtrail': 'cloudtrail_logs'
      };
      return logTypeMap[logType] || `${logType}_logs`;
    }
    
    // 로그 타입이 없으면 버킷명으로 추측
    if (!bucketName) return 'access_logs';
    
    const lowerBucket = bucketName.toLowerCase();
    
    if (lowerBucket.includes('cloudfront')) {
      return 'cloudfront_logs';
    } else if (lowerBucket.includes('alb') || lowerBucket.includes('loadbalancer')) {
      return 'alb_logs';
    } else if (lowerBucket.includes('vpc') || lowerBucket.includes('flow')) {
      return 'vpc_flow_logs';
    } else if (lowerBucket.includes('cloudtrail')) {
      return 'cloudtrail_logs';
    } else if (lowerBucket.includes('s3') || lowerBucket.includes('access')) {
      return 's3_access_logs';
    } else {
      return 'access_logs';
    }
  };

  // Validate database name
  const validateDatabaseName = (name: string): ValidationResult => {
    if (!name.trim()) {
      return { isValid: false, error: 'Database name is required.' };
    }
    
    if (name.length < 3) {
      return { isValid: false, error: 'Database name must be at least 3 characters long.' };
    }
    
    if (name.length > 64) {
      return { isValid: false, error: 'Database name cannot exceed 64 characters.' };
    }
    
    if (!/^[a-z][a-z0-9_]*$/.test(name)) {
      return { 
        isValid: false, 
        error: 'Database name must start with lowercase letter and contain only lowercase letters, numbers, and underscores.' 
      };
    }
    
    if (name.endsWith('_')) {
      return { isValid: false, error: 'Database name cannot end with underscore.' };
    }
    
    return { isValid: true };
  };

  // Validate table name
  const validateTableName = (name: string): ValidationResult => {
    if (!name.trim()) {
      return { isValid: false, error: 'Table name is required.' };
    }
    
    if (name.length < 3) {
      return { isValid: false, error: 'Table name must be at least 3 characters long.' };
    }
    
    if (name.length > 64) {
      return { isValid: false, error: 'Table name cannot exceed 64 characters.' };
    }
    
    if (!/^[a-z][a-z0-9_]*$/.test(name)) {
      return { 
        isValid: false, 
        error: 'Table name must start with lowercase letter and contain only lowercase letters, numbers, and underscores.' 
      };
    }
    
    if (name.endsWith('_')) {
      return { isValid: false, error: 'Table name cannot end with underscore.' };
    }
    
    return { isValid: true };
  };

  // Update configuration when bucket or detected log type changes
  useEffect(() => {
    if (selectedBucket) {
      const newDatabaseName = generateDatabaseName(selectedBucket);
      const newTableName = generateTableName(detectedLogType, selectedBucket);
      
      setDatabaseName(newDatabaseName);
      setTableName(newTableName);
      
      // Clear any existing errors when bucket changes
      setErrors({});
    }
  }, [selectedBucket, detectedLogType]);

  // Validate and notify parent component of changes
  useEffect(() => {
    // Only validate if bucket is selected or if user has started editing
    const shouldValidate = selectedBucket || databaseName || tableName;
    
    if (!shouldValidate) {
      // Clear errors and set as invalid but don't show errors
      setErrors({});
      const config: DatabaseConfig = {
        databaseName: '',
        tableName: '',
        isValid: false,
        errors: {}
      };
      onConfigurationChange?.(config);
      return;
    }
    
    const databaseValidation = validateDatabaseName(databaseName);
    const tableValidation = validateTableName(tableName);
    
    const newErrors: { databaseName?: string; tableName?: string } = {};
    
    // Only show errors if user has interacted with the fields or bucket is selected
    if (selectedBucket || databaseName) {
      if (!databaseValidation.isValid) {
        newErrors.databaseName = databaseValidation.error;
      }
    }
    
    if (selectedBucket || tableName) {
      if (!tableValidation.isValid) {
        newErrors.tableName = tableValidation.error;
      }
    }
    
    setErrors(newErrors);
    
    const config: DatabaseConfig = {
      databaseName,
      tableName,
      isValid: databaseValidation.isValid && tableValidation.isValid,
      errors: newErrors
    };
    
    onConfigurationChange?.(config);
  }, [databaseName, tableName, selectedBucket]); // onConfigurationChange 제거하여 무한 루프 방지

  // Handle database name change
  const handleDatabaseNameChange = (value: string) => {
    setDatabaseName(value);
  };

  // Handle table name change
  const handleTableNameChange = (value: string) => {
    setTableName(value);
  };

  // Handle database name editing
  const handleDatabaseEdit = () => {
    if (disabled) return;
    setIsEditingDatabase(true);
    setTimeout(() => databaseInputRef.current?.focus(), 0);
  };

  const handleDatabaseBlur = () => {
    setIsEditingDatabase(false);
  };

  const handleDatabaseKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      setIsEditingDatabase(false);
    } else if (e.key === 'Escape') {
      setIsEditingDatabase(false);
      // Reset to original value if needed
    }
  };

  // Handle table name editing
  const handleTableEdit = () => {
    if (disabled) return;
    setIsEditingTable(true);
    setTimeout(() => tableInputRef.current?.focus(), 0);
  };

  const handleTableBlur = () => {
    setIsEditingTable(false);
  };

  const handleTableKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      setIsEditingTable(false);
    } else if (e.key === 'Escape') {
      setIsEditingTable(false);
    }
  };

  // Handle preview tooltip
  const showPreviewTooltip = () => {
    if (previewTimeoutRef.current) {
      clearTimeout(previewTimeoutRef.current);
    }
    setShowPreview(true);
    
    previewTimeoutRef.current = setTimeout(() => {
      setShowPreview(false);
    }, 3000);
  };

  const hidePreviewTooltip = () => {
    if (previewTimeoutRef.current) {
      clearTimeout(previewTimeoutRef.current);
    }
    setShowPreview(false);
  };

  // Cleanup timeout on unmount
  useEffect(() => {
    return () => {
      if (previewTimeoutRef.current) {
        clearTimeout(previewTimeoutRef.current);
      }
    };
  }, []);

  const isConfigValid = !errors.databaseName && !errors.tableName && databaseName && tableName;

  return (
    <div className={`database-configuration ${disabled ? 'disabled' : ''}`}>
      {/* Database Name Section */}
      <div className="form-group">
        <label htmlFor="database-name" className="form-label">
          <span className="label-text">Database Name</span>
        </label>
        
        <div className={`inline-edit-container ${errors.databaseName ? 'error' : ''}`}>
          {isEditingDatabase ? (
            <input
              ref={databaseInputRef}
              type="text"
              className="inline-edit-input"
              value={databaseName}
              onChange={(e) => handleDatabaseNameChange(e.target.value)}
              onBlur={handleDatabaseBlur}
              onKeyDown={handleDatabaseKeyDown}
              disabled={disabled}
              placeholder={t('placeholder.database.name')}
            />
          ) : (
            <div 
              className="inline-edit-display"
              onClick={handleDatabaseEdit}
              role="button"
              tabIndex={disabled ? -1 : 0}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  handleDatabaseEdit();
                }
              }}
            >
              <span className="display-text">{databaseName || t('placeholder.database.name')}</span>
              {!disabled && <span className="edit-icon">✏️</span>}
            </div>
          )}
        </div>
        
        {errors.databaseName && (
          <div className="error-message">
            <span className="error-icon">⚠️</span>
            {errors.databaseName}
          </div>
        )}
      </div>

      {/* Table Name Section */}
      <div className="form-group">
        <label htmlFor="table-name" className="form-label">
          <span className="label-text">Table Name</span>
        </label>
        
        <div className={`inline-edit-container ${errors.tableName ? 'error' : ''}`}>
          {isEditingTable ? (
            <input
              ref={tableInputRef}
              type="text"
              className="inline-edit-input"
              value={tableName}
              onChange={(e) => handleTableNameChange(e.target.value)}
              onBlur={handleTableBlur}
              onKeyDown={handleTableKeyDown}
              disabled={disabled}
              placeholder={t('placeholder.table.name')}
            />
          ) : (
            <div 
              className="inline-edit-display"
              onClick={handleTableEdit}
              role="button"
              tabIndex={disabled ? -1 : 0}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  handleTableEdit();
                }
              }}
            >
              <span className="display-text">{tableName || t('placeholder.table.name')}</span>
              {!disabled && <span className="edit-icon">✏️</span>}
            </div>
          )}
        </div>
        
        {errors.tableName && (
          <div className="error-message">
            <span className="error-icon">⚠️</span>
            {errors.tableName}
          </div>
        )}
      </div>

      {/* Configuration Preview */}
      <div className="configuration-preview">
        <div 
          className="preview-trigger"
          onMouseEnter={showPreviewTooltip}
          onMouseLeave={hidePreviewTooltip}
          onClick={showPreviewTooltip}
        >
          <span className="preview-icon">👁️</span>
          <span className="preview-text">설정 미리보기</span>
        </div>
        
        {showPreview && (
          <div className="preview-tooltip">
            <div className="tooltip-header">
              <span className="tooltip-icon">🗄️</span>
              <span className="tooltip-title">데이터베이스 설정 미리보기</span>
            </div>
            <div className="tooltip-content">
              <div className="preview-item">
                <strong>Database:</strong> 
                <code>{databaseName || '(미설정)'}</code>
              </div>
              <div className="preview-item">
                <strong>Table:</strong> 
                <code>{tableName || '(미설정)'}</code>
              </div>
              <div className="preview-item">
                <strong>Full Name:</strong> 
                <code>{databaseName && tableName ? `${databaseName}.${tableName}` : '(미설정)'}</code>
              </div>
              <div className={`preview-status ${isConfigValid ? 'valid' : 'invalid'}`}>
                <span className="status-icon">{isConfigValid ? '✅' : '❌'}</span>
                <span className="status-text">
                  {isConfigValid ? '설정이 유효합니다' : '설정을 확인해주세요'}
                </span>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Configuration Status */}
      {databaseName && tableName && (
        <div className={`configuration-status ${isConfigValid ? 'valid' : 'invalid'}`}>
          <span className="status-icon">{isConfigValid ? '✅' : '⚠️'}</span>
          <span className="status-text">
            {isConfigValid 
              ? `${databaseName}.${tableName} 테이블이 생성됩니다`
              : '설정을 확인하고 오류를 수정해주세요'
            }
          </span>
        </div>
      )}
    </div>
  );
};