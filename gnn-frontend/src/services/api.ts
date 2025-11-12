import type { PredictionRecord } from '../types/api';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8080';

export interface ApiError {
  detail: string;
}

async function fetchApi<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
    ...options,
  });

  if (!response.ok) {
    const error: ApiError = await response.json().catch(() => ({
      detail: 'An error occurred',
    }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  return response.json();
}

// Health check
export async function checkHealth(): Promise<{
  status: string;
  timestamp: string;
}> {
  return fetchApi('/health');
}

// Get prediction history
export async function getPredictionHistory(options?: {
  days?: number;
  startDate?: string;
}): Promise<PredictionRecord[]> {
  const params = new URLSearchParams();
  if (options?.days) params.set('days', options.days.toString());
  if (options?.startDate) params.set('start_date', options.startDate);

  const path = params.toString() ? `/history?${params.toString()}` : '/history';
  return fetchApi<PredictionRecord[]>(path);
}

// Get latest prediction
export async function getLatestPrediction(): Promise<{
  feature_date: string;
  prediction_for_date: string;
  predicted_close: number;
  predicted_delta: number;
  reference_close: number;
  top_contributors: Array<{
    country: string;
    contribution: number;
    percentage: number;
  }>;
}> {
  return fetchApi('/predict', { method: 'POST' });
}

export async function triggerBackfill(options: {
  days: number;
  startDate?: string;
  dryRun?: boolean;
}): Promise<{ [key: string]: unknown }> {
  const params = new URLSearchParams({ days: options.days.toString() });
  if (options.startDate) params.set('start_date', options.startDate);
  if (options.dryRun) params.set('dry_run', 'true');

  return fetchApi(`/backfill?${params.toString()}`, { method: 'POST' });
}
