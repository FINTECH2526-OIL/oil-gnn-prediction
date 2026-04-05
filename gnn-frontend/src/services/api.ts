import type { PredictionRecord } from '../types/api';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'https://oil-gnn-backend-653222494702.us-central1.run.app/';

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

// Admin: manually patch oil prices and run prediction
export interface PriceEntry {
  date: string;       // YYYY-MM-DD
  wti_price: number;
  brent_price: number;
}

export interface PatchResult {
  date: string;
  predicted_delta: number;
  predicted_direction: 'UP' | 'DOWN' | 'FLAT';
  reference_wti: number;
  top_contributors: Record<string, { contribution: number; percentage: number; raw_prediction: number; attention_weight: number }>;
  total_abs_contribution: number;
  num_countries: number;
  model_version: string;
  injected_dates: string[];
  gcs_file: string;
}

export async function adminPatchPrices(prices: PriceEntry[]): Promise<PatchResult> {
  return fetchApi('/admin/patch-prices', {
    method: 'POST',
    body: JSON.stringify({ prices }),
  });
}

// Update predictions with latest data
export async function updatePredictions(forceRefresh = false): Promise<{
  status: string;
  message: string;
  latest_alpha_vantage_date: string | null;
  latest_processed_date?: string;
  new_processed_date?: string;
}> {
  const params = forceRefresh ? '?force_refresh=true' : '';
  return fetchApi(`/update${params}`, { method: 'POST' });
}
