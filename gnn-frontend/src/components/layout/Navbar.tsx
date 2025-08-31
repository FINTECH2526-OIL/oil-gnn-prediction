import { useState } from 'react';
import { useUIStore } from '../../store';
import { Bell, Settings, User, Search, Menu } from 'lucide-react';
import logo from '../../assets/fintech-logo.png';

interface NavbarProps {
  className?: string;
}

/**
 * Main navigation bar component
 * Features:
 * - NUS Fintech Society logo
 * - Search functionality
 * - Notification bell
 * - User profile menu
 * - Settings access
 * - Responsive hamburger menu for mobile
 */
export const Navbar: React.FC<NavbarProps> = ({ className = '' }) => {
  const { toggleSidebar } = useUIStore();
  const [searchQuery, setSearchQuery] = useState('');
  const [showNotifications, setShowNotifications] = useState(false);
  const [showUserMenu, setShowUserMenu] = useState(false);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    console.log('Searching for:', searchQuery);
    // TODO: Implement search functionality when backend is ready
  };

  return (
    <nav className={`glass-dark border-b border-white/10 ${className}`}>
      <div className="flex items-center justify-between h-16 px-6">
        {/* Left section - Logo and menu toggle */}
        <div className="flex items-center space-x-4">
          {/* Mobile menu toggle */}
          <button
            onClick={toggleSidebar}
            className="p-2 rounded-lg text-gray-400 hover:text-white hover:bg-white/10 transition-colors lg:hidden"
            aria-label="Toggle sidebar"
          >
            <Menu size={20} />
          </button>

          {/* Logo and brand */}
          <div className="flex items-center space-x-3">
            <img 
              src={logo} 
              alt="NUS Fintech Society" 
              className="h-8 w-8 object-contain"
            />
            <div className="hidden sm:block">
              <h1 className="text-lg font-semibold text-white">
                Oil Price Intelligence
              </h1>
              <p className="text-xs text-gray-400 -mt-1">
                Powered by Graph Neural Networks
              </p>
            </div>
          </div>
        </div>

        {/* Center section - Search */}
        <div className="hidden md:flex flex-1 max-w-lg mx-8">
          <form onSubmit={handleSearch} className="w-full">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={18} />
              <input
                type="text"
                placeholder="Search events, countries, predictions..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all"
              />
            </div>
          </form>
        </div>

        {/* Right section - Actions and profile */}
        <div className="flex items-center space-x-3">
          {/* Search button for mobile */}
          <button className="p-2 rounded-lg text-gray-400 hover:text-white hover:bg-white/10 transition-colors md:hidden">
            <Search size={20} />
          </button>

          {/* Notifications */}
          <div className="relative">
            <button
              onClick={() => setShowNotifications(!showNotifications)}
              className="p-2 rounded-lg text-gray-400 hover:text-white hover:bg-white/10 transition-colors relative"
              aria-label="Notifications"
            >
              <Bell size={20} />
              {/* Notification badge */}
              <span className="absolute -top-1 -right-1 h-3 w-3 bg-red-500 rounded-full text-xs flex items-center justify-center">
                <span className="animate-pulse h-2 w-2 bg-red-400 rounded-full"></span>
              </span>
            </button>

            {/* Notifications dropdown */}
            {showNotifications && (
              <div className="absolute right-0 mt-2 w-80 glass-dark rounded-lg shadow-2xl border border-white/10 z-50 animate-slide-up">
                <div className="p-4">
                  <h3 className="text-sm font-semibold text-white mb-3">Recent Alerts</h3>
                  <div className="space-y-3">
                    <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-lg">
                      <p className="text-sm text-red-300 font-medium">High Impact Event</p>
                      <p className="text-xs text-gray-400 mt-1">New sanctions detected affecting oil markets</p>
                      <p className="text-xs text-gray-500 mt-1">2 minutes ago</p>
                    </div>
                    <div className="p-3 bg-yellow-500/10 border border-yellow-500/20 rounded-lg">
                      <p className="text-sm text-yellow-300 font-medium">Price Prediction Update</p>
                      <p className="text-xs text-gray-400 mt-1">Model confidence increased to 94%</p>
                      <p className="text-xs text-gray-500 mt-1">15 minutes ago</p>
                    </div>
                    <div className="p-3 bg-blue-500/10 border border-blue-500/20 rounded-lg">
                      <p className="text-sm text-blue-300 font-medium">New Data Available</p>
                      <p className="text-xs text-gray-400 mt-1">GDELT events updated for 12 countries</p>
                      <p className="text-xs text-gray-500 mt-1">1 hour ago</p>
                    </div>
                  </div>
                  <button className="w-full mt-3 text-xs text-primary-400 hover:text-primary-300 transition-colors">
                    View all notifications
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* Settings */}
          <button className="p-2 rounded-lg text-gray-400 hover:text-white hover:bg-white/10 transition-colors">
            <Settings size={20} />
          </button>

          {/* User profile */}
          <div className="relative">
            <button
              onClick={() => setShowUserMenu(!showUserMenu)}
              className="flex items-center space-x-2 p-2 rounded-lg text-gray-400 hover:text-white hover:bg-white/10 transition-colors"
            >
              <div className="h-8 w-8 bg-gradient-to-r from-primary-500 to-secondary-500 rounded-full flex items-center justify-center">
                <User size={16} className="text-white" />
              </div>
              <span className="hidden sm:block text-sm text-white">Analyst</span>
            </button>

            {/* User menu dropdown */}
            {showUserMenu && (
              <div className="absolute right-0 mt-2 w-48 glass-dark rounded-lg shadow-2xl border border-white/10 z-50 animate-slide-up">
                <div className="p-2">
                  <div className="px-3 py-2 border-b border-white/10">
                    <p className="text-sm font-medium text-white">Research Analyst</p>
                    <p className="text-xs text-gray-400">analyst@fintech.nus.edu</p>
                  </div>
                  <button className="w-full text-left px-3 py-2 text-sm text-gray-300 hover:text-white hover:bg-white/10 rounded transition-colors">
                    Profile Settings
                  </button>
                  <button className="w-full text-left px-3 py-2 text-sm text-gray-300 hover:text-white hover:bg-white/10 rounded transition-colors">
                    API Keys
                  </button>
                  <button className="w-full text-left px-3 py-2 text-sm text-gray-300 hover:text-white hover:bg-white/10 rounded transition-colors">
                    Documentation
                  </button>
                  <hr className="border-white/10 my-1" />
                  <button className="w-full text-left px-3 py-2 text-sm text-red-400 hover:text-red-300 hover:bg-red-500/10 rounded transition-colors">
                    Sign Out
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
};

