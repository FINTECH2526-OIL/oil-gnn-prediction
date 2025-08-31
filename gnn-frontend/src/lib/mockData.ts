import type { 
  Country, 
  GeopoliticalEvent, 
  OilPrice, 
  PredictionResult, 
  GraphNode,
  GraphEdge 
} from '../types';

/**
 * Mock data generator for development and testing
 * This file provides realistic sample data that mimics what would come from the backend API
 */

// Mock countries data
export const mockCountries: Country[] = [
  {
    id: 'usa',
    name: 'United States',
    code: 'US',
    coordinates: { lat: 39.8283, lng: -98.5795 },
    oilProduction: 19500000,
    oilReserves: 69000000000,
    economicIndicators: {
      gdp: 26900000000000,
      inflationRate: 3.2,
      currencyCode: 'USD'
    }
  },
  {
    id: 'russia',
    name: 'Russia',
    code: 'RU',
    coordinates: { lat: 61.5240, lng: 105.3188 },
    oilProduction: 11500000,
    oilReserves: 80000000000,
    economicIndicators: {
      gdp: 2100000000000,
      inflationRate: 5.8,
      currencyCode: 'RUB'
    }
  },
  {
    id: 'saudi_arabia',
    name: 'Saudi Arabia',
    code: 'SA',
    coordinates: { lat: 23.8859, lng: 45.0792 },
    oilProduction: 12300000,
    oilReserves: 258000000000,
    economicIndicators: {
      gdp: 833000000000,
      inflationRate: 2.5,
      currencyCode: 'SAR'
    }
  },
  {
    id: 'iran',
    name: 'Iran',
    code: 'IR',
    coordinates: { lat: 32.4279, lng: 53.6880 },
    oilProduction: 3800000,
    oilReserves: 208600000000,
    economicIndicators: {
      gdp: 640000000000,
      inflationRate: 35.2,
      currencyCode: 'IRR'
    }
  },
  {
    id: 'china',
    name: 'China',
    code: 'CN',
    coordinates: { lat: 35.8617, lng: 104.1954 },
    oilProduction: 4900000,
    oilReserves: 25000000000,
    economicIndicators: {
      gdp: 17700000000000,
      inflationRate: 2.1,
      currencyCode: 'CNY'
    }
  },
  {
    id: 'canada',
    name: 'Canada',
    code: 'CA',
    coordinates: { lat: 56.1304, lng: -106.3468 },
    oilProduction: 5500000,
    oilReserves: 169700000000,
    economicIndicators: {
      gdp: 2140000000000,
      inflationRate: 3.8,
      currencyCode: 'CAD'
    }
  }
];

// Mock geopolitical events
export const mockEvents: GeopoliticalEvent[] = [
  {
    id: 'event_1',
    title: 'US Sanctions on Russian Oil Exports',
    description: 'New round of comprehensive sanctions targeting Russian oil infrastructure and export capabilities',
    timestamp: '2024-01-15T14:30:00Z',
    countries: ['usa', 'russia'],
    eventType: 'sanction',
    severity: 'critical',
    sentimentScore: -0.85,
    impact: {
      immediate: 0.95,
      shortTerm: 0.75,
      longTerm: 0.45
    }
  },
  {
    id: 'event_2',
    title: 'OPEC+ Production Cut Agreement',
    description: 'OPEC+ announces 2 million barrels per day production cut to stabilize oil prices',
    timestamp: '2024-01-14T09:15:00Z',
    countries: ['saudi_arabia', 'russia'],
    eventType: 'economic',
    severity: 'high',
    sentimentScore: 0.65,
    impact: {
      immediate: 0.80,
      shortTerm: 0.70,
      longTerm: 0.60
    }
  },
  {
    id: 'event_3',
    title: 'Iran Nuclear Deal Negotiations Resume',
    description: 'Diplomatic talks resume regarding Iran nuclear program and potential sanctions relief',
    timestamp: '2024-01-13T16:45:00Z',
    countries: ['iran', 'usa'],
    eventType: 'political',
    severity: 'medium',
    sentimentScore: 0.35,
    impact: {
      immediate: 0.40,
      shortTerm: 0.65,
      longTerm: 0.80
    }
  },
  {
    id: 'event_4',
    title: 'China Strategic Petroleum Reserve Purchases',
    description: 'China increases strategic oil purchases amid global supply concerns',
    timestamp: '2024-01-12T11:20:00Z',
    countries: ['china'],
    eventType: 'trade',
    severity: 'medium',
    sentimentScore: 0.25,
    impact: {
      immediate: 0.50,
      shortTerm: 0.45,
      longTerm: 0.30
    }
  }
];

