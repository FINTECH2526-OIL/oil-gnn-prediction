import { useEffect, useState } from 'react';
import { 
  TrendingUp, 
  TrendingDown, 
  Activity, 
  Globe, 
  Zap, 
  AlertTriangle,
  BarChart3,
  Clock,
  Target,
  Layers
} from 'lucide-react';
import { useAppStore } from '../store';
import { 
  countriesApi, 
  eventsApi, 
  oilPricesApi, 
  predictionsApi,
  handleApiError 
} from '../services/api';
import { LoadingSpinner } from '../components/ui/LoadingSpinner';
import { ErrorBoundary } from '../components/ui/ErrorBoundary';
import type { GeopoliticalEvent, OilPrice, PredictionResult } from '../types';

/**
 * Main Dashboard page component
 * Features:
 * - Real-time oil price display
 * - Key metrics cards
 * - Recent events table
 * - Latest predictions
 * - System health indicators
 * - Interactive data visualization previews
 */
export const Dashboard: React.FC = () => {
  const { 
    countries, 
    events, 
    oilPrices, 
    predictions,
    loading,
    error,
    setCountries,
    setEvents,
    setOilPrices,
    setPredictions,
    setLoading,
    setError,
    clearError
  } = useAppStore();

  const [refreshing, setRefreshing] = useState(false);

  // Load initial data
  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    setLoading({ isLoading: true, message: 'Loading dashboard data...' });
    clearError();

    try {
      // Load data in parallel for better performance
      const [countriesResponse, eventsResponse, pricesResponse, predictionsResponse] = await Promise.all([
        countriesApi.getAll(),
        eventsApi.getAll(),
        oilPricesApi.getLatest(),
        predictionsApi.getLatest(),
      ]);

      setCountries(countriesResponse.data);
      setEvents(eventsResponse.data);
      setOilPrices(pricesResponse.data);
      setPredictions([predictionsResponse.data]);

    } catch (err) {
      const apiError = handleApiError(err);
      setError({ hasError: true, message: apiError.error, code: apiError.code });
    } finally {
      setLoading({ isLoading: false });
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    await loadDashboardData();
    setRefreshing(false);
  };

  // Calculate key metrics
  const currentPrice = oilPrices[0]?.price || 0;
  const priceChange = oilPrices[0]?.change?.percentage || 0;
  const criticalEvents = events.filter(e => e.severity === 'critical').length;
  const activeCountries = countries.length;
  const modelAccuracy = predictions[0]?.prediction.confidence || 0;

  if (loading.isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <LoadingSpinner size="lg" />
          <p className="text-gray-400 mt-4">{loading.message}</p>
        </div>
      </div>
    );
  }

  if (error.hasError) {
    return (
      <div className="card text-center py-12">
        <AlertTriangle className="mx-auto text-red-500 mb-4" size={48} />
        <h3 className="text-lg font-semibold text-white mb-2">Failed to Load Dashboard</h3>
        <p className="text-gray-400 mb-6">{error.message}</p>
        <button onClick={handleRefresh} className="btn-primary">
          Try Again
        </button>
      </div>
    );
  }

  return (
    <ErrorBoundary>
      <div className="space-y-6 animate-fade-in">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold gradient-text">
              Oil Price Intelligence Dashboard
            </h1>
            <p className="text-gray-400 mt-2">
              Real-time geopolitical analysis and price prediction
            </p>
          </div>
          <button
            onClick={handleRefresh}
            disabled={refreshing}
            className="btn-secondary flex items-center space-x-2"
          >
            <Activity size={16} className={refreshing ? 'animate-spin' : ''} />
            <span>Refresh Data</span>
          </button>
        </div>

        {/* Key Metrics Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {/* Current Oil Price */}
          <div className="card group hover:shadow-glow transition-all duration-300">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-400 text-sm">Current Oil Price (WTI)</p>
                <p className="text-2xl font-bold text-white mt-1">
                  ${currentPrice.toFixed(2)}
                </p>
                <div className={`flex items-center space-x-1 mt-2 ${
                  priceChange >= 0 ? 'text-green-400' : 'text-red-400'
                }`}>
                  {priceChange >= 0 ? <TrendingUp size={16} /> : <TrendingDown size={16} />}
                  <span className="text-sm font-medium">
                    {priceChange >= 0 ? '+' : ''}{priceChange.toFixed(2)}%
                  </span>
                </div>
              </div>
              <div className="p-3 bg-primary-500/20 rounded-lg">
                <BarChart3 className="text-primary-400" size={24} />
              </div>
            </div>
          </div>

          {/* Critical Events */}
          <div className="card group hover:shadow-glow transition-all duration-300">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-400 text-sm">Critical Events</p>
                <p className="text-2xl font-bold text-white mt-1">{criticalEvents}</p>
                <p className="text-red-400 text-sm mt-2">High impact detected</p>
              </div>
              <div className="p-3 bg-red-500/20 rounded-lg">
                <Zap className="text-red-400" size={24} />
              </div>
            </div>
          </div>

          {/* Active Countries */}
          <div className="card group hover:shadow-glow transition-all duration-300">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-400 text-sm">Monitored Countries</p>
                <p className="text-2xl font-bold text-white mt-1">{activeCountries}</p>
                <p className="text-blue-400 text-sm mt-2">Global coverage</p>
              </div>
              <div className="p-3 bg-blue-500/20 rounded-lg">
                <Globe className="text-blue-400" size={24} />
              </div>
            </div>
          </div>

          {/* Model Accuracy */}
          <div className="card group hover:shadow-glow transition-all duration-300">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-400 text-sm">Model Accuracy</p>
                <p className="text-2xl font-bold text-white mt-1">
                  {(modelAccuracy * 100).toFixed(1)}%
                </p>
                <p className="text-green-400 text-sm mt-2">High confidence</p>
              </div>
              <div className="p-3 bg-green-500/20 rounded-lg">
                <Target className="text-green-400" size={24} />
              </div>
            </div>
          </div>
        </div>

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Recent Events Table */}
          <div className="lg:col-span-2">
            <div className="card">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-xl font-semibold text-white flex items-center space-x-2">
                  <Activity size={20} />
                  <span>Recent Geopolitical Events</span>
                </h2>
                <span className="text-xs text-gray-400">
                  Last updated: {new Date().toLocaleTimeString()}
                </span>
              </div>
              
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-white/10">
                      <th className="text-left text-gray-400 text-sm font-medium pb-3">Event</th>
                      <th className="text-left text-gray-400 text-sm font-medium pb-3">Countries</th>
                      <th className="text-left text-gray-400 text-sm font-medium pb-3">Severity</th>
                      <th className="text-left text-gray-400 text-sm font-medium pb-3">Impact</th>
                    </tr>
                  </thead>
                  <tbody className="space-y-2">
                    {events.slice(0, 5).map((event: GeopoliticalEvent) => (
                      <tr key={event.id} className="border-b border-white/5 hover:bg-white/5 transition-colors">
                        <td className="py-4 pr-4">
                          <div>
                            <p className="text-white font-medium text-sm">{event.title}</p>
                            <p className="text-gray-400 text-xs mt-1 line-clamp-2">
                              {event.description}
                            </p>
                          </div>
                        </td>
                        <td className="py-4 px-4">
                          <div className="flex flex-wrap gap-1">
                            {event.countries.slice(0, 2).map(countryId => {
                              const country = countries.find(c => c.id === countryId);
                              return (
                                <span key={countryId} className="text-xs bg-blue-500/20 text-blue-300 px-2 py-1 rounded">
                                  {country?.code || countryId}
                                </span>
                              );
                            })}
                            {event.countries.length > 2 && (
                              <span className="text-xs text-gray-400">+{event.countries.length - 2}</span>
                            )}
                          </div>
                        </td>
                        <td className="py-4 px-4">
                          <span className={`text-xs px-2 py-1 rounded-full ${
                            event.severity === 'critical' ? 'bg-red-500/20 text-red-300' :
                            event.severity === 'high' ? 'bg-orange-500/20 text-orange-300' :
                            event.severity === 'medium' ? 'bg-yellow-500/20 text-yellow-300' :
                            'bg-gray-500/20 text-gray-300'
                          }`}>
                            {event.severity}
                          </span>
                        </td>
                        <td className="py-4 pl-4">
                          <div className="flex items-center space-x-2">
                            <div className="w-12 bg-gray-700 rounded-full h-2">
                              <div 
                                className={`h-2 rounded-full ${
                                  event.impact!.immediate > 0.7 ? 'bg-red-500' :
                                  event.impact!.immediate > 0.4 ? 'bg-yellow-500' : 'bg-green-500'
                                }`}
                                style={{ width: `${event.impact!.immediate * 100}%` }}
                              />
                            </div>
                            <span className="text-xs text-gray-400">
                              {(event.impact!.immediate * 100).toFixed(0)}%
                            </span>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          {/* Latest Prediction & Quick Actions */}
          <div className="space-y-6">
            {/* Latest Prediction */}
            <div className="card">
              <h3 className="text-lg font-semibold text-white mb-4 flex items-center space-x-2">
                <Clock size={18} />
                <span>Latest Prediction</span>
              </h3>
              
              {predictions.length > 0 && (
                <div className="space-y-4">
                  <div className="text-center p-4 bg-gradient-to-r from-primary-500/10 to-secondary-500/10 rounded-lg border border-primary-500/20">
                    <p className="text-gray-400 text-sm">24h Forecast</p>
                    <p className="text-2xl font-bold text-white mt-1">
                      ${predictions[0].prediction.price.toFixed(2)}
                    </p>
                    <div className="flex items-center justify-center space-x-2 mt-2">
                      <div className={`w-2 h-2 rounded-full ${
                        predictions[0].prediction.trend === 'bullish' ? 'bg-green-500' :
                        predictions[0].prediction.trend === 'bearish' ? 'bg-red-500' : 'bg-yellow-500'
                      }`} />
                      <span className="text-sm text-gray-300 capitalize">
                        {predictions[0].prediction.trend}
                      </span>
                    </div>
                  </div>
                  
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-400">Confidence</span>
                      <span className="text-white font-medium">
                        {(predictions[0].prediction.confidence * 100).toFixed(1)}%
                      </span>
                    </div>
                    <div className="w-full bg-gray-700 rounded-full h-2">
                      <div 
                        className="bg-gradient-to-r from-green-500 to-blue-500 h-2 rounded-full transition-all duration-300"
                        style={{ width: `${predictions[0].prediction.confidence * 100}%` }}
                      />
                    </div>
                  </div>

                  <div className="pt-2 border-t border-white/10">
                    <p className="text-xs text-gray-400 mb-2">Primary Factors:</p>
                    <div className="space-y-1">
                      {predictions[0].explanation.primaryFactors.slice(0, 3).map((factor, index) => (
                        <div key={index} className="flex justify-between text-xs">
                          <span className="text-gray-300">{factor.factor}</span>
                          <span className="text-primary-400 font-medium">
                            {(factor.impact * 100).toFixed(0)}%
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Quick Actions */}
            <div className="card">
              <h3 className="text-lg font-semibold text-white mb-4 flex items-center space-x-2">
                <Layers size={18} />
                <span>Quick Actions</span>
              </h3>
              
              <div className="space-y-3">
                <button className="w-full btn-primary text-left">
                  <div className="flex items-center space-x-3">
                    <BarChart3 size={18} />
                    <div>
                      <p className="font-medium">View Graph Network</p>
                      <p className="text-xs opacity-80">Explore country relationships</p>
                    </div>
                  </div>
                </button>
                
                <button className="w-full btn-secondary text-left">
                  <div className="flex items-center space-x-3">
                    <Activity size={18} />
                    <div>
                      <p className="font-medium">Live Data Feed</p>
                      <p className="text-xs opacity-80">Real-time event monitoring</p>
                    </div>
                  </div>
                </button>
                
                <button className="w-full glass border border-white/20 hover:border-white/30 p-3 rounded-lg transition-all text-left">
                  <div className="flex items-center space-x-3">
                    <Activity size={18} className="text-gray-400" />
                    <div>
                      <p className="font-medium text-white">Request Prediction</p>
                      <p className="text-xs text-gray-400">Generate new forecast</p>
                    </div>
                  </div>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </ErrorBoundary>
  );
};

