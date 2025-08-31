import type { 
  Country, 
  GeopoliticalEvent, 
  OilPrice, 
  PredictionResult, 
  ApiResponse,
  ApiError 
} from '../types';
import { 
  mockCountries, 
  mockEvents, 
  mockOilPrices, 
  mockPredictions  
} from '../lib/mockData';

/**
 * API service layer for interacting with backend endpoints
 * Currently uses mock data but structured to easily swap to real API calls
 */

// Configuration
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
const API_TIMEOUT = 10000; // 10 seconds

// Helper function to simulate API delay
const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

// Helper function to create mock API responses
const createMockResponse = <T>(data: T): ApiResponse<T> => ({
  data,
  success: true,
  timestamp: new Date().toISOString()
});

// Helper function to simulate potential API errors
const simulateError = (probability: number = 0.05): void => {
  if (Math.random() < probability) {
    throw new Error('Simulated API error');
  }
};

/**
 * Countries API
 */
export const countriesApi = {
  // Get all countries
  async getAll(): Promise<ApiResponse<Country[]>> {
    await delay(300);
    simulateError(0.02);
    return createMockResponse(mockCountries);
  },

  // Get country by ID
  async getById(id: string): Promise<ApiResponse<Country>> {
    await delay(200);
    simulateError(0.02);
    const country = mockCountries.find(c => c.id === id);
    if (!country) {
      throw new Error(`Country with id ${id} not found`);
    }
    return createMockResponse(country);
  },

  // Get countries by region or filter
  async getByFilter(filters: Partial<Country>): Promise<ApiResponse<Country[]>> {
    await delay(250);
    simulateError(0.02);
    // Simple filtering logic - in real API this would be server-side
    const filtered = mockCountries.filter(country => {
      return Object.entries(filters).every(([key, value]) => {
        return country[key as keyof Country] === value;
      });
    });
    return createMockResponse(filtered);
  }
};

/**
 * Events API
 */
export const eventsApi = {
  // Get all events
  async getAll(): Promise<ApiResponse<GeopoliticalEvent[]>> {
    await delay(400);
    simulateError(0.03);
    return createMockResponse(mockEvents);
  },

  // Get events by date range
  async getByDateRange(startDate: string, endDate: string): Promise<ApiResponse<GeopoliticalEvent[]>> {
    await delay(350);
    simulateError(0.03);
    const filtered = mockEvents.filter(event => {
      const eventDate = new Date(event.timestamp);
      return eventDate >= new Date(startDate) && eventDate <= new Date(endDate);
    });
    return createMockResponse(filtered);
  },

  // Get events by country
  async getByCountry(countryId: string): Promise<ApiResponse<GeopoliticalEvent[]>> {
    await delay(300);
    simulateError(0.03);
    const filtered = mockEvents.filter(event => 
      event.countries.includes(countryId)
    );
    return createMockResponse(filtered);
  },

  // Get events by severity
  async getBySeverity(severity: GeopoliticalEvent['severity']): Promise<ApiResponse<GeopoliticalEvent[]>> {
    await delay(250);
    simulateError(0.03);
    const filtered = mockEvents.filter(event => event.severity === severity);
    return createMockResponse(filtered);
  }
};

/**
 * Oil Prices API
 */
export const oilPricesApi = {
  // Get latest prices
  async getLatest(): Promise<ApiResponse<OilPrice[]>> {
    await delay(200);
    simulateError(0.02);
    return createMockResponse(mockOilPrices);
  },

  // Get historical prices
  async getHistorical(
    startDate: string, 
    endDate: string, 
    priceType?: OilPrice['priceType']
  ): Promise<ApiResponse<OilPrice[]>> {
    await delay(500);
    simulateError(0.03);
    let filtered = mockOilPrices.filter(price => {
      const priceDate = new Date(price.timestamp);
      return priceDate >= new Date(startDate) && priceDate <= new Date(endDate);
    });
    
    if (priceType) {
      filtered = filtered.filter(price => price.priceType === priceType);
    }
    
    return createMockResponse(filtered);
  },

  // Get real-time price updates (would typically use WebSocket)
  async getRealTime(): Promise<ApiResponse<OilPrice>> {
    await delay(100);
    simulateError(0.01);
    // Simulate real-time price with slight variation
    const basePrice = mockOilPrices[0];
    const variation = (Math.random() - 0.5) * 2; // ±1 dollar variation
    const newPrice: OilPrice = {
      ...basePrice,
      price: Number((basePrice.price + variation).toFixed(2)),
      timestamp: new Date().toISOString(),
      change: {
        absolute: Number(variation.toFixed(2)),
        percentage: Number(((variation / basePrice.price) * 100).toFixed(2))
      }
    };
    return createMockResponse(newPrice);
  }
};

/**
 * Predictions API
 */
export const predictionsApi = {
  // Get latest prediction
  async getLatest(): Promise<ApiResponse<PredictionResult>> {
    await delay(600);
    simulateError(0.04);
    return createMockResponse(mockPredictions[0]);
  },

  // Get prediction by time horizon
  async getByTimeHorizon(
    timeHorizon: PredictionResult['prediction']['timeHorizon']
  ): Promise<ApiResponse<PredictionResult[]>> {
    await delay(500);
    simulateError(0.04);
    const filtered = mockPredictions.filter(pred => 
      pred.prediction.timeHorizon === timeHorizon
    );
    return createMockResponse(filtered);
  },

  // Request new prediction (calls ML model)
  async requestPrediction(
    timeHorizon: PredictionResult['prediction']['timeHorizon'],
    includeExplanation: boolean = true
  ): Promise<ApiResponse<PredictionResult>> {
    await delay(2000); // Longer delay to simulate ML model processing
    simulateError(0.05);
    
    // In real implementation, this would call the FastAPI /predict endpoint
    console.log(`Requesting prediction for ${timeHorizon} with explanation: ${includeExplanation}`);
    
    return createMockResponse(mockPredictions[0]);
  },

  // Get prediction explanation
  async getExplanation(predictionId: string): Promise<ApiResponse<PredictionResult['explanation']>> {
    await delay(400);
    simulateError(0.03);
    const prediction = mockPredictions.find(p => p.id === predictionId);
    if (!prediction) {
      throw new Error(`Prediction with id ${predictionId} not found`);
    }
    return createMockResponse(prediction.explanation);
  }
};

/**
 * Health check API
 */
export const healthApi = {
  async check(): Promise<ApiResponse<{ status: string; version: string; timestamp: string }>> {
    await delay(100);
    return createMockResponse({
      status: 'healthy',
      version: '2.1.0',
      timestamp: new Date().toISOString()
    });
  }
};

/**
 * Error handler for API calls
 */
export const handleApiError = (error: unknown): ApiError => {
  if (error instanceof Error) {
    return {
      error: error.message,
      code: 500,
      timestamp: new Date().toISOString()
    };
  }
  
  return {
    error: 'Unknown API error',
    code: 500,
    timestamp: new Date().toISOString()
  };
};

