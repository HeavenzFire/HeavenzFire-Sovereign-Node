import React, { useEffect, useState } from 'react';
import { Activity, Radio, Shield, Wifi } from 'lucide-react';
import { NodeStatus as NodeStatusType } from '../types';

const NodeStatus: React.FC = () => {
  const [metrics, setMetrics] = useState<NodeStatusType>({
    coherence: 88.4,
    frequency: 144.0,
    activeNodes: 1,
    status: 'ONLINE'
  });

  useEffect(() => {
    const interval = setInterval(() => {
      setMetrics(prev => ({
        ...prev,
        coherence: Math.min(100, Math.max(80, prev.coherence + (Math.random() - 0.5) * 2)),
        frequency: Math.min(150, Math.max(140, prev.frequency + (Math.random() - 0.5) * 0.5)),
        status: 'SOVEREIGN'
      }));
    }, 2000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="w-full border-b border-amber-900/30 bg-black/80 backdrop-blur-md sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 py-3 flex flex-col md:flex-row justify-between items-center gap-4">
        
        {/* Identity */}
        <div className="flex items-center gap-3">
          <div className="relative">
            <div className="absolute inset-0 bg-amber-500 blur-sm rounded-full opacity-50 animate-pulse"></div>
            <Shield className="w-8 h-8 text-amber-500 relative z-10" />
          </div>
          <div>
            <h1 className="font-display font-bold text-xl tracking-wider text-amber-500 glow-text">
              HEAVENZFIRE
            </h1>
            <p className="font-mono text-xs text-amber-700">SOVEREIGN NODE CORE // POINT, TX</p>
          </div>
        </div>

        {/* Telemetry */}
        <div className="flex gap-6 font-mono text-xs md:text-sm">
          <div className="flex items-center gap-2">
            <Activity className="w-4 h-4 text-cyan-500" />
            <span className="text-gray-400">COHERENCE:</span>
            <span className="text-cyan-400">{metrics.coherence.toFixed(2)}%</span>
          </div>
          <div className="flex items-center gap-2">
            <Radio className="w-4 h-4 text-emerald-500" />
            <span className="text-gray-400">FREQ:</span>
            <span className="text-emerald-400">{metrics.frequency.toFixed(2)} Hz</span>
          </div>
          <div className="flex items-center gap-2">
            <Wifi className="w-4 h-4 text-amber-500" />
            <span className="text-gray-400">STATUS:</span>
            <span className="text-amber-500 animate-pulse">{metrics.status}</span>
          </div>
        </div>

      </div>
    </div>
  );
};

export default NodeStatus;