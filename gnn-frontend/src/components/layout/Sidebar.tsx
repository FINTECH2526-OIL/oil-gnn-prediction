import { useLocation, useNavigate } from 'react-router-dom';
import { useUIStore } from '../../store';
import { 
  BarChart3, 
  Network, 
  Activity, 
  Globe, 
  TrendingUp,
  ChevronLeft,
  Info,
  Zap
} from 'lucide-react';

interface SidebarProps {
  className?: string;
}

/**
 * Sidebar navigation component
 * Features:
 * - Main navigation items for /dashboard, /graph, /scenarios
 * - Collapsible design
 * - Active route highlighting
 * - Quick stats section
 * - Recent activity feed
 */
export const Sidebar: React.FC<SidebarProps> = ({ className = '' }) => {
  const location = useLocation();
  const navigate = useNavigate();
  const { sidebarCollapsed, toggleSidebar } = useUIStore();

  // Navigation items configuration
  const navigationItems = [
    {
      path: '/dashboard',
      label: 'Dashboard',
      icon: BarChart3,
      description: 'Overview & Analytics',
      badge: null,
    },
    {
      path: '/graph',
      label: 'Graph Network',
      icon: Network,
      description: 'Interactive GNN Visualization',
      badge: 'Live',
    },
  ];

  // Quick stats data (mock data for now)
  const quickStats = [
    { label: 'Active Countries', value: '23', change: '+2', icon: Globe },
    { label: 'Live Events', value: '156', change: '+12', icon: Activity },
    { label: 'Model Accuracy', value: '94.2%', change: '+1.2%', icon: TrendingUp },
  ];

  const isActive = (path: string) => location.pathname === path;

  return (
    <aside 
      className={`glass-dark border-r border-white/10 transition-all duration-300 ${
        sidebarCollapsed ? 'w-16' : 'w-64'
      } ${className}`}
    >
      <div className="flex flex-col h-full overflow-hidden">
        {/* Collapse toggle */}
        <div className="flex items-center justify-end p-4 border-b border-white/10">
          <button
            onClick={toggleSidebar}
            className="p-2 rounded-lg text-gray-400 hover:text-white hover:bg-white/10 transition-colors"
            aria-label={sidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          >
            <ChevronLeft 
              size={18} 
              className={`transition-transform duration-200 ${
                sidebarCollapsed ? 'rotate-180' : ''
              }`} 
            />
          </button>
        </div>

        {/* Main Navigation */}
        <nav className="flex-1 px-4 py-6 overflow-y-auto sidebar-scroll">
          <div className="space-y-2">
            {navigationItems.map((item) => {
              const Icon = item.icon;
              const active = isActive(item.path);
              
              return (
                <button
                  key={item.path}
                  onClick={() => navigate(item.path)}
                  className={`w-full nav-item group ${active ? 'active' : ''}`}
                  title={sidebarCollapsed ? item.label : undefined}
                >
                  <Icon size={20} className="flex-shrink-0" />
                  
                  {!sidebarCollapsed && (
                    <>
                      <div className="flex-1 text-left ml-3">
                        <div className="flex items-center justify-between">
                          <span className="font-medium">{item.label}</span>
                          {item.badge && (
                            <span className="text-xs bg-green-500/20 text-green-400 px-2 py-0.5 rounded-full border border-green-500/30">
                              {item.badge}
                            </span>
                          )}
                        </div>
                        <p className="text-xs text-gray-400 mt-0.5">
                          {item.description}
                        </p>
                      </div>
                    </>
                  )}
                </button>
              );
            })}
          </div>

          {/* Quick Stats Section */}
          {!sidebarCollapsed && (
            <div className="mt-8">
              <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-4 px-3">
                Quick Stats
              </h3>
              <div className="space-y-3">
                {quickStats.map((stat, index) => {
                  const Icon = stat.icon;
                  return (
                    <div key={index} className="glass p-3 rounded-lg">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-2">
                          <Icon size={16} className="text-primary-400" />
                          <span className="text-xs text-gray-400">{stat.label}</span>
                        </div>
                        <span className={`text-xs ${
                          stat.change.startsWith('+') ? 'text-green-400' : 'text-red-400'
                        }`}>
                          {stat.change}
                        </span>
                      </div>
                      <p className="text-lg font-semibold text-white mt-1">{stat.value}</p>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Recent Activity */}
          {!sidebarCollapsed && (
            <div className="mt-8">
              <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-4 px-3">
                Recent Activity
              </h3>
              <div className="space-y-3">
                <div className="flex items-start space-x-3 p-3 glass rounded-lg">
                  <div className="p-1 bg-red-500/20 rounded">
                    <Zap size={12} className="text-red-400" />
                  </div>
                  <div className="flex-1">
                    <p className="text-xs text-white font-medium">High Impact Event</p>
                    <p className="text-xs text-gray-400 mt-1">Russia sanctions detected</p>
                    <p className="text-xs text-gray-500 mt-1">2m ago</p>
                  </div>
                </div>
                
                <div className="flex items-start space-x-3 p-3 glass rounded-lg">
                  <div className="p-1 bg-blue-500/20 rounded">
                    <Activity size={12} className="text-blue-400" />
                  </div>
                  <div className="flex-1">
                    <p className="text-xs text-white font-medium">Model Update</p>
                    <p className="text-xs text-gray-400 mt-1">GNN retrained with new data</p>
                    <p className="text-xs text-gray-500 mt-1">15m ago</p>
                  </div>
                </div>

                <div className="flex items-start space-x-3 p-3 glass rounded-lg">
                  <div className="p-1 bg-green-500/20 rounded">
                    <TrendingUp size={12} className="text-green-400" />
                  </div>
                  <div className="flex-1">
                    <p className="text-xs text-white font-medium">Price Prediction</p>
                    <p className="text-xs text-gray-400 mt-1">$78.45 (+2.3%) 24h forecast</p>
                    <p className="text-xs text-gray-500 mt-1">30m ago</p>
                  </div>
                </div>
              </div>
            </div>
          )}
        </nav>

        {/* Footer info */}
        {!sidebarCollapsed && (
          <div className="p-4 border-t border-white/10">
            <div className="flex items-center space-x-2 text-xs text-gray-400">
              <Info size={14} />
              <span>Model v2.1.0 • API Online</span>
            </div>
            <div className="mt-2 h-1 bg-gray-700 rounded-full overflow-hidden">
              <div className="h-full w-3/4 bg-gradient-to-r from-green-500 to-blue-500 rounded-full"></div>
            </div>
            <p className="text-xs text-gray-500 mt-1">System health: 94%</p>
          </div>
        )}

        {/* Collapsed state tooltip */}
        {sidebarCollapsed && (
          <div className="p-4 border-t border-white/10 flex justify-center">
            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
          </div>
        )}
      </div>
    </aside>
  );
};

