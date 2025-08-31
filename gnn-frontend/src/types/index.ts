// Core data types for the oil price prediction system

export interface Country {
  id: string;
  name: string;
  code: string; // ISO country code
  coordinates: {
    lat: number;
    lng: number;
  };
  oilProduction?: number;
  oilReserves?: number;
  economicIndicators?: {
    gdp: number;
    inflationRate: number;
    currencyCode: string;
  };
}

export interface GeopoliticalEvent {
  id: string;
  title: string;
  description: string;
  timestamp: string;
  countries: string[]; // Country IDs
  eventType: 'sanction' | 'conflict' | 'trade' | 'political' | 'economic' | 'natural_disaster';
  severity: 'low' | 'medium' | 'high' | 'critical';
  sentimentScore: number; // -1 to 1
  sourceUrl?: string;
  impact?: {
    immediate: number;
    shortTerm: number;
    longTerm: number;
  };
}

export interface OilPrice {
  timestamp: string;
  price: number;
  currency: 'USD';
  priceType: 'WTI' | 'Brent' | 'Dubai';
  volume?: number;
  change?: {
    absolute: number;
    percentage: number;
  };
}

export interface GraphNode {
  id: string;
  label: string;
  type: 'country' | 'event' | 'price_point';
  position: {
    x: number;
    y: number;
  };
  data: Country | GeopoliticalEvent | OilPrice;
  style?: {
    color?: string;
    size?: number;
    opacity?: number;
  };
}

export interface GraphEdge {
  id: string;
  source: string; // Node ID
  target: string; // Node ID
  weight: number; // 0-1, representing correlation strength
  type: 'correlation' | 'causation' | 'influence';
  label?: string;
  style?: {
    color?: string;
    width?: number;
    opacity?: number;
  };
}

export interface PredictionResult {
  id: string;
  timestamp: string;
  prediction: {
    price: number;
    confidence: number; // 0-1
    timeHorizon: '1h' | '6h' | '24h' | '7d';
    trend: 'bullish' | 'bearish' | 'neutral';
  };
  explanation: {
    primaryFactors: Array<{
      factor: string;
      impact: number; // -1 to 1
      confidence: number;
    }>;
    keyEvents: string[]; // Event IDs
    affectedCountries: string[]; // Country IDs
  };
  metadata: {
    modelVersion: string;
    dataQuality: number;
    featureImportance: Record<string, number>;
  };
}

// API Response types
export interface ApiResponse<T> {
  data: T;
  success: boolean;
  message?: string;
  timestamp: string;
}

export interface ApiError {
  error: string;
  code: number;
  details?: any;
  timestamp: string;
}

// UI State types
export interface LoadingState {
  isLoading: boolean;
  message?: string;
}

export interface ErrorState {
  hasError: boolean;
  message?: string;
  code?: number;
}

// Navigation types
export type RouteType = '/dashboard' | '/graph';

export interface NavigationItem {
  path: RouteType;
  label: string;
  icon: string;
  description?: string;
}

