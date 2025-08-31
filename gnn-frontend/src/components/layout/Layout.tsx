import { Outlet } from 'react-router-dom';
import { useUIStore } from '../../store';
import { Navbar } from './Navbar';
import { Sidebar } from './Sidebar';

/**
 * Main layout component that wraps all pages
 * Features:
 * - Responsive design that adapts to sidebar state
 * - Glass morphism design with gradient backgrounds
 * - Smooth transitions between collapsed/expanded states
 * - Proper content area scrolling
 */
export const Layout: React.FC = () => {
  const { sidebarCollapsed } = useUIStore();

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900">
      {/* Fixed navbar */}
      <Navbar className="fixed top-0 left-0 right-0 z-40" />
      
      <div className="flex pt-16">
        {/* Sidebar */}
        <Sidebar className="fixed left-0 top-16 bottom-0 z-30" />
        
        {/* Main content area */}
        <main 
          className={`flex-1 transition-all duration-300 ${
            sidebarCollapsed ? 'ml-16' : 'ml-64'
          }`}
        >
          {/* Content wrapper with padding and scrolling */}
          <div className="h-[calc(100vh-4rem)] overflow-y-auto">
            <div className="p-6">
              {/* Page content rendered by React Router */}
              <Outlet />
            </div>
          </div>
        </main>
      </div>
      
      {/* Background gradient overlay */}
      <div className="fixed inset-0 pointer-events-none z-0">
        <div className="absolute inset-0 bg-gradient-to-br from-primary-500/5 via-transparent to-secondary-500/5"></div>
        <div className="absolute top-1/4 left-1/4 w-64 h-64 bg-primary-500/10 rounded-full blur-3xl"></div>
        <div className="absolute bottom-1/4 right-1/4 w-64 h-64 bg-secondary-500/10 rounded-full blur-3xl"></div>
      </div>
    </div>
  );
};

