/**
 * Preview panel component showing generation status and download
 */
import React from 'react';
import { JobStatus } from '../api/client';

interface PreviewPanelProps {
  previewUrl: string | null;
  jobStatus: JobStatus | null;
  isGenerating: boolean;
  error: string | null;
  format: 'png' | 'svg' | 'pdf';
  onFormatChange: (format: 'png' | 'svg' | 'pdf') => void;
  onPreview: () => void;
  onDownload: () => void;
  canGenerate: boolean;
}

export function PreviewPanel({
  previewUrl,
  jobStatus,
  isGenerating,
  error,
  format,
  onFormatChange,
  onPreview,
  onDownload,
  canGenerate,
}: PreviewPanelProps) {
  const progress = jobStatus?.progress || 0;
  const isComplete = jobStatus?.status === 'complete';

  return (
    <div className="preview-section">
      <div className="preview-card">
        <div className="preview-container">
          {error && (
            <div className="error-message" style={{ margin: '1rem' }}>
              {error}
            </div>
          )}

          {!error && !previewUrl && !isGenerating && (
            <div className="preview-placeholder">
              <svg
                className="preview-placeholder-icon"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={1.5}
                  d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7"
                />
              </svg>
              <p>Enter a city and country, then click "Generate Preview" to see your map</p>
            </div>
          )}

          {!error && isGenerating && (
            <div className="preview-loading">
              <div className="spinner" />
              <div className="progress-bar">
                <div className="progress-fill" style={{ width: `${progress}%` }} />
              </div>
              <p style={{ color: 'var(--color-text-muted)', fontSize: '0.875rem' }}>
                {progress < 30 && 'Looking up location...'}
                {progress >= 30 && progress < 60 && 'Fetching map data...'}
                {progress >= 60 && progress < 80 && 'Downloading features...'}
                {progress >= 80 && 'Rendering poster...'}
              </p>
            </div>
          )}

          {!error && previewUrl && !isGenerating && (
            <img
              src={previewUrl}
              alt="Map preview"
              className="preview-image"
            />
          )}
        </div>

        <div className="preview-actions">
          <button
            type="button"
            className="button button-secondary button-full"
            onClick={onPreview}
            disabled={!canGenerate || isGenerating}
          >
            {isGenerating ? 'Generating...' : previewUrl ? 'Regenerate Preview' : 'Generate Preview'}
          </button>

          {previewUrl && !isGenerating && (
            <>
              <div className="format-selector">
                {(['png', 'svg', 'pdf'] as const).map((f) => (
                  <button
                    key={f}
                    type="button"
                    className={`format-option ${format === f ? 'selected' : ''}`}
                    onClick={() => onFormatChange(f)}
                  >
                    {f.toUpperCase()}
                  </button>
                ))}
              </div>

              <button
                type="button"
                className="button button-primary button-full"
                onClick={onDownload}
                disabled={isGenerating}
              >
                Download Full Resolution
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
