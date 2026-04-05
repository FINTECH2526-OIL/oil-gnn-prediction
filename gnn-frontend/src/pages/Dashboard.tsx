import { useEffect, useState } from 'react';
import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    Title,
    Tooltip,
    Legend,
} from 'chart.js';
import { Line } from 'react-chartjs-2';
import type { ChartOptions } from 'chart.js';
import { getPredictionHistory, checkHealth, 
    // triggerBackfill, updatePredictions 
} from '../services/api';
import type { PredictionRecord } from '../types/api';

ChartJS.register(
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    Title,
    Tooltip,
    Legend
);

type DateRange = 7 | 14 | 30;
const DEFAULT_HISTORY_WINDOW = 90; // fetch enough to cover gaps in prediction history

export default function Dashboard() {
    const [history, setHistory] = useState<PredictionRecord[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [dateRange, setDateRange] = useState<DateRange>(30);
    const [apiStatus, setApiStatus] = useState<'healthy' | 'unhealthy' | 'checking'>('checking');
    const [backfillStatus, /*setBackfillStatus*/] = useState<'idle' | 'running' | 'failed' | 'success'>('idle');
    const [updateStatus, /*setUpdateStatus*/] = useState<'idle' | 'checking' | 'updating' | 'success' | 'error'>('idle');
    const [updateMessage, /*setUpdateMessage*/] = useState<string>('');

    // const handleUpdateData = async () => {
    //     try {
    //         setUpdateStatus('checking');
    //         setUpdateMessage('Checking for new data...');
            
    //         const result = await updatePredictions(false);
            
    //         setUpdateStatus('updating');
    //         setUpdateMessage(result.message || 'Updating predictions...');
            
    //         // Wait a bit for processing
    //         await new Promise(resolve => setTimeout(resolve, 2000));
            
    //         // Refresh history
    //         const today = new Date();
    //         const startDate = new Date(today);
    //         startDate.setDate(startDate.getDate() - 30);
    //         const startDateIso = startDate.toISOString().split('T')[0];
            
    //         const newData = await getPredictionHistory({
    //             days: DEFAULT_HISTORY_WINDOW,
    //             startDate: startDateIso,
    //         });
            
    //         setHistory(newData);
    //         setUpdateStatus('success');
    //         setUpdateMessage('Successfully updated! Showing latest predictions.');
            
    //         // Clear success message after 5 seconds
    //         setTimeout(() => {
    //             setUpdateStatus('idle');
    //             setUpdateMessage('');
    //         }, 5000);
    //     } catch (err) {
    //         setUpdateStatus('error');
    //         setUpdateMessage(err instanceof Error ? err.message : 'Update failed');
            
    //         // Clear error after 5 seconds
    //         setTimeout(() => {
    //             setUpdateStatus('idle');
    //             setUpdateMessage('');
    //         }, 5000);
    //     }
    // };

    useEffect(() => {
        const fetchData = async () => {
            try {
                setLoading(true);
                setError(null);

                // Check API health
                try {
                    await checkHealth();
                    setApiStatus('healthy');
                } catch {
                    setApiStatus('unhealthy');
                }

                // Fetch prediction history
                const data = await getPredictionHistory({
                    days: DEFAULT_HISTORY_WINDOW,
                });

                // const latestFeatureDate = data[0]?.feature_date
                //     ? new Date(data[0].feature_date)
                //     : null;
                // const hasRecentCoverage = latestFeatureDate ? latestFeatureDate >= startDate : false;
                // const hasSufficientRecords = data.length >= DEFAULT_HISTORY_WINDOW;

                // if (!hasRecentCoverage || !hasSufficientRecords) {
                //     try {
                //         setBackfillStatus('running');
                //         await triggerBackfill({
                //             days: DEFAULT_HISTORY_WINDOW,
                //             startDate: startDateIso,
                //         });
                //         setBackfillStatus('success');
                //         data = await getPredictionHistory({
                //             days: DEFAULT_HISTORY_WINDOW,
                //             startDate: startDateIso,
                //         });
                //     } catch (backfillError) {
                //         console.error('Backfill attempt failed', backfillError);
                //         setBackfillStatus('failed');
                //     }
                // }

                setHistory(data);
            } catch (err) {
                setError(err instanceof Error ? err.message : 'Failed to load data');
                setApiStatus('unhealthy');
            } finally {
                setLoading(false);
            }
        };

        fetchData();
    }, []);

    const cutoff = new Date();
    cutoff.setDate(cutoff.getDate() - dateRange);
    cutoff.setHours(0, 0, 0, 0);
    const filteredHistory: PredictionRecord[] = history.filter(
        (r) => new Date(r.prediction_for_date + 'T00:00:00') >= cutoff
    );

    // Calculate metrics
    const latestPrediction = history[0];
    const recordsWithActuals = filteredHistory.filter((record) => record.actual_close !== undefined);
    const avgError = recordsWithActuals.length > 0
        ? recordsWithActuals.reduce<number>((sum, record) => sum + Math.abs(record.error_delta ?? 0), 0) / recordsWithActuals.length
        : 0;

    const _asc = [...filteredHistory].reverse();
    const _view = _asc.length > 1 ? _asc.slice(0, -1) : _asc;
    const _preds = _asc.length > 1 ? _asc.slice(1).map(r => r.predicted_close) : _asc.map(r => r.predicted_close);

    // Chart data
    const chartData = {
        labels: _view.map((record) =>
            new Date(record.prediction_for_date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
        ),
        datasets: [
            {
                label: 'Predicted Close Price',
                data: _preds,
                borderColor: 'rgb(59, 130, 246)',
                backgroundColor: 'rgba(59, 130, 246, 0.1)',
                tension: 0.4,
            },
            {
                label: 'Actual Close Price',
                data: _view.map((record) => record.actual_close),
                borderColor: 'rgb(16, 185, 129)',
                backgroundColor: 'rgba(16, 185, 129, 0.1)',
                tension: 0.4,
                spanGaps: true,
            },
        ],
    };

    const chartOptions: ChartOptions<'line'> = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                position: 'top' as const,
            },
            title: {
                display: true,
                text: 'WTI Crude Oil Price Predictions vs Actuals',
                font: {
                    size: 16,
                    weight: 'bold' as const,
                },
            },
            tooltip: {
                callbacks: {
                    label: (context: { dataset: { label?: string }; parsed: { y: number } }) => {
                        const label = context.dataset.label || '';
                        const value = context.parsed.y;
                        return `${label}: $${value.toFixed(2)}`;
                    },
                },
            },
        },
        scales: {
            y: {
                title: {
                    display: true,
                    text: 'Price (USD)',
                },
            },
        },
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center min-h-screen">
                <div className="text-xl text-gray-600">Loading predictions...</div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="flex items-center justify-center min-h-screen">
                <div className="text-xl text-red-600">Error: {error}</div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gray-50 p-6">
            <div className="max-w-7xl mx-auto">
                {/* Header */}
                <div className="mb-8">
                    <div className="flex items-center justify-between mb-4">
                        <h1 className="text-4xl font-bold text-gray-900">
                            Oil Price Prediction Dashboard
                        </h1>
                        {/* Update Button */}
                        {/* <button
                            onClick={handleUpdateData}
                            disabled={updateStatus === 'checking' || updateStatus === 'updating'}
                            className={`
                                flex items-center gap-2 px-6 py-3 rounded-lg font-semibold
                                transition-all duration-200 shadow-md hover:shadow-lg
                                ${updateStatus === 'idle' 
                                    ? 'bg-blue-600 hover:bg-blue-700 text-white' 
                                    : updateStatus === 'success'
                                    ? 'bg-green-600 text-white'
                                    : updateStatus === 'error'
                                    ? 'bg-red-600 text-white'
                                    : 'bg-gray-400 text-white cursor-not-allowed'
                                }
                            `}
                        >
                            {updateStatus === 'checking' && (
                                <>
                                    <svg className="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                    </svg>
                                    Checking...
                                </>
                            )}
                            {updateStatus === 'updating' && (
                                <>
                                    <svg className="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                    </svg>
                                    Updating...
                                </>
                            )}
                            {updateStatus === 'success' && (
                                <>
                                    <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7"></path>
                                    </svg>
                                    Updated!
                                </>
                            )}
                            {updateStatus === 'error' && (
                                <>
                                    <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12"></path>
                                    </svg>
                                    Failed
                                </>
                            )}
                            {updateStatus === 'idle' && (
                                <>
                                    <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
                                    </svg>
                                    Update Data
                                </>
                            )}
                        </button>  */}
                    </div> 
                    
                    <div className="flex items-center gap-4">
                        <div className="flex items-center gap-2">
                            <div className={`w-3 h-3 rounded-full ${apiStatus === 'healthy' ? 'bg-green-500' : 'bg-red-500'}`} />
                            <span className="text-sm text-gray-600">
                                API Status: {apiStatus === 'healthy' ? 'Healthy' : 'Unhealthy'}
                            </span>
                        </div>
                        
                        {updateMessage && (
                            <div className={`text-sm px-3 py-1 rounded ${
                                updateStatus === 'success' ? 'bg-green-100 text-green-800' :
                                updateStatus === 'error' ? 'bg-red-100 text-red-800' :
                                'bg-blue-100 text-blue-800'
                            }`}>
                                {updateMessage}
                            </div>
                        )}
                    </div>
                    
                    {backfillStatus === 'running' && (
                        <div className="mt-2 text-sm text-blue-600">
                            Backfilling recent history, please wait...
                        </div>
                    )}
                    {backfillStatus === 'failed' && (
                        <div className="mt-2 text-sm text-red-600">
                            Unable to backfill recent history automatically. Please try again later.
                        </div>
                    )}
                </div>

                {/* Metrics Cards */}
                <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
                    <div className="bg-white rounded-lg shadow p-6">
                        <div className="text-sm text-gray-600 mb-1">Latest Prediction</div>
                        <div className="text-2xl font-bold text-blue-600">
                            ${latestPrediction?.predicted_close.toFixed(2) || 'N/A'}
                        </div>
                        <div className="text-xs text-gray-500 mt-1">
                            For: {latestPrediction?.prediction_for_date || 'N/A'}
                        </div>
                    </div>

                    <div className="bg-white rounded-lg shadow p-6">
                        <div className="text-sm text-gray-600 mb-1">Predicted Change</div>
                        <div className={`text-2xl font-bold ${(latestPrediction?.predicted_delta || 0) >= 0 ? 'text-green-600' : 'text-red-600'
                            }`}>
                            {(latestPrediction?.predicted_delta || 0) >= 0 ? '+' : ''}
                            ${latestPrediction?.predicted_delta.toFixed(2) || 'N/A'}
                        </div>
                        <div className="text-xs text-gray-500 mt-1">
                            From: ${latestPrediction?.reference_close.toFixed(2) || 'N/A'}
                        </div>
                    </div>

                    <div className="bg-white rounded-lg shadow p-6">
                        <div className="text-sm text-gray-600 mb-1">Avg Prediction Error</div>
                        <div className="text-2xl font-bold text-purple-600">
                            ${avgError.toFixed(2)}
                        </div>
                        <div className="text-xs text-gray-500 mt-1">
                            Last {recordsWithActuals.length} days
                        </div>
                    </div>

                    <div className="bg-white rounded-lg shadow p-6">
                        <div className="text-sm text-gray-600 mb-1">Total Predictions</div>
                        <div className="text-2xl font-bold text-gray-900">
                            {history.length}
                        </div>
                        <div className="text-xs text-gray-500 mt-1">
                            {recordsWithActuals.length} with actuals
                        </div>
                    </div>
                </div>

                {/* Date Range Selector */}
                <div className="bg-white rounded-lg shadow p-6 mb-8">
                    <div className="flex items-center justify-between mb-4">
                        <h2 className="text-xl font-semibold text-gray-900">Price Prediction Chart</h2>
                        <div className="flex gap-2">
                            {([7, 14, 30] as DateRange[]).map((days) => (
                                <button
                                    key={days}
                                    onClick={() => setDateRange(days)}
                                    className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${dateRange === days
                                        ? 'bg-blue-600 text-white'
                                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                                        }`}
                                >
                                    {days}D
                                </button>
                            ))}
                        </div>
                    </div>
                    <div className="h-96">
                        <Line data={chartData} options={chartOptions} />
                    </div>
                </div>

                {/* Top Contributors Table */}
                {latestPrediction && (
                    <div className="bg-white rounded-lg shadow p-6">
                        <h2 className="text-xl font-semibold text-gray-900 mb-4">
                            Top Contributing Countries
                        </h2>
                        <div className="overflow-x-auto">
                            <table className="w-full">
                                <thead>
                                    <tr className="border-b border-gray-200">
                                        <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">
                                            Country
                                        </th>
                                        <th className="text-right py-3 px-4 text-sm font-semibold text-gray-700">
                                            Contribution
                                        </th>
                                        <th className="text-right py-3 px-4 text-sm font-semibold text-gray-700">
                                            Percentage
                                        </th>
                                        <th className="text-right py-3 px-4 text-sm font-semibold text-gray-700">
                                            Raw Prediction
                                        </th>
                                        <th className="text-right py-3 px-4 text-sm font-semibold text-gray-700">
                                            Attention Weight
                                        </th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {latestPrediction.top_contributors.map((contributor, idx) => (
                                        <tr key={idx} className="border-b border-gray-100 hover:bg-gray-50">
                                            <td className="py-3 px-4 text-sm text-gray-900">
                                                {contributor.country}
                                            </td>
                                            <td className={`py-3 px-4 text-sm text-right font-medium ${contributor.contribution >= 0 ? 'text-green-600' : 'text-red-600'
                                                }`}>
                                                {contributor.contribution >= 0 ? '+' : ''}
                                                ${contributor.contribution.toFixed(3)}
                                            </td>
                                            <td className="py-3 px-4 text-sm text-right text-gray-700">
                                                {contributor.percentage.toFixed(2)}%
                                            </td>
                                            <td className="py-3 px-4 text-sm text-right text-gray-700">
                                                ${contributor.raw_prediction.toFixed(3)}
                                            </td>
                                            <td className="py-3 px-4 text-sm text-right text-gray-700">
                                                {contributor.attention_weight.toFixed(4)}
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
