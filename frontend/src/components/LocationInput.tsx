/**
 * Location input component for city and country, with optional custom coordinates
 */

interface LocationInputProps {
  city: string;
  country: string;
  onCityChange: (city: string) => void;
  onCountryChange: (country: string) => void;
  useCoordinates: boolean;
  onUseCoordinatesChange: (use: boolean) => void;
  latitude: string;
  longitude: string;
  onLatitudeChange: (lat: string) => void;
  onLongitudeChange: (lon: string) => void;
  disabled?: boolean;
}

export function LocationInput({
  city,
  country,
  onCityChange,
  onCountryChange,
  useCoordinates,
  onUseCoordinatesChange,
  latitude,
  longitude,
  onLatitudeChange,
  onLongitudeChange,
  disabled = false,
}: LocationInputProps) {
  return (
    <div className="card">
      <h2 className="card-title">Location</h2>
      <div className="input-row">
        <div className="input-group">
          <label htmlFor="city" className="input-label">
            City
          </label>
          <input
            id="city"
            type="text"
            className="input"
            placeholder="e.g., Tokyo"
            value={city}
            onChange={(e) => onCityChange(e.target.value)}
            disabled={disabled}
          />
        </div>
        <div className="input-group">
          <label htmlFor="country" className="input-label">
            Country
          </label>
          <input
            id="country"
            type="text"
            className="input"
            placeholder="e.g., Japan"
            value={country}
            onChange={(e) => onCountryChange(e.target.value)}
            disabled={disabled}
          />
        </div>
      </div>

      <div style={{ marginTop: '0.75rem' }}>
        <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer', fontSize: '0.85rem' }}>
          <input
            type="checkbox"
            checked={useCoordinates}
            onChange={(e) => onUseCoordinatesChange(e.target.checked)}
            disabled={disabled}
          />
          Use custom coordinates
        </label>
      </div>

      {useCoordinates && (
        <div className="input-row" style={{ marginTop: '0.5rem' }}>
          <div className="input-group">
            <label htmlFor="latitude" className="input-label">
              Latitude
            </label>
            <input
              id="latitude"
              type="number"
              className="input"
              placeholder="e.g., 35.6762"
              value={latitude}
              onChange={(e) => onLatitudeChange(e.target.value)}
              disabled={disabled}
              min={-90}
              max={90}
              step="any"
            />
          </div>
          <div className="input-group">
            <label htmlFor="longitude" className="input-label">
              Longitude
            </label>
            <input
              id="longitude"
              type="number"
              className="input"
              placeholder="e.g., 139.6503"
              value={longitude}
              onChange={(e) => onLongitudeChange(e.target.value)}
              disabled={disabled}
              min={-180}
              max={180}
              step="any"
            />
          </div>
        </div>
      )}
    </div>
  );
}
