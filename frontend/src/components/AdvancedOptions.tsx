/**
 * Advanced options component with collapsible panel
 */
import React, { useState } from 'react';
import { DimensionPreset } from '../api/client';

interface AdvancedOptionsProps {
  distance: number;
  onDistanceChange: (distance: number) => void;
  preset: string;
  onPresetChange: (presetId: string) => void;
  customWidth: number;
  customHeight: number;
  onCustomWidthChange: (width: number) => void;
  onCustomHeightChange: (height: number) => void;
  cityLabel: string;
  countryLabel: string;
  onCityLabelChange: (label: string) => void;
  onCountryLabelChange: (label: string) => void;
  presets: DimensionPreset[];
  disabled?: boolean;
}

export function AdvancedOptions({
  distance,
  onDistanceChange,
  preset,
  onPresetChange,
  customWidth,
  customHeight,
  onCustomWidthChange,
  onCustomHeightChange,
  cityLabel,
  countryLabel,
  onCityLabelChange,
  onCountryLabelChange,
  presets,
  disabled = false,
}: AdvancedOptionsProps) {
  const [isOpen, setIsOpen] = useState(false);

  const formatDistance = (meters: number): string => {
    if (meters >= 1000) {
      return `${(meters / 1000).toFixed(1)} km`;
    }
    return `${meters} m`;
  };

  return (
    <div className="card">
      <button
        type="button"
        className="advanced-toggle"
        onClick={() => setIsOpen(!isOpen)}
      >
        <span className="advanced-toggle-label">Advanced Options</span>
        <svg
          className={`advanced-toggle-icon ${isOpen ? 'open' : ''}`}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M19 9l-7 7-7-7"
          />
        </svg>
      </button>

      {isOpen && (
        <div className="advanced-options">
          {/* Distance/Zoom Slider */}
          <div className="slider-container">
            <div className="slider-header">
              <label className="input-label">Map Radius</label>
              <span className="slider-value">{formatDistance(distance)}</span>
            </div>
            <input
              type="range"
              className="slider"
              min={4000}
              max={30000}
              step={1000}
              value={distance}
              onChange={(e) => onDistanceChange(Number(e.target.value))}
              disabled={disabled}
            />
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>
              <span>Dense (4km)</span>
              <span>Wide (30km)</span>
            </div>
          </div>

          {/* Dimension Presets */}
          <div className="input-group">
            <label className="input-label">Dimensions</label>
            <select
              className="select"
              value={preset}
              onChange={(e) => onPresetChange(e.target.value)}
              disabled={disabled}
            >
              {presets.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name} ({p.description})
                </option>
              ))}
              <option value="custom">Custom</option>
            </select>
          </div>

          {/* Custom Dimensions */}
          {preset === 'custom' && (
            <div className="input-row">
              <div className="input-group">
                <label className="input-label">Width (inches)</label>
                <input
                  type="number"
                  className="input"
                  min={3}
                  max={20}
                  step={0.1}
                  value={customWidth}
                  onChange={(e) => onCustomWidthChange(Number(e.target.value))}
                  disabled={disabled}
                />
              </div>
              <div className="input-group">
                <label className="input-label">Height (inches)</label>
                <input
                  type="number"
                  className="input"
                  min={3}
                  max={24}
                  step={0.1}
                  value={customHeight}
                  onChange={(e) => onCustomHeightChange(Number(e.target.value))}
                  disabled={disabled}
                />
              </div>
            </div>
          )}

          {/* Custom Labels */}
          <div className="input-row">
            <div className="input-group">
              <label className="input-label">Custom City Label</label>
              <input
                type="text"
                className="input"
                placeholder="Override city name"
                value={cityLabel}
                onChange={(e) => onCityLabelChange(e.target.value)}
                disabled={disabled}
              />
            </div>
            <div className="input-group">
              <label className="input-label">Custom Country Label</label>
              <input
                type="text"
                className="input"
                placeholder="Override country name"
                value={countryLabel}
                onChange={(e) => onCountryLabelChange(e.target.value)}
                disabled={disabled}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
