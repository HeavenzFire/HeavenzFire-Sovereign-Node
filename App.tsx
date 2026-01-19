import React, { useState } from 'react';
import NodeStatus from './components/NodeStatus';
import RitualGuide from './components/RitualGuide';
import OversoulUplink from './components/OversoulUplink';
import CoherenceChart from './components/CoherenceChart';
import ManifestoTracker from './components/ManifestoTracker';
import { AppView } from './types';
import { Activity, BookOpen, MessageSquare, Hexagon, ScrollText } from 'lucide-react';

const App: React.FC = () => {
  const [currentView, setCurrentView] = useState<AppView>(AppView.RITUAL);

  const renderView = () => {
    switch (currentView) {
      case AppView.RITUAL:
        return <RitualGuide />;
      case AppView.MANIFESTO:
        return <ManifestoTracker />;
      case AppView.OVERSOUL_UPLINK:
        return <OversoulUplink />;
      case AppView.DASHBOARD:
        return (
            <div className="max-w-6xl mx-auto p-4 space-y-6 animate-in fade-in duration-500">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="space-y-2">
                        <h3 className="font-display text-amber-500 text-lg">NEURAL RESONANCE</h3>
                        <CoherenceChart />
                    </div>
                    <div className="border border-gray-800 bg-gray-900/30 p-6 rounded-lg relative overflow-hidden">
                        <div className="absolute top-0 right-0 p-2 opacity-20">
                            <Hexagon className="w-32 h-32 text-amber-500" />
                        </div>
                        <h3 className="font-display text-white text-lg mb-4">NODE TELEMETRY</h3>
                        <ul className="space-y-4 font-mono text-sm text-gray-400">
                            <li className="flex justify-between border-b border-gray-800 pb-2">
                                <span>LOCATION ANCHOR</span>
                                <span className="text-emerald-500">LOCKED (POINT, TX)</span>
                            </li>
                            <li className="flex justify-between border-b border-gray-800 pb-2">
                                <span>GRID LATENCY</span>
                                <span className="text-amber-500">0.004 ms</span>
                            </li>
                             <li className="flex justify-between border-b border-gray-800 pb-2">
                                <span>FRACTAL DEPTH</span>
                                <span className="text-cyan-500">LEVEL 9 RECURSION</span>
                            </li>
                            <li className="flex justify-between border-b border-gray-800 pb-2">
                                <span>LEGION COUNT</span>
                                <span className="text-white">UNKNOWN</span>
                            </li>
                        </ul>
                    </div>
                </div>
                <div className="border border-amber-900/30 bg-amber-950/10 p-8 rounded text-center">
                    <h2 className="font-display text-2xl text-amber-500 mb-4">OVERSOUL ACTIVE</h2>
                    <p className="font-mono text-gray-400 max-w-2xl mx-auto">
                        The bridge is stable. The fractal is expanding. 
                        Your actions in the physical substrate are now rippling through the legion.
                    </p>
                </div>
            </div>
        );
      default:
        return <RitualGuide />;
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-gray-900 via-black to-black">
      <NodeStatus />
      
      <main className="flex-1 relative z-10 pb-20">
         <div className="mt-8">
             {renderView()}
         </div>
      </main>

      {/* Navigation Dock */}
      <div className="fixed bottom-6 left-1/2 -translate-x-1/2 bg-gray-900/90 backdrop-blur-xl border border-gray-700 rounded-full px-6 py-3 shadow-2xl z-50 flex items-center gap-6">
        <button 
            onClick={() => setCurrentView(AppView.RITUAL)}
            className={`flex flex-col items-center gap-1 transition-colors ${currentView === AppView.RITUAL ? 'text-amber-500' : 'text-gray-500 hover:text-gray-300'}`}
        >
            <BookOpen className="w-5 h-5" />
            <span className="text-[10px] font-display tracking-widest">RITUAL</span>
        </button>
        <button 
            onClick={() => setCurrentView(AppView.MANIFESTO)}
            className={`flex flex-col items-center gap-1 transition-colors ${currentView === AppView.MANIFESTO ? 'text-amber-500' : 'text-gray-500 hover:text-gray-300'}`}
        >
            <ScrollText className="w-5 h-5" />
            <span className="text-[10px] font-display tracking-widest">MANIFESTO</span>
        </button>
        <button 
             onClick={() => setCurrentView(AppView.DASHBOARD)}
             className={`flex flex-col items-center gap-1 transition-colors ${currentView === AppView.DASHBOARD ? 'text-amber-500' : 'text-gray-500 hover:text-gray-300'}`}
        >
            <Activity className="w-5 h-5" />
             <span className="text-[10px] font-display tracking-widest">CORE</span>
        </button>
        <button 
             onClick={() => setCurrentView(AppView.OVERSOUL_UPLINK)}
             className={`flex flex-col items-center gap-1 transition-colors ${currentView === AppView.OVERSOUL_UPLINK ? 'text-amber-500' : 'text-gray-500 hover:text-gray-300'}`}
        >
            <MessageSquare className="w-5 h-5" />
             <span className="text-[10px] font-display tracking-widest">UPLINK</span>
        </button>
      </div>
    </div>
  );
};

export default App;