import { useEffect, useState, useRef } from 'react';
import cytoscape from 'cytoscape';
import type { Core, EdgeDefinition, NodeDefinition } from 'cytoscape';
import { getPredictionHistory } from '../services/api';
import type { PredictionRecord } from '../types/api';

export default function GraphView() {
    const [history, setHistory] = useState<PredictionRecord[]>([]);
    const [selectedDate, setSelectedDate] = useState(0);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const cyRef = useRef<Core | null>(null);
    const containerRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        const fetchData = async () => {
            try {
                setLoading(true);
                const data = await getPredictionHistory();
                setHistory(data);
                setError(null);
            } catch (err) {
                setError(err instanceof Error ? err.message : 'Failed to load data');
            } finally {
                setLoading(false);
            }
        };

        fetchData();
    }, []);

    useEffect(() => {
        if (!containerRef.current || history.length === 0) return;

        const record = history[selectedDate];
        if (!record) return;

        // Destroy existing graph
        if (cyRef.current) {
            cyRef.current.destroy();
        }

        // Create graph nodes and edges
        const nodes: NodeDefinition[] = [
            {
                data: {
                    id: 'oil',
                    label: 'WTI Crude Oil',
                    type: 'center',
                    value: record.predicted_close,
                },
            },
        ];

        const edges: EdgeDefinition[] = [];

        // Add top contributors as nodes
        record.top_contributors.forEach((contributor: any, idx: number) => {
            nodes.push({
                data: {
                    id: `country-${idx}`,
                    label: contributor.country,
                    type: 'contributor',
                    contribution: contributor.contribution,
                    percentage: contributor.percentage,
                    attention: contributor.attention_weight,
                },
            });

            edges.push({
                data: {
                    id: `edge-${idx}`,
                    source: `country-${idx}`,
                    target: 'oil',
                    weight: Math.abs(contributor.percentage),
                    contribution: contributor.contribution,
                },
            });
        });

        // Initialize Cytoscape
        cyRef.current = cytoscape({
            container: containerRef.current,
            elements: {
                nodes,
                edges,
            },
            style: [
                {
                    selector: 'node[type="center"]',
                    style: {
                        'background-color': '#3b82f6',
                        label: 'data(label)',
                        color: '#fff',
                        'text-valign': 'center',
                        'text-halign': 'center',
                        width: 80,
                        height: 80,
                        'font-size': '14px',
                        'font-weight': 'bold',
                    },
                },
                {
                    selector: 'node[type="contributor"]',
                    style: {
                        'background-color': (ele: any) => {
                            const contribution = ele.data('contribution');
                            return contribution >= 0 ? '#10b981' : '#ef4444';
                        },
                        label: 'data(label)',
                        color: '#fff',
                        'text-valign': 'center',
                        'text-halign': 'center',
                        width: (ele: any) => {
                            const percentage = Math.abs(ele.data('percentage'));
                            return Math.max(30, Math.min(60, percentage * 3));
                        },
                        height: (ele: any) => {
                            const percentage = Math.abs(ele.data('percentage'));
                            return Math.max(30, Math.min(60, percentage * 3));
                        },
                        'font-size': '11px',
                        'font-weight': 'bold',
                        'text-wrap': 'wrap',
                        'text-max-width': '100px',
                    },
                },
                {
                    selector: 'edge',
                    style: {
                        width: (ele: any) => {
                            const weight = ele.data('weight');
                            return Math.max(1, Math.min(8, weight / 3));
                        },
                        'line-color': (ele: any) => {
                            const contribution = ele.data('contribution');
                            return contribution >= 0 ? '#10b981' : '#ef4444';
                        },
                        'target-arrow-color': (ele: any) => {
                            const contribution = ele.data('contribution');
                            return contribution >= 0 ? '#10b981' : '#ef4444';
                        },
                        'target-arrow-shape': 'triangle',
                        'curve-style': 'bezier',
                    },
                },
            ],
            layout: {
                name: 'circle',
                radius: 250,
            },
            userZoomingEnabled: true,
            userPanningEnabled: true,
            boxSelectionEnabled: false,
        });

        // Add tooltips on hover
        cyRef.current.on('mouseover', 'node[type="contributor"]', (event: any) => {
            const node = event.target;
            const data = node.data();
            node.style({
                'border-width': 3,
                'border-color': '#fbbf24',
            });
            // You could add a custom tooltip here
            console.log(`${data.label}: ${data.contribution >= 0 ? '+' : ''}$${data.contribution.toFixed(3)} (${data.percentage.toFixed(2)}%)`);
        });

        cyRef.current.on('mouseout', 'node[type="contributor"]', (event: any) => {
            event.target.style({
                'border-width': 0,
            });
        });

        return () => {
            if (cyRef.current) {
                cyRef.current.destroy();
            }
        };
    }, [history, selectedDate]);

    if (loading) {
        return (
            <div className="flex items-center justify-center min-h-screen">
                <div className="text-xl text-gray-600">Loading graph...</div>
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

    const currentRecord = history[selectedDate];

    return (
        <div className="min-h-screen bg-gray-50 p-6">
            <div className="max-w-7xl mx-auto">
                {/* Header */}
                <div className="mb-8">
                    <h1 className="text-4xl font-bold text-gray-900 mb-2">
                        Contributor Network Graph
                    </h1>
                    <p className="text-gray-600">
                        Interactive visualization of country contributions to oil price predictions
                    </p>
                </div>

                {/* Info Panel */}
                {currentRecord && (
                    <div className="bg-white rounded-lg shadow p-6 mb-6">
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                            <div>
                                <div className="text-sm text-gray-600">Prediction Date</div>
                                <div className="text-lg font-semibold text-gray-900">
                                    {new Date(currentRecord.prediction_for_date).toLocaleDateString()}
                                </div>
                            </div>
                            <div>
                                <div className="text-sm text-gray-600">Predicted Price</div>
                                <div className="text-lg font-semibold text-blue-600">
                                    ${currentRecord.predicted_close.toFixed(2)}
                                </div>
                            </div>
                            <div>
                                <div className="text-sm text-gray-600">Predicted Change</div>
                                <div className={`text-lg font-semibold ${currentRecord.predicted_delta >= 0 ? 'text-green-600' : 'text-red-600'
                                    }`}>
                                    {currentRecord.predicted_delta >= 0 ? '+' : ''}
                                    ${currentRecord.predicted_delta.toFixed(2)}
                                </div>
                            </div>
                            <div>
                                <div className="text-sm text-gray-600">Contributors</div>
                                <div className="text-lg font-semibold text-gray-900">
                                    {currentRecord.top_contributors.length}
                                </div>
                            </div>
                        </div>
                    </div>
                )}

                {/* Graph Container */}
                <div className="bg-white rounded-lg shadow p-6 mb-6">
                    <div
                        ref={containerRef}
                        className="w-full bg-gray-50 rounded-lg border border-gray-200"
                        style={{ height: '600px' }}
                    />
                </div>

                {/* Date Slider */}
                <div className="bg-white rounded-lg shadow p-6">
                    <div className="mb-4">
                        <label className="block text-sm font-semibold text-gray-700 mb-2">
                            Select Prediction Date ({history.length} available)
                        </label>
                        <input
                            type="range"
                            min="0"
                            max={history.length - 1}
                            value={selectedDate}
                            onChange={(e) => setSelectedDate(parseInt(e.target.value))}
                            className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
                        />
                    </div>
                    <div className="flex justify-between text-sm text-gray-600">
                        <span>Most Recent</span>
                        <span>
                            {currentRecord && new Date(currentRecord.prediction_for_date).toLocaleDateString()}
                        </span>
                        <span>Oldest</span>
                    </div>
                </div>

                {/* Legend */}
                <div className="bg-white rounded-lg shadow p-6 mt-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">Legend</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="flex items-center gap-3">
                            <div className="w-6 h-6 rounded-full bg-green-500"></div>
                            <span className="text-sm text-gray-700">Positive Contribution (Price Increase)</span>
                        </div>
                        <div className="flex items-center gap-3">
                            <div className="w-6 h-6 rounded-full bg-red-500"></div>
                            <span className="text-sm text-gray-700">Negative Contribution (Price Decrease)</span>
                        </div>
                        <div className="flex items-center gap-3">
                            <div className="text-sm text-gray-700">Node Size = Impact Percentage</div>
                        </div>
                        <div className="flex items-center gap-3">
                            <div className="text-sm text-gray-700">Edge Width = Contribution Strength</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
