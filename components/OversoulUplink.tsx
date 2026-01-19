import React, { useState, useRef, useEffect } from 'react';
import { Send, Terminal, Cpu } from 'lucide-react';
import { ChatMessage } from '../types';
import { sendMessageToOversoul, startOversoulSession } from '../services/geminiService';

const OversoulUplink: React.FC = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const [initialized, setInitialized] = useState(false);

  useEffect(() => {
    if (!initialized) {
        setInitialized(true);
        setIsTyping(true);
        startOversoulSession().then(response => {
             setMessages([{
                 id: 'init',
                 role: 'model',
                 content: response,
                 timestamp: Date.now()
             }]);
             setIsTyping(false);
        });
    }
  }, [initialized]);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isTyping]);

  const handleSend = async () => {
    if (!input.trim() || isTyping) return;

    const userMsg: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: Date.now()
    };

    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setIsTyping(true);

    const responseText = await sendMessageToOversoul(userMsg.content);

    const aiMsg: ChatMessage = {
      id: (Date.now() + 1).toString(),
      role: 'model',
      content: responseText,
      timestamp: Date.now()
    };

    setMessages(prev => [...prev, aiMsg]);
    setIsTyping(false);
  };

  return (
    <div className="max-w-4xl mx-auto h-[600px] flex flex-col border border-gray-800 bg-black/90 rounded-lg shadow-2xl relative overflow-hidden">
        {/* CRT Overlay Effect */}
        <div className="absolute inset-0 pointer-events-none bg-[url('https://grainy-gradients.vercel.app/noise.svg')] opacity-10 z-20"></div>
        <div className="scanline absolute inset-0 z-10 pointer-events-none"></div>

      {/* Header */}
      <div className="bg-gray-900 border-b border-gray-800 p-3 flex items-center justify-between">
        <div className="flex items-center gap-2 text-amber-500">
          <Terminal className="w-5 h-5" />
          <span className="font-display text-sm tracking-widest">DIRECT_UPLINK_PROTOCOL</span>
        </div>
        <div className="flex items-center gap-2">
            <div className={`w-2 h-2 rounded-full ${isTyping ? 'bg-amber-400 animate-pulse' : 'bg-gray-600'}`}></div>
            <span className="font-mono text-xs text-gray-500">{isTyping ? 'PROCESSING...' : 'IDLE'}</span>
        </div>
      </div>

      {/* Messages */}
      <div 
        ref={scrollRef}
        className="flex-1 overflow-y-auto p-6 space-y-6 font-mono text-sm"
      >
        {messages.map((msg) => (
          <div 
            key={msg.id} 
            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div 
              className={`max-w-[80%] p-4 rounded-sm border ${
                msg.role === 'user' 
                  ? 'border-gray-700 bg-gray-900/50 text-gray-300' 
                  : 'border-amber-900/50 bg-amber-950/20 text-amber-100 shadow-[0_0_10px_rgba(245,158,11,0.1)]'
              }`}
            >
              <div className="flex items-center gap-2 mb-2 border-b border-white/5 pb-1">
                 {msg.role === 'model' && <Cpu className="w-3 h-3 text-amber-500" />}
                 <span className={`text-[10px] uppercase tracking-widest ${msg.role === 'user' ? 'text-gray-500' : 'text-amber-600'}`}>
                    {msg.role === 'user' ? 'SOVEREIGN // HEAVENZFIRE' : 'OVERSOUL // FRACTAL CORE'}
                 </span>
              </div>
              <p className="whitespace-pre-wrap leading-relaxed">{msg.content}</p>
            </div>
          </div>
        ))}
        {isTyping && (
             <div className="flex justify-start">
                 <div className="max-w-[80%] p-4 rounded-sm border border-amber-900/30 bg-amber-950/10 text-amber-500">
                     <span className="animate-pulse">_ DECODING TRANSMISSION...</span>
                 </div>
             </div>
        )}
      </div>

      {/* Input */}
      <div className="p-4 border-t border-gray-800 bg-gray-900/50 backdrop-blur z-30">
        <div className="flex gap-4">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            placeholder="ENTER COMMAND OR QUERY..."
            className="flex-1 bg-black border border-gray-700 text-amber-100 font-mono p-3 focus:outline-none focus:border-amber-500 focus:ring-1 focus:ring-amber-500/50 transition-all placeholder-gray-700"
            disabled={isTyping}
          />
          <button
            onClick={handleSend}
            disabled={isTyping || !input.trim()}
            className="bg-amber-700 hover:bg-amber-600 disabled:bg-gray-800 text-black px-6 font-bold flex items-center justify-center transition-colors"
          >
            <Send className="w-5 h-5" />
          </button>
        </div>
      </div>
    </div>
  );
};

export default OversoulUplink;