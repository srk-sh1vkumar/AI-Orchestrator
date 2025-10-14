import React, { useState } from 'react';
import { Sidebar } from './components/Sidebar';
import { ChatPage } from './pages/ChatPage';
import type { LLMProvider } from './types';

function App() {
  const [selectedProvider, setSelectedProvider] = useState<LLMProvider | undefined>();

  return (
    <div className="h-screen flex overflow-hidden bg-gray-50">
      <Sidebar
        selectedProvider={selectedProvider}
        onProviderSelect={setSelectedProvider}
      />
      <div className="flex-1 flex flex-col overflow-hidden">
        <ChatPage selectedProvider={selectedProvider} />
      </div>
    </div>
  );
}

export default App;
