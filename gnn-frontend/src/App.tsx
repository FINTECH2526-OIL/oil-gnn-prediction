import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Layout } from './components/layout/Layout';
import Dashboard from './pages/Dashboard';
import GraphView from './pages/GraphView';

/**
 * Main App component with routing configuration
 * 
 * Routes:
 * - /dashboard: Main overview page with metrics and data tables
 * - /graph: Interactive graph network visualization
 * - / (root): Redirects to /dashboard
 * 
 * The app uses React Router v6 with a nested layout structure.
 * All routes are wrapped in the main Layout component which provides
 * the navbar, sidebar, and consistent styling.
 */
function App() {
  return (
    <Router>
      <div className="App">
        <Routes>
          {/* Main layout with nested routes */}
          <Route path="/" element={<Layout />}>
            {/* Redirect root to dashboard */}
            <Route index element={<Navigate to="/dashboard" replace />} />

            {/* Main application routes */}
            <Route path="dashboard" element={<Dashboard />} />
            <Route path="graph" element={<GraphView />} />

            {/* Catch-all route - redirect to dashboard */}
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Route>
        </Routes>
      </div>
    </Router>
  );
}

export default App;