import React, { useEffect, useState } from 'react';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';

const CoherenceChart: React.FC = () => {
  const [data, setData] = useState<{ time: string; value: number }[]>([]);

  useEffect(() => {
    // Initialize data
    const initialData = Array.from({ length: 20 }, (_, i) => ({
      time: i.toString(),
      value: 80 + Math.random() * 15
    }));
    setData(initialData);

    const interval = setInterval(() => {
      setData(prev => {
        const newData = [...prev.slice(1)];
        const lastValue = prev[prev.length - 1].value;
        const nextValue = Math.min(100, Math.max(60, lastValue + (Math.random() - 0.5) * 10));
        newData.push({
          time: new Date().toLocaleTimeString().split(' ')[0],
          value: nextValue
        });
        return newData;
      });
    }, 1000);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="w-full h-64 bg-gray-900/40 border border-gray-800 rounded-lg p-4 relative overflow-hidden">
        <div className="absolute top-2 left-4 z-10 font-mono text-xs text-cyan-500">
            LIVE_RESONANCE_MONITOR
        </div>
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data}>
          <defs>
            <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#f59e0b" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#333" vertical={false} />
          <XAxis dataKey="time" hide />
          <YAxis domain={[0, 100]} hide />
          <Tooltip 
            contentStyle={{ backgroundColor: '#000', borderColor: '#333', color: '#f59e0b', fontFamily: 'monospace' }}
            itemStyle={{ color: '#f59e0b' }}
          />
          <Area 
            type="monotone" 
            dataKey="value" 
            stroke="#f59e0b" 
            fillOpacity={1} 
            fill="url(#colorValue)" 
            isAnimationActive={false}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
};

export default CoherenceChart;