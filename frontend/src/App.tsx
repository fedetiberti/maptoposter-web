/**
 * Main App component for MapToPoster web application
 */
import React, { useState, useEffect, useCallback } from 'react';
import { api, Theme, DimensionPreset } from './api/client';
import { useJob } from './hooks/useJob';
import { LocationInput } from './components/LocationInput';
import { ThemePicker } from './components/ThemePicker';
import { AdvancedOptions } from './components/AdvancedOptions';
import { PreviewPanel } from './components/PreviewPanel';

function App() {
  // Location state
  const [city, setCity] = useState('');
  const [country, setCountry] = useState('');

  // Theme state
  const [themes, setThemes] = useState<Theme[]>([]);
  const [selectedTheme, setSelectedTheme] = useState('noir');

  // Advanced options state
  const [distance, setDistance] = useState(15000);
  const [presets, setPresets] = useState<DimensionPreset[]>([]);
  const [selectedPreset, setSelectedPreset] = useState('poster');
  const [customWidth, setCustomWidth] = useState(12);
  const [customHeight, setCustomHeight] = useState(16);
  const [cityLabel, setCityLabel] = useState('');
  const [countryLabel, setCountryLabel] = useState('');

  // Output state
  const [format, setFormat] = useState<'png' | 'svg' | 'pdf'>('png');
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);

  // Job polling
  const { status: jobStatus, isPolling, error: jobError, startPolling, reset: resetJob } = useJob();

  // Loading state
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Load themes and presets on mount
  useEffect(() => {
    async function loadData() {
      try {
        const [themesData, presetsData] = await Promise.all([
          api.getThemes(),
          api.getPresets(),
        ]);
        setThemes(themesData);
        setPresets(presetsData);

        // Set default theme if noir exists
        if (themesData.some(t => t.id === 'noir')) {
          setSelectedTheme('noir');
        } else if (themesData.length > 0) {
          setSelectedTheme(themesData[0].id);
        }
      } catch (err) {
        setError('Failed to load themes. Please refresh the page.');
        console.error('Failed to load data:', err);
      } finally {
        setIsLoading(false);
      }
    }

    loadData();
  }, []);

  // Get current dimensions based on preset selection
  const getDimensions = useCallback(() => {
    if (selectedPreset === 'custom') {
      return { width: customWidth, height: customHeight };
    }
    const preset = presets.find(p => p.id === selectedPreset);
    if (preset) {
      return { width: preset.width, height: preset.height };
    }
    return { width: 12, height: 16 };
  }, [selectedPreset, customWidth, customHeight, presets]);

  // Handle preset change
  const handlePresetChange = (presetId: string) => {
    setSelectedPreset(presetId);
    if (presetId !== 'custom') {
      const preset = presets.find(p => p.id === presetId);
      if (preset) {
        setCustomWidth(preset.width);
        setCustomHeight(preset.height);
      }
    }
  };

  // Handle preview generation
  const handlePreview = async () => {
    if (!city || !country) {
      setError('Please enter both city and country');
      return;
    }

    setError(null);
    setPreviewUrl(null);
    resetJob();

    try {
      const { width, height } = getDimensions();
      const result = await api.generatePoster({
        city,
        country,
        theme: selectedTheme,
        preview: true,
        options: {
          distance,
          width,
          height,
          format: 'png', // Preview always PNG
          city_label: cityLabel || undefined,
          country_label: countryLabel || undefined,
        },
      });

      startPolling(result.job_id);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start generation');
    }
  };

  // Handle full resolution download
  const handleDownload = async () => {
    if (!city || !country) {
      setError('Please enter both city and country');
      return;
    }

    setError(null);
    resetJob();

    try {
      const { width, height } = getDimensions();
      const result = await api.generatePoster({
        city,
        country,
        theme: selectedTheme,
        preview: false,
        options: {
          distance,
          width,
          height,
          format,
          city_label: cityLabel || undefined,
          country_label: countryLabel || undefined,
        },
      });

      startPolling(result.job_id);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start generation');
    }
  };

  // Update preview URL when job completes
  useEffect(() => {
    if (jobStatus?.status === 'complete' && jobStatus.download_url) {
      // For preview jobs, show the image
      // For download jobs, trigger download
      const downloadUrl = api.getDownloadUrl(jobStatus.job_id);

      // Check if this was a preview (PNG format and smaller size expected)
      // We'll determine by checking if previewUrl is currently null
      if (!previewUrl || previewUrl.includes('_preview_')) {
        setPreviewUrl(downloadUrl);
      } else {
        // Full resolution - trigger download
        const link = document.createElement('a');
        link.href = downloadUrl;
        link.download = '';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
      }
    }
  }, [jobStatus]);

  // Combine errors
  const displayError = error || jobError;

  // Can generate if city and country are filled
  const canGenerate = city.trim().length > 0 && country.trim().length > 0;

  if (isLoading) {
    return (
      <div className="app">
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100vh' }}>
          <div className="spinner" />
        </div>
      </div>
    );
  }

  return (
    <div className="app">
      <header className="header">
        <div className="header-content">
          <svg className="logo" viewBox="0 0 100 100">
            <rect width="100" height="100" rx="10" fill="#1a1a1a"/>
            <path d="M20 70 L30 50 L45 60 L60 35 L80 55" stroke="#fff" strokeWidth="3" fill="none" strokeLinecap="round" strokeLinejoin="round"/>
            <circle cx="30" cy="50" r="4" fill="#fff"/>
            <circle cx="60" cy="35" r="4" fill="#fff"/>
          </svg>
          <h1>MapToPoster</h1>
        </div>
      </header>

      <main className="main">
        <div className="form-section">
          <LocationInput
            city={city}
            country={country}
            onCityChange={setCity}
            onCountryChange={setCountry}
            disabled={isPolling}
          />

          <ThemePicker
            themes={themes}
            selectedTheme={selectedTheme}
            onThemeSelect={setSelectedTheme}
            disabled={isPolling}
          />

          <AdvancedOptions
            distance={distance}
            onDistanceChange={setDistance}
            preset={selectedPreset}
            onPresetChange={handlePresetChange}
            customWidth={customWidth}
            customHeight={customHeight}
            onCustomWidthChange={setCustomWidth}
            onCustomHeightChange={setCustomHeight}
            cityLabel={cityLabel}
            countryLabel={countryLabel}
            onCityLabelChange={setCityLabel}
            onCountryLabelChange={setCountryLabel}
            presets={presets}
            disabled={isPolling}
          />
        </div>

        <PreviewPanel
          previewUrl={previewUrl}
          jobStatus={jobStatus}
          isGenerating={isPolling}
          error={displayError}
          format={format}
          onFormatChange={setFormat}
          onPreview={handlePreview}
          onDownload={handleDownload}
          canGenerate={canGenerate}
        />
      </main>

      <footer className="footer">
        <p>
          Powered by <a href="https://github.com/fedetiberti/maptoposter" target="_blank" rel="noopener noreferrer">maptoposter</a> | Map data © OpenStreetMap contributors
        </p>
      </footer>
    </div>
  );
}

export default App;
