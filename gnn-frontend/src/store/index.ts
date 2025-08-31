import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import type { 
  Country, 
  GeopoliticalEvent, 
  OilPrice, 
  PredictionResult,
  GraphNode,
  GraphEdge,
  LoadingState,
  ErrorState,
  RouteType 
} from '../types';

// Main application store
interface AppState {
  // Navigation
  currentRoute: RouteType;
  setCurrentRoute: (route: RouteType) => void;
  
  // Data
  countries: Country[];
  events: GeopoliticalEvent[];
  oilPrices: OilPrice[];
  predictions: PredictionResult[];
  
  // Graph
  graphNodes: GraphNode[];
  graphEdges: GraphEdge[];
  selectedNode: GraphNode | null;
  selectedEdge: GraphEdge | null;
  
  // UI State
  loading: LoadingState;
  error: ErrorState;
  
  // Actions
  setCountries: (countries: Country[]) => void;
  setEvents: (events: GeopoliticalEvent[]) => void;
  setOilPrices: (prices: OilPrice[]) => void;
  setPredictions: (predictions: PredictionResult[]) => void;
  
  setGraphNodes: (nodes: GraphNode[]) => void;
  setGraphEdges: (edges: GraphEdge[]) => void;
  setSelectedNode: (node: GraphNode | null) => void;
  setSelectedEdge: (edge: GraphEdge | null) => void;
  
  setLoading: (loading: LoadingState) => void;
  setError: (error: ErrorState) => void;
  clearError: () => void;
  
  // Computed values
  getCountryById: (id: string) => Country | undefined;
  getEventById: (id: string) => GeopoliticalEvent | undefined;
  getPredictionById: (id: string) => PredictionResult | undefined;
}

export const useAppStore = create<AppState>()(
  devtools(
    (set, get) => ({
      // Initial state
      currentRoute: '/dashboard',
      countries: [],
      events: [],
      oilPrices: [],
      predictions: [],
      graphNodes: [],
      graphEdges: [],
      selectedNode: null,
      selectedEdge: null,
      loading: { isLoading: false },
      error: { hasError: false },

      // Navigation actions
      setCurrentRoute: (route) => set({ currentRoute: route }),

      // Data actions
      setCountries: (countries) => set({ countries }),
      setEvents: (events) => set({ events }),
      setOilPrices: (oilPrices) => set({ oilPrices }),
      setPredictions: (predictions) => set({ predictions }),

      // Graph actions
      setGraphNodes: (graphNodes) => set({ graphNodes }),
      setGraphEdges: (graphEdges) => set({ graphEdges }),
      setSelectedNode: (selectedNode) => set({ selectedNode }),
      setSelectedEdge: (selectedEdge) => set({ selectedEdge }),

      // UI actions
      setLoading: (loading) => set({ loading }),
      setError: (error) => set({ error }),
      clearError: () => set({ error: { hasError: false } }),

      // Computed getters
      getCountryById: (id) => get().countries.find(c => c.id === id),
      getEventById: (id) => get().events.find(e => e.id === id),
      getPredictionById: (id) => get().predictions.find(p => p.id === id),
    }),
    { name: 'oil-gnn-store' }
  )
);

// Separate store for UI preferences and settings
interface UIStore {
  sidebarCollapsed: boolean;
  theme: 'dark' | 'light';
  graphSettings: {
    layout: 'grid';
    showLabels: boolean;
    animationsEnabled: boolean;
    nodeSize: number;
    edgeWidth: number;
  };
  
  toggleSidebar: () => void;
  setTheme: (theme: 'dark' | 'light') => void;
  updateGraphSettings: (settings: Partial<UIStore['graphSettings']>) => void;
}

export const useUIStore = create<UIStore>()(
  devtools(
    (set) => ({
      sidebarCollapsed: false,
      theme: 'dark',
      graphSettings: {
        layout: 'grid',
        showLabels: true,
        animationsEnabled: true,
        nodeSize: 20,
        edgeWidth: 2,
      },

      toggleSidebar: () => set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed })),
      setTheme: (theme) => set({ theme }),
      updateGraphSettings: (settings) => 
        set((state) => ({ 
          graphSettings: { ...state.graphSettings, ...settings } 
        })),
    }),
    { name: 'ui-store' }
  )
);

