# oil-gnn-prediction
Predicts short-term oil price changes by combining Graph Neural Networks with Gradient Boosted Trees

Frontend structure:
gnn-frontend/src/
├── components/
│   ├── layout/          # Layout components
│   └── ui/              # Reusable UI components
├── pages/               # Main application pages
├── store/               # Zustand state management
├── services/            # API service layer
├── types/               # TypeScript type definitions
├── lib/                 # Utility functions and mock data
├── hooks/               # Custom React hooks
└── assets/              # Images and static files

Graph visualisation:
Library Choice: Cytoscape.js
Performance: Handles 1000+ nodes efficiently with WebGL rendering
Flexibility: Highly customizable layouts and styling
Interactivity: Built-in support for zoom, pan, drag, selection
Layout Algorithms: Multiple options (force-directed, circular, hierarchical, grid)