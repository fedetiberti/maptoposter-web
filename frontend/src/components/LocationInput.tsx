/**
 * Location input component for city and country
 */

interface LocationInputProps {
  city: string;
  country: string;
  onCityChange: (city: string) => void;
  onCountryChange: (country: string) => void;
  disabled?: boolean;
}

export function LocationInput({
  city,
  country,
  onCityChange,
  onCountryChange,
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
    </div>
  );
}