// Mock oil price data
export const mockOilPrices: OilPrice[] = [
  {
    timestamp: '2024-01-15T15:00:00Z',
    price: 78.45,
    currency: 'USD',
    priceType: 'WTI',
    volume: 425000,
    change: { absolute: 2.15, percentage: 2.82 }
  },
  {
    timestamp: '2024-01-15T14:00:00Z',
    price: 76.30,
    currency: 'USD',
    priceType: 'WTI',
    volume: 380000,
    change: { absolute: -0.45, percentage: -0.58 }
  },
  {
    timestamp: '2024-01-15T13:00:00Z',
    price: 76.75,
    currency: 'USD',
    priceType: 'WTI',
    volume: 395000,
    change: { absolute: 1.25, percentage: 1.65 }
  }
];

// Mock prediction results
export const mockPredictions: PredictionResult[] = [
  {
    id: 'pred_1',
    timestamp: '2024-01-15T15:30:00Z',
    prediction: {
      price: 79.85,
      confidence: 0.94,
      timeHorizon: '24h',
      trend: 'bullish'
    },
    explanation: {
      primaryFactors: [
        { factor: 'OPEC+ Production Cut', impact: 0.75, confidence: 0.92 },
        { factor: 'US-Russia Sanctions', impact: 0.65, confidence: 0.88 },
        { factor: 'China Demand Increase', impact: 0.35, confidence: 0.76 }
      ],
      keyEvents: ['event_1', 'event_2'],
      affectedCountries: ['usa', 'russia', 'saudi_arabia', 'china']
    },
    metadata: {
      modelVersion: '2.1.0',
      dataQuality: 0.96,
      featureImportance: {
        'geopolitical_events': 0.45,
        'production_data': 0.25,
        'market_sentiment': 0.20,
        'economic_indicators': 0.10
      }
    }
  }
];

// Generate mock graph nodes
export const generateMockGraphNodes = (): GraphNode[] => {
  const nodes: GraphNode[] = [];
  
  // Add country nodes
  mockCountries.forEach((country, index) => {
    nodes.push({
      id: country.id,
      label: country.name,
      type: 'country',
      position: {
        x: Math.cos((index * 60) * Math.PI / 180) * 200 + 400,
        y: Math.sin((index * 60) * Math.PI / 180) * 200 + 300
      },
      data: country,
      style: {
        color: '#f97316',
        size: 25 + (country.oilProduction || 0) / 1000000,
        opacity: 0.9
      }
    });
  });
  
  // Add event nodes
  mockEvents.forEach((event, index) => {
    nodes.push({
      id: event.id,
      label: event.title.substring(0, 20) + '...',
      type: 'event',
      position: {
        x: 200 + index * 100,
        y: 100 + index * 50
      },
      data: event,
      style: {
        color: event.severity === 'critical' ? '#ef4444' : 
               event.severity === 'high' ? '#f59e0b' : '#0ea5e9',
        size: 15 + event.impact!.immediate * 15,
        opacity: 0.8
      }
    });
  });
  
  // Add oil price nodes
  nodes.push({
    id: 'oil_price_current',
    label: 'Current Price',
    type: 'price_point',
    position: { x: 400, y: 100 },
    data: mockOilPrices[0],
    style: {
      color: '#10b981',
      size: 20,
      opacity: 1.0
    }
  });
  
  return nodes;
};

// Generate mock graph edges
export const generateMockGraphEdges = (): GraphEdge[] => {
  const edges: GraphEdge[] = [];
  
  // Country to event correlations
  const countryEventCorrelations = [
    { source: 'usa', target: 'event_1', weight: 0.95, type: 'causation' as const },
    { source: 'russia', target: 'event_1', weight: 0.90, type: 'correlation' as const },
    { source: 'saudi_arabia', target: 'event_2', weight: 0.85, type: 'causation' as const },
    { source: 'russia', target: 'event_2', weight: 0.80, type: 'correlation' as const },
    { source: 'iran', target: 'event_3', weight: 0.75, type: 'correlation' as const },
    { source: 'china', target: 'event_4', weight: 0.70, type: 'causation' as const },
  ];
  
  countryEventCorrelations.forEach((corr, index) => {
    edges.push({
      id: `edge_${index}`,
      source: corr.source,
      target: corr.target,
      weight: corr.weight,
      type: corr.type,
      style: {
        color: corr.weight > 0.8 ? '#ef4444' : 
               corr.weight > 0.6 ? '#f59e0b' : '#6b7280',
        width: 1 + corr.weight * 3,
        opacity: 0.7
      }
    });
  });
  
  // Event to price correlations
  mockEvents.forEach((event, index) => {
    edges.push({
      id: `price_edge_${index}`,
      source: event.id,
      target: 'oil_price_current',
      weight: event.impact!.immediate,
      type: 'influence',
      style: {
        color: '#10b981',
        width: 1 + event.impact!.immediate * 2,
        opacity: 0.6
      }
    });
  });
  
  return edges;
};