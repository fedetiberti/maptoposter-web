/**
 * Theme picker component with color swatches
 */
import { Theme } from '../api/client';

interface ThemePickerProps {
  themes: Theme[];
  selectedTheme: string;
  onThemeSelect: (themeId: string) => void;
  disabled?: boolean;
}

export function ThemePicker({
  themes,
  selectedTheme,
  onThemeSelect,
  disabled = false,
}: ThemePickerProps) {
  return (
    <div className="card">
      <h2 className="card-title">Theme</h2>
      <div className="theme-grid">
        {themes.map((theme) => (
          <div key={theme.id}>
            <button
              type="button"
              className={`theme-swatch ${selectedTheme === theme.id ? 'selected' : ''}`}
              onClick={() => !disabled && onThemeSelect(theme.id)}
              disabled={disabled}
              title={theme.name}
              aria-label={`Select ${theme.name} theme`}
            >
              <div
                className="theme-swatch-bg"
                style={{ backgroundColor: theme.colors.bg }}
              />
              <div className="theme-swatch-roads">
                <div
                  className="theme-swatch-road"
                  style={{ backgroundColor: theme.colors.road_primary }}
                />
                <div
                  className="theme-swatch-road"
                  style={{ backgroundColor: theme.colors.road_primary, opacity: 0.7 }}
                />
                <div
                  className="theme-swatch-road"
                  style={{ backgroundColor: theme.colors.road_primary, opacity: 0.4 }}
                />
              </div>
            </button>
            <div className="theme-name">{theme.name}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
