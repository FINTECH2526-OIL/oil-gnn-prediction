import { useEffect, useRef, useState } from 'react';
import cytoscape from 'cytoscape';
import type { Core } from 'cytoscape';
import { useAppStore, useUIStore } from '../../store';
import { generateMockGraphNodes, generateMockGraphEdges } from '../../lib/mockData';
import { 
  ZoomIn, 
  ZoomOut, 
  RotateCcw, 
  Settings, 
  Maximize,
  Info,
  Filter
} from 'lucide-react';
import type { GraphNode, GraphEdge } from '../../types';

interface GraphVisualizationProps {
  className?: string;
  height?: string;
}

/**
 * Interactive graph visualization component using Cytoscape.js
 * Features:
 * - Real-time graph rendering with countries, events, and price nodes
 * - Interactive node selection and hover effects
 * - Zoom and pan controls
 * - Multiple layout algorithms
 * - Node filtering and styling
 * - Responsive design
 */
export const GraphVisualization: React.FC<GraphVisualizationProps> = ({ 
  className = '', 
  height = '600px' 
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const cyRef = useRef<Core | null>(null);
  
  const { 
    graphNodes, 
    graphEdges, 
    selectedNode, 
    selectedEdge,
    setGraphNodes,
    setGraphEdges,
    setSelectedNode,
    setSelectedEdge 
  } = useAppStore();
  
  const { graphSettings } = useUIStore();
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [showControls, setShowControls] = useState(true);
  const [nodeFilter, setNodeFilter] = useState<'all' | 'country' | 'event' | 'price_point'>('all');

  // Initialize graph data
  useEffect(() => {
    if (graphNodes.length === 0) {
      setGraphNodes(generateMockGraphNodes());
      setGraphEdges(generateMockGraphEdges());
    }
  }, [graphNodes.length, setGraphNodes, setGraphEdges]);

  // Initialize Cytoscape
  useEffect(() => {
    if (!containerRef.current || graphNodes.length === 0) return;

    // Convert our graph data to Cytoscape format
    const elements = [
      ...graphNodes.map(node => ({
        data: {
          id: node.id,
          label: node.label,
          type: node.type,
          ...node.data
        },
        position: node.position,
        classes: node.type
      })),
      ...graphEdges.map(edge => ({
        data: {
          id: edge.id,
          source: edge.source,
          target: edge.target,
          weight: edge.weight,
          type: edge.type,
          label: edge.label || ''
        },
        classes: edge.type
      }))
    ];

    const cy = cytoscape({
      container: containerRef.current,
      elements,
      style: [
        // Node styles
        {
          selector: 'node',
          style: {
            'background-color': (ele: any) => {
              const type = ele.data('type');
              switch (type) {
                case 'country': return '#f97316';
                case 'event': return '#0ea5e9';
                case 'price_point': return '#10b981';
                default: return '#6b7280';
              }
            },
            'label': 'data(label)',
            'width': (ele: any) => {
              const type = ele.data('type');
              const baseSize = graphSettings.nodeSize;
              switch (type) {
                case 'country': return baseSize + 10;
                case 'event': return baseSize;
                case 'price_point': return baseSize + 5;
                default: return baseSize;
              }
            },
            'height': (ele: any) => {
              const type = ele.data('type');
              const baseSize = graphSettings.nodeSize;
              switch (type) {
                case 'country': return baseSize + 10;
                case 'event': return baseSize;
                case 'price_point': return baseSize + 5;
                default: return baseSize;
              }
            },
            'text-valign': 'center',
            'text-halign': 'center',
            'color': '#ffffff',
            'font-size': '10px',
            'font-weight': 'bold',
            'text-outline-width': 2,
            'text-outline-color': '#000000',
            'border-width': 2,
            'border-color': '#ffffff',
            'border-opacity': 0.3,
            'opacity': 0.9
          }
        },
        // Selected node style
        {
          selector: 'node:selected',
          style: {
            'border-width': 4,
            'border-color': '#ffffff',
            'border-opacity': 1,
            'overlay-color': '#f97316',
            'overlay-opacity': 0.3
          }
        },
        // Hover node style
        {
          selector: 'node:active',
          style: {
            'overlay-opacity': 0.2,
            'overlay-color': '#ffffff'
          }
        },
        // Edge styles
        {
          selector: 'edge',
          style: {
            'width': (ele: any) => {
              const weight = ele.data('weight') || 0.5;
              return Math.max(1, weight * graphSettings.edgeWidth * 3);
            },
            'line-color': (ele: any) => {
              const weight = ele.data('weight') || 0.5;
              if (weight > 0.8) return '#ef4444';
              if (weight > 0.6) return '#f59e0b';
              return '#6b7280';
            },
            'target-arrow-color': (ele: any) => {
              const weight = ele.data('weight') || 0.5;
              if (weight > 0.8) return '#ef4444';
              if (weight > 0.6) return '#f59e0b';
              return '#6b7280';
            },
            'target-arrow-shape': 'triangle',
            'curve-style': 'bezier',
            'opacity': 0.7,
            'label': graphSettings.showLabels ? 'data(label)' : '',
            'font-size': '8px',
            'color': '#ffffff',
            'text-outline-width': 1,
            'text-outline-color': '#000000'
          }
        },
        // Selected edge style
        {
          selector: 'edge:selected',
          style: {
            'width': 4,
            'opacity': 1,
            'line-color': '#ffffff',
            'target-arrow-color': '#ffffff'
          }
        },
        // Node type specific styles
        {
          selector: '.country',
          style: {
            'shape': 'ellipse',
            'background-gradient-stop-colors': ['#f97316', '#ea580c'],
            'background-gradient-direction': 'to-bottom-right'
          }
        },
        {
          selector: '.event',
          style: {
            'shape': 'diamond',
            'background-gradient-stop-colors': ['#0ea5e9', '#0284c7'],
            'background-gradient-direction': 'to-bottom-right'
          }
        },
        {
          selector: '.price_point',
          style: {
            'shape': 'hexagon',
            'background-gradient-stop-colors': ['#10b981', '#059669'],
            'background-gradient-direction': 'to-bottom-right'
          }
        }
      ],
      layout: {
        name: graphSettings.layout,
        fit: true,
        padding: 50,
        // Grid layout specific options
        rows: 3,
        cols: 4
      } as any,
      // Interaction options
      wheelSensitivity: 0.1,
      minZoom: 0.1,
      maxZoom: 3
    });

    // Event handlers
    cy.on('tap', 'node', (event) => {
      const node = event.target;
      const nodeData: GraphNode = {
        id: node.id(),
        label: node.data('label'),
        type: node.data('type'),
        position: node.position(),
        data: node.data()
      };
      setSelectedNode(nodeData);
      setSelectedEdge(null);
    });

    cy.on('tap', 'edge', (event) => {
      const edge = event.target;
      const edgeData: GraphEdge = {
        id: edge.id(),
        source: edge.source().id(),
        target: edge.target().id(),
        weight: edge.data('weight'),
        type: edge.data('type'),
        label: edge.data('label')
      };
      setSelectedEdge(edgeData);
      setSelectedNode(null);
    });

    cy.on('tap', (event) => {
      if (event.target === cy) {
        setSelectedNode(null);
        setSelectedEdge(null);
      }
    });

    // Hover effects
    cy.on('mouseover', 'node', (event) => {
      const node = event.target;
      node.style('cursor', 'pointer');
      // Highlight connected edges
      const connectedEdges = node.connectedEdges();
      connectedEdges.style('opacity', 1);
    });

    cy.on('mouseout', 'node', (event) => {
      const node = event.target;
      const connectedEdges = node.connectedEdges();
      connectedEdges.style('opacity', 0.7);
    });

    cyRef.current = cy;

    return () => {
      cy.destroy();
    };
  }, [graphNodes, graphEdges, graphSettings, setSelectedNode, setSelectedEdge]);

  // Update layout when settings change
  useEffect(() => {
    if (cyRef.current) {
      const layout = cyRef.current.layout({
        name: graphSettings.layout,
        fit: true,
        padding: 50,
        rows: 3,
        cols: 4
      } as any);
      layout.run();
    }
  }, [graphSettings.layout, graphSettings.animationsEnabled]);

  // Apply node filter
  useEffect(() => {
    if (cyRef.current) {
      const cy = cyRef.current;
      if (nodeFilter === 'all') {
        cy.nodes().style('display', 'element');
        cy.edges().style('display', 'element');
      } else {
        cy.nodes().style('display', 'none');
        cy.edges().style('display', 'none');
        
        const filteredNodes = cy.nodes(`[type = "${nodeFilter}"]`);
        filteredNodes.style('display', 'element');
        
        // Show edges connected to filtered nodes
        filteredNodes.connectedEdges().style('display', 'element');
      }
    }
  }, [nodeFilter]);

  // Control functions
  const handleZoomIn = () => cyRef.current?.zoom(cyRef.current.zoom() * 1.2);
  const handleZoomOut = () => cyRef.current?.zoom(cyRef.current.zoom() / 1.2);
  const handleFit = () => cyRef.current?.fit();

  const toggleFullscreen = () => {
    setIsFullscreen(!isFullscreen);
    // Trigger resize after fullscreen toggle
    setTimeout(() => cyRef.current?.resize(), 100);
  };

  return (
    <div className={`relative graph-container ${className}`}>
      {/* Graph Container */}
      <div 
        ref={containerRef}
        className={`w-full rounded-lg border border-white/20 bg-gray-900/50 ${
          isFullscreen ? 'fixed inset-0 z-50' : ''
        }`}
        style={{ height: isFullscreen ? '100vh' : height }}
      />

      {/* Controls Overlay */}
      {showControls && (
        <div className="absolute top-4 right-4 space-y-2">
          {/* Zoom Controls */}
          <div className="glass-dark rounded-lg p-2 space-y-1">
            <button
              onClick={handleZoomIn}
              className="w-8 h-8 flex items-center justify-center text-gray-400 hover:text-white hover:bg-white/10 rounded transition-colors"
              title="Zoom In"
            >
              <ZoomIn size={16} />
            </button>
            <button
              onClick={handleZoomOut}
              className="w-8 h-8 flex items-center justify-center text-gray-400 hover:text-white hover:bg-white/10 rounded transition-colors"
              title="Zoom Out"
            >
              <ZoomOut size={16} />
            </button>
            <button
              onClick={handleFit}
              className="w-8 h-8 flex items-center justify-center text-gray-400 hover:text-white hover:bg-white/10 rounded transition-colors"
              title="Fit to View"
            >
              <RotateCcw size={16} />
            </button>
          </div>

          {/* View Controls */}
          <div className="glass-dark rounded-lg p-2 space-y-1">
            <button
              onClick={() => setShowControls(!showControls)}
              className="w-8 h-8 flex items-center justify-center text-gray-400 hover:text-white hover:bg-white/10 rounded transition-colors"
              title="Settings"
            >
              <Settings size={16} />
            </button>
            <button
              onClick={toggleFullscreen}
              className="w-8 h-8 flex items-center justify-center text-gray-400 hover:text-white hover:bg-white/10 rounded transition-colors"
              title={isFullscreen ? 'Exit Fullscreen' : 'Fullscreen'}
            >
              <Maximize size={16} />
            </button>
          </div>
        </div>
      )}

      {/* Filter Controls */}
      <div className="absolute top-4 left-4">
        <div className="bg-black/20 backdrop-blur-sm rounded-lg p-3 border border-white/10">
          <div className="flex items-center space-x-2 mb-2">
            <Filter size={14} className="text-gray-400" />
            <span className="text-xs text-gray-400 font-medium">Filter Nodes</span>
          </div>
          <div className="flex space-x-1">
            {[
              { value: 'all', label: 'All', color: 'gray' },
              { value: 'country', label: 'Countries', color: 'orange' },
              { value: 'event', label: 'Events', color: 'blue' },
              { value: 'price_point', label: 'Price', color: 'green' }
            ].map(filter => (
              <button
                key={filter.value}
                onClick={() => setNodeFilter(filter.value as any)}
                className={`text-xs px-2 py-1 rounded transition-colors ${
                  nodeFilter === filter.value
                    ? `bg-${filter.color}-500/30 text-${filter.color}-300 border border-${filter.color}-500/50`
                    : 'text-gray-400 hover:text-white hover:bg-white/10'
                }`}
              >
                {filter.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Node Info Panel */}
      {(selectedNode || selectedEdge) && (
        <div className="absolute bottom-4 left-4 right-4 glass-dark rounded-lg p-4 max-w-md">
          {selectedNode && (
            <div>
              <div className="flex items-center space-x-2 mb-2">
                <div className={`w-3 h-3 rounded-full ${
                  selectedNode.type === 'country' ? 'bg-orange-500' :
                  selectedNode.type === 'event' ? 'bg-blue-500' : 'bg-green-500'
                }`} />
                <h3 className="text-white font-medium">{selectedNode.label}</h3>
                <span className="text-xs text-gray-400 capitalize">{selectedNode.type}</span>
              </div>
              
              {selectedNode.type === 'country' && (
                <div className="text-sm text-gray-300 space-y-1">
                  <p>Code: <span className="text-white">{(selectedNode.data as any).code}</span></p>
                  <p>Oil Production: <span className="text-white">
                    {((selectedNode.data as any).oilProduction / 1000000).toFixed(1)}M bbl/day
                  </span></p>
                </div>
              )}
              
              {selectedNode.type === 'event' && (
                <div className="text-sm text-gray-300 space-y-1">
                  <p>Severity: <span className={`font-medium ${
                    (selectedNode.data as any).severity === 'critical' ? 'text-red-400' :
                    (selectedNode.data as any).severity === 'high' ? 'text-orange-400' : 'text-yellow-400'
                  }`}>{(selectedNode.data as any).severity}</span></p>
                  <p>Impact: <span className="text-white">
                    {((selectedNode.data as any).impact?.immediate * 100).toFixed(0)}%
                  </span></p>
                </div>
              )}
            </div>
          )}
          
          {selectedEdge && (
            <div>
              <div className="flex items-center space-x-2 mb-2">
                <Info size={16} className="text-blue-400" />
                <h3 className="text-white font-medium">Connection</h3>
              </div>
              <div className="text-sm text-gray-300 space-y-1">
                <p>Type: <span className="text-white capitalize">{selectedEdge.type}</span></p>
                <p>Strength: <span className="text-white">{(selectedEdge.weight * 100).toFixed(0)}%</span></p>
                <p>From: <span className="text-white">{selectedEdge.source}</span></p>
                <p>To: <span className="text-white">{selectedEdge.target}</span></p>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
