import React, { useState, useEffect, useRef } from 'react';
import { listBuckets, listFolders, BucketInfo, FolderInfo } from '../services/api';
import './S3LocationSelector.css';

interface S3LocationSelectorProps {
  onLocationChange?: (bucket: string, folder: string) => void;
  disabled?: boolean;
}

export const S3LocationSelector: React.FC<S3LocationSelectorProps> = ({
  onLocationChange,
  disabled = false
}) => {
  const [buckets, setBuckets] = useState<BucketInfo[]>([]);
  const [selectedBucket, setSelectedBucket] = useState<string>('');
  const [selectedFolder, setSelectedFolder] = useState<string>('');
  const [folders, setFolders] = useState<FolderInfo[]>([]);
  const [isLoadingBuckets, setIsLoadingBuckets] = useState(false);
  const [isLoadingFolders, setIsLoadingFolders] = useState(false);
  const [bucketDropdownOpen, setBucketDropdownOpen] = useState(false);
  const [folderDropdownOpen, setFolderDropdownOpen] = useState(false);
  const [error, setError] = useState<string>('');

  const bucketDropdownRef = useRef<HTMLDivElement>(null);
  const folderDropdownRef = useRef<HTMLDivElement>(null);

  // Load buckets on component mount
  useEffect(() => {
    loadBuckets();
  }, []);

  // Close dropdowns when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (bucketDropdownRef.current && !bucketDropdownRef.current.contains(event.target as Node)) {
        setBucketDropdownOpen(false);
      }
      if (folderDropdownRef.current && !folderDropdownRef.current.contains(event.target as Node)) {
        setFolderDropdownOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Notify parent component of location changes
  useEffect(() => {
    if (selectedBucket && onLocationChange) {
      onLocationChange(selectedBucket, selectedFolder);
    }
  }, [selectedBucket, selectedFolder, onLocationChange]);

  const loadBuckets = async () => {
    setIsLoadingBuckets(true);
    setError('');
    
    try {
      const bucketList = await listBuckets();
      setBuckets(bucketList);
    } catch (err: any) {
      setError(err.message || '버킷 목록을 불러오는데 실패했습니다. 다시 시도해주세요.');
    } finally {
      setIsLoadingBuckets(false);
    }
  };

  const loadFolders = async (bucketName: string) => {
    setIsLoadingFolders(true);
    
    try {
      const response = await listFolders(bucketName);
      setFolders(response.folders);
    } catch (err: any) {
      console.error('Failed to load folders:', err);
      setFolders([]);
    } finally {
      setIsLoadingFolders(false);
    }
  };

  const handleBucketSelect = async (bucket: BucketInfo) => {
    setSelectedBucket(bucket.name);
    setSelectedFolder(''); // Reset folder selection
    setBucketDropdownOpen(false);
    
    // 폴더 목록 로드 및 자동 선택
    setIsLoadingFolders(true);
    
    try {
      const response = await listFolders(bucket.name);
      setFolders(response.folders);
      
      // 로그 관련 폴더 자동 감지 및 선택
      const logFolderPatterns = [
        'access-logs/',
        'logs/',
        'log/',
        'access-log/',
        'cloudtrail/',
        'alb-logs/',
        'cloudfront-logs/',
        'vpc-flow-logs/'
      ];
      
      // 패턴과 일치하는 첫 번째 폴더 찾기
      const detectedFolder = response.folders.find(folder => 
        logFolderPatterns.some(pattern => 
          folder.path.toLowerCase().includes(pattern.toLowerCase())
        )
      );
      
      if (detectedFolder) {
        setSelectedFolder(detectedFolder.path);
        console.log('Auto-detected log folder:', detectedFolder.path);
      }
    } catch (err: any) {
      console.error('Failed to load folders:', err);
      setFolders([]);
    } finally {
      setIsLoadingFolders(false);
    }
  };

  const handleFolderSelect = (folder: string) => {
    setSelectedFolder(folder);
    setFolderDropdownOpen(false);
  };

  const getS3Path = () => {
    if (!selectedBucket) return '';
    return `s3://${selectedBucket}/${selectedFolder}`;
  };

  const getSelectedRegion = () => {
    const bucket = buckets.find(b => b.name === selectedBucket);
    return bucket?.region || '';
  };

  return (
    <div className="s3-location-selector">
      {error && (
        <div className="error-message">
          <span className="error-icon">⚠️</span>
          {error}
          <button 
            className="retry-button"
            onClick={loadBuckets}
            disabled={isLoadingBuckets}
          >
            다시 시도
          </button>
        </div>
      )}

      <div className="form-group">
        <label htmlFor="bucket-selector">Select Log Bucket</label>
        <div 
          className={`custom-dropdown-container ${bucketDropdownOpen ? 'open' : ''} ${disabled ? 'disabled' : ''}`}
          ref={bucketDropdownRef}
        >
          <button
            type="button"
            className={`custom-dropdown-trigger ${selectedBucket ? 'has-value' : ''}`}
            onClick={() => !disabled && setBucketDropdownOpen(!bucketDropdownOpen)}
            disabled={disabled || isLoadingBuckets}
            aria-haspopup="listbox"
            aria-expanded={bucketDropdownOpen}
          >
            <span className="dropdown-icon">📁</span>
            <span className="dropdown-text">
              {isLoadingBuckets ? (
                <span className="loading-text">
                  <span className="loading-spinner-small"></span>
                  버킷 목록 로딩 중...
                </span>
              ) : selectedBucket ? (
                selectedBucket
              ) : (
                'Select a bucket...'
              )}
            </span>
            <span className={`dropdown-arrow ${bucketDropdownOpen ? 'open' : ''}`}>
              ▼
            </span>
          </button>

          {bucketDropdownOpen && !isLoadingBuckets && (
            <div className="custom-dropdown-menu" role="listbox">
              {buckets.length === 0 ? (
                <div className="dropdown-item disabled">
                  사용 가능한 버킷이 없습니다
                </div>
              ) : (
                buckets.map((bucket) => (
                  <button
                    key={bucket.name}
                    type="button"
                    className={`dropdown-item ${selectedBucket === bucket.name ? 'selected' : ''}`}
                    onClick={() => handleBucketSelect(bucket)}
                    role="option"
                    aria-selected={selectedBucket === bucket.name}
                  >
                    <span className="item-icon">📁</span>
                    <div className="item-content">
                      <div className="item-name">{bucket.name}</div>
                      <div className="item-region">
                        <span className="region-icon">🌍</span>
                        {bucket.region || 'us-east-1'}
                      </div>
                    </div>
                  </button>
                ))
              )}
            </div>
          )}
        </div>
      </div>

      <div className="form-group">
        <label htmlFor="folder-selector">Select Folder (Optional)</label>
        <div 
          className={`custom-dropdown-container ${folderDropdownOpen ? 'open' : ''} ${disabled || !selectedBucket ? 'disabled' : ''}`}
          ref={folderDropdownRef}
        >
          <button
            type="button"
            className={`custom-dropdown-trigger ${selectedFolder ? 'has-value' : ''}`}
            onClick={() => !disabled && selectedBucket && setFolderDropdownOpen(!folderDropdownOpen)}
            disabled={disabled || !selectedBucket || isLoadingFolders}
            aria-haspopup="listbox"
            aria-expanded={folderDropdownOpen}
          >
            <span className="dropdown-icon">📂</span>
            <span className="dropdown-text">
              {isLoadingFolders ? (
                <span className="loading-text">
                  <span className="loading-spinner-small"></span>
                  폴더 목록 로딩 중...
                </span>
              ) : selectedFolder ? (
                selectedFolder
              ) : selectedBucket ? (
                'Select a folder... (optional)'
              ) : (
                'Select a bucket first'
              )}
            </span>
            <span className={`dropdown-arrow ${folderDropdownOpen ? 'open' : ''}`}>
              ▼
            </span>
          </button>

          {folderDropdownOpen && !isLoadingFolders && selectedBucket && (
            <div className="custom-dropdown-menu" role="listbox">
              <button
                type="button"
                className={`dropdown-item ${selectedFolder === '' ? 'selected' : ''}`}
                onClick={() => handleFolderSelect('')}
                role="option"
                aria-selected={selectedFolder === ''}
              >
                <span className="item-icon">📁</span>
                <div className="item-content">
                  <div className="item-name">루트 폴더 (전체 버킷)</div>
                  <div className="item-description">버킷의 모든 파일 스캔</div>
                </div>
              </button>
              {folders.length === 0 ? (
                <div className="dropdown-item disabled">
                  <span className="item-icon">ℹ️</span>
                  <div className="item-content">
                    <div className="item-name">폴더가 없습니다</div>
                    <div className="item-description">루트 폴더를 선택하세요</div>
                  </div>
                </div>
              ) : (
                folders.map((folder) => (
                  <button
                    key={folder.path}
                    type="button"
                    className={`dropdown-item ${selectedFolder === folder.path ? 'selected' : ''}`}
                    onClick={() => handleFolderSelect(folder.path)}
                    role="option"
                    aria-selected={selectedFolder === folder.path}
                  >
                    <span className="item-icon">📂</span>
                    <div className="item-content">
                      <div className="item-name">{folder.name}</div>
                      <div className="item-description">{folder.path}</div>
                    </div>
                  </button>
                ))
              )}
            </div>
          )}
        </div>
      </div>

      {/* S3 Location Info Panel */}
      {selectedBucket && (
        <div className="location-info-panel">
          <div className="info-panel location">
            <span className="info-icon">📍</span>
            <div className="info-content">
              <strong>S3 Location:</strong>
              <code>{getS3Path()}</code>
            </div>
          </div>
          
          {getSelectedRegion() && (
            <div className="info-panel region">
              <span className="info-icon">🌍</span>
              <div className="info-content">
                <strong>Region:</strong>
                <code>{getSelectedRegion()}</code>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};