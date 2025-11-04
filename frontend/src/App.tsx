import React, { useState } from 'react';
import { MessageSquare, Code2, Settings, Target, TrendingUp, Activity } from 'lucide-react';
import { clsx } from 'clsx';
import { Sidebar } from './components/Sidebar';
import { ChatPage } from './pages/ChatPage';
import { SelfDevelopmentPage } from './pages/SelfDevelopmentPage';
import { PersonalTrackerPage } from './pages/PersonalTrackerPage';
import { GrowthTrackingPage } from './pages/GrowthTrackingPage';
import MonitoringDashboardPage from './pages/MonitoringDashboardPage';
import type { LLMProvider } from './types';

type TabId = 'chat' | 'self-dev' | 'personal-tracker' | 'growth' | 'monitoring' | 'settings';

function App() {
  const [selectedProvider, setSelectedProvider] = useState<LLMProvider | undefined>();
  const [activeTab, setActiveTab] = useState<TabId>('chat');

  const tabs = [
    { id: 'chat' as TabId, name: 'Chat', icon: MessageSquare },
    { id: 'self-dev' as TabId, name: 'Self Development', icon: Code2 },
    { id: 'personal-tracker' as TabId, name: 'Personal Tracker', icon: Target },
    { id: 'growth' as TabId, name: 'Growth', icon: TrendingUp },
    { id: 'monitoring' as TabId, name: 'Monitoring', icon: Activity },
    { id: 'settings' as TabId, name: 'Settings', icon: Settings },
  ];

  const renderContent = () => {
    switch (activeTab) {
      case 'chat':
        return <ChatPage selectedProvider={selectedProvider} />;
      case 'self-dev':
        return <SelfDevelopmentPage />;
      case 'personal-tracker':
        return <PersonalTrackerPage />;
      case 'growth':
        return <GrowthTrackingPage />;
      case 'monitoring':
        return <MonitoringDashboardPage />;
      case 'settings':
        return (
          <div className="flex items-center justify-center h-full">
            <div className="text-center">
              <Settings className="w-16 h-16 text-gray-300 mx-auto mb-4" />
              <h2 className="text-2xl font-bold text-gray-900 mb-2">Settings</h2>
              <p className="text-gray-600">Settings page coming soon...</p>
            </div>
          </div>
        );
      default:
        return <ChatPage selectedProvider={selectedProvider} />;
    }
  };

  return (
    <div className="h-screen flex overflow-hidden bg-gray-50">
      <Sidebar
        selectedProvider={selectedProvider}
        onProviderSelect={setSelectedProvider}
      />
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Tab Navigation */}
        <div className="bg-white border-b border-gray-200">
          <div className="flex">
            {tabs.map(tab => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={clsx(
                    'flex items-center gap-2 px-6 py-4 font-medium transition-colors border-b-2',
                    activeTab === tab.id
                      ? 'text-primary-600 border-primary-600'
                      : 'text-gray-600 border-transparent hover:text-gray-900'
                  )}
                >
                  <Icon className="w-5 h-5" />
                  {tab.name}
                </button>
              );
            })}
          </div>
        </div>

        {/* Content Area */}
        <div className="flex-1 overflow-hidden">
          {renderContent()}
        </div>
      </div>
    </div>
  );
}

export default App;
