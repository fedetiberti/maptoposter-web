/**
 * API client for communicating with the MapToPoster backend
 */

const API_BASE = import.meta.env.VITE_API_URL || '';

export interface Theme {
  id: string;
  name: string;
  description: string;
  colors: {
    bg: string;
    text: string;
    road_primary: string;
    water: string;
    parks: string;
  };
}

export interface DimensionPreset {
  id: string;
  name: string;
  width: number;
  height: number;
  description: string;
}

export interface GenerateOptions {
  distance: number;
  width: number;
  height: number;
  format: 'png' | 'svg' | 'pdf';
  city_label?: string;
  country_label?: string;
  latitude?: number;
  longitude?: number;
}

export interface GenerateRequest {
  city: string;
  country: string;
  theme: string;
  preview: boolean;
  options: GenerateOptions;
}

export interface JobStatus {
  job_id: string;
  status: 'pending' | 'processing' | 'complete' | 'error';
  progress: number;
  download_url?: string;
  expires_at?: string;
  error?: string;
}

class ApiClient {
  private async fetch<T>(path: string, options?: RequestInit): Promise<T> {
    const response = await fetch(`${API_BASE}${path}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
      throw new Error(error.detail || `HTTP ${response.status}`);
    }

    return response.json();
  }

  async getThemes(): Promise<Theme[]> {
    const result = await this.fetch<{ themes: Theme[] }>('/api/themes');
    return result.themes;
  }

  async getPresets(): Promise<DimensionPreset[]> {
    const result = await this.fetch<{ presets: DimensionPreset[] }>('/api/presets');
    return result.presets;
  }

  async generatePoster(request: GenerateRequest): Promise<{ job_id: string; estimated_wait: number }> {
    return this.fetch('/api/generate', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async getJobStatus(jobId: string): Promise<JobStatus> {
    return this.fetch(`/api/job/${jobId}`);
  }

  getDownloadUrl(jobId: string): string {
    return `${API_BASE}/api/download/${jobId}`;
  }
}

export const api = new ApiClient();
