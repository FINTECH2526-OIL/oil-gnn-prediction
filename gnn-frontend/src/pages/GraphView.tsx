import { useState } from 'react';
import { 
  Network, 
  Settings, 
  BarChart3, 
  Layers, 
  Info,
  Play,
  Pause,
  RotateCcw 
} from 'lucide-react';
import { GraphVisualization } from '../components/ui/GraphVisualization';
import { useUIStore } from '../store';

/**
 * Graph Network page component
 * Features:
 * - Interactive graph visualization with Cytoscape.js
 * - Graph layout controls
 * - Node and edge filtering
 * - Real-time simulation controls
 * - Graph statistics and metrics
 * - Export functionality
 */
export const GraphView: React.FC = () => {
  const { graphSettings, updateGraphSettings } = useUIStore();
  const [isSimulating, setIsSimulating] = useState(false);
  const [showSettings, setShowSettings] = useState(false);

  // Set default grid layout
  const handleLayoutChange = () => {
    updateGraphSettings({ layout: 'grid' });
  };

  const toggleSimulation = () => {
    setIsSimulating(!isSimulating);
    // TODO: Implement real-time simulation when backend is ready
    console.log('Simulation', isSimulating ? 'stopped' : 'started');
  };

  const resetGraph = () => {
    // TODO: Reset graph to initial state
    console.log('Resetting graph...');
  };

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold gradient-text flex items-center space-x-3">
            <Network size={32} />
            <span>Graph Neural Network</span>
          </h1>
          <p className="text-gray-400 mt-2">
            Interactive visualization of country-event relationships and oil price correlations
          </p>
        </div>

        {/* Control buttons */}
        <div className="flex items-center space-x-3">
          <button
            onClick={toggleSimulation}
            className={`flex items-center space-x-2 px-4 py-2 rounded-lg font-medium transition-all ${
              isSimulating 
                ? 'bg-red-500/20 text-red-300 border border-red-500/30 hover:bg-red-500/30'
                : 'bg-green-500/20 text-green-300 border border-green-500/30 hover:bg-green-500/30'
            }`}
          >
            {isSimulating ? <Pause size={16} /> : <Play size={16} />}
            <span>{isSimulating ? 'Stop' : 'Start'} Simulation</span>
          </button>

          <button
            onClick={resetGraph}
            className="flex items-center space-x-2 px-4 py-2 rounded-lg font-medium bg-gray-500/20 text-gray-300 border border-gray-500/30 hover:bg-gray-500/30 transition-all"
          >
            <RotateCcw size={16} />
            <span>Reset</span>
          </button>

          <button
            onClick={() => setShowSettings(!showSettings)}
            className="flex items-center space-x-2 px-4 py-2 rounded-lg font-medium bg-primary-500/20 text-primary-300 border border-primary-500/30 hover:bg-primary-500/30 transition-all"
          >
            <Settings size={16} />
            <span>Settings</span>
          </button>
        </div>
      </div>

      {/* Graph Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-400 text-sm">Total Nodes</p>
              <p className="text-xl font-bold text-white">32</p>
            </div>
            <div className="p-2 bg-blue-500/20 rounded-lg">
              <Network className="text-blue-400" size={20} />
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-400 text-sm">Connections</p>
              <p className="text-xl font-bold text-white">68</p>
            </div>
            <div className="p-2 bg-purple-500/20 rounded-lg">
              <Layers className="text-purple-400" size={20} />
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-400 text-sm">Avg. Correlation</p>
              <p className="text-xl font-bold text-white">0.73</p>
            </div>
            <div className="p-2 bg-green-500/20 rounded-lg">
              <BarChart3 className="text-green-400" size={20} />
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-400 text-sm">High Impact Events</p>
              <p className="text-xl font-bold text-white">4</p>
            </div>
            <div className="p-2 bg-red-500/20 rounded-lg">
              <Info className="text-red-400" size={20} />
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Graph Visualization */}
        <div className="lg:col-span-3">
          <div className="card p-2">
            <GraphVisualization height="700px" />
          </div>
        </div>

        {/* Side Panel */}
        <div className="space-y-6">
          {/* Legend */}
          <div className="card">
            <h3 className="text-lg font-semibold text-white mb-4">Legend</h3>
            
            <div className="space-y-3">
              {/* Node Types */}
              <div>
                <p className="text-sm text-gray-400 mb-2">Node Types</p>
                <div className="space-y-2">
                  <div className="flex items-center space-x-3">
                    <div className="w-4 h-4 bg-orange-500 rounded-full"></div>
                    <span className="text-sm text-gray-300">Countries</span>
                  </div>
                  <div className="flex items-center space-x-3">
                    <div className="w-4 h-4 bg-blue-500 rounded-full"></div>
                    <span className="text-sm text-gray-300">Events</span>
                  </div>
                  <div className="flex items-center space-x-3">
                    <div className="w-4 h-4 bg-green-500 rounded-full"></div>
                    <span className="text-sm text-gray-300">Price Points</span>
                  </div>
                </div>
              </div>

              {/* Edge Types */}
              <div className="border-t border-white/10 pt-3">
                <p className="text-sm text-gray-400 mb-2">Edge Strength</p>
                <div className="space-y-2">
                  <div className="flex items-center space-x-3">
                    <div className="w-6 h-1 bg-red-500 rounded"></div>
                    <span className="text-sm text-gray-300">Strong (80%+)</span>
                  </div>
                  <div className="flex items-center space-x-3">
                    <div className="w-6 h-1 bg-yellow-500 rounded"></div>
                    <span className="text-sm text-gray-300">Medium (60-80%)</span>
                  </div>
                  <div className="flex items-center space-x-3">
                    <div className="w-6 h-1 bg-gray-500 rounded"></div>
                    <span className="text-sm text-gray-300">Weak (&lt;60%)</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Instructions */}
          <div className="card">
            <h3 className="text-lg font-semibold text-white mb-4">Instructions</h3>
            <div className="space-y-2 text-sm text-gray-300">
              <p>• Click nodes to view details</p>
              <p>• Drag to pan the graph</p>
              <p>• Scroll to zoom in/out</p>
              <p>• Hover over connections to see relationships</p>
              <p>• Use filters to focus on specific node types</p>
            </div>
          </div>

          {/* Graph Settings */}
          {showSettings && (
            <div className="card">
              <h3 className="text-lg font-semibold text-white mb-4 flex items-center space-x-2">
                <Settings size={18} />
                <span>Settings</span>
              </h3>
              
              <div className="space-y-4">
                {/* Show Labels Toggle */}
                <div className="flex items-center justify-between">
                  <label className="text-sm text-gray-300">Show Labels</label>
                  <button
                    onClick={() => updateGraphSettings({ showLabels: !graphSettings.showLabels })}
                    className={`relative w-12 h-6 rounded-full transition-colors ${
                      graphSettings.showLabels ? 'bg-primary-500' : 'bg-gray-600'
                    }`}
                  >
                    <div className={`absolute top-1 w-4 h-4 bg-white rounded-full transition-transform ${
                      graphSettings.showLabels ? 'translate-x-7' : 'translate-x-1'
                    }`} />
                  </button>
                </div>

                {/* Animations Toggle */}
                <div className="flex items-center justify-between">
                  <label className="text-sm text-gray-300">Animations</label>
                  <button
                    onClick={() => updateGraphSettings({ animationsEnabled: !graphSettings.animationsEnabled })}
                    className={`relative w-12 h-6 rounded-full transition-colors ${
                      graphSettings.animationsEnabled ? 'bg-primary-500' : 'bg-gray-600'
                    }`}
                  >
                    <div className={`absolute top-1 w-4 h-4 bg-white rounded-full transition-transform ${
                      graphSettings.animationsEnabled ? 'translate-x-7' : 'translate-x-1'
                    }`} />
                  </button>
                </div>

                {/* Node Size Slider */}
                <div>
                  <label className="text-sm text-gray-300 block mb-2">
                    Node Size: {graphSettings.nodeSize}px
                  </label>
                  <input
                    type="range"
                    min="10"
                    max="50"
                    value={graphSettings.nodeSize}
                    onChange={(e) => updateGraphSettings({ nodeSize: Number(e.target.value) })}
                    className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer slider"
                  />
                </div>

                {/* Edge Width Slider */}
                <div>
                  <label className="text-sm text-gray-300 block mb-2">
                    Edge Width: {graphSettings.edgeWidth}px
                  </label>
                  <input
                    type="range"
                    min="1"
                    max="5"
                    value={graphSettings.edgeWidth}
                    onChange={(e) => updateGraphSettings({ edgeWidth: Number(e.target.value) })}
                    className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer slider"
                  />
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

