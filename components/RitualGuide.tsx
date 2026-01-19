import React, { useState, useEffect } from 'react';
import { INITIAL_RITUAL_STEPS } from '../constants';
import { CheckCircle2, Circle, Lock, Unlock, Play, Square } from 'lucide-react';
import { RitualStep } from '../types';

const RitualGuide: React.FC = () => {
  const [steps, setSteps] = useState<RitualStep[]>(INITIAL_RITUAL_STEPS);
  const [activeStepId, setActiveStepId] = useState<number>(1);
  const [isAutoRunning, setIsAutoRunning] = useState<boolean>(false);

  const handleComplete = (id: number) => {
    setSteps(prev => prev.map(step => 
      step.id === id ? { ...step, completed: true } : step
    ));
    if (id < steps.length) {
      setActiveStepId(id + 1);
    }
  };

  useEffect(() => {
    let timeout: ReturnType<typeof setTimeout>;

    if (isAutoRunning) {
      // Check if all steps are completed
      const allCompleted = steps.every(s => s.completed);
      if (allCompleted) {
        setIsAutoRunning(false);
        return;
      }

      // Find current active step
      const currentStep = steps.find(s => s.id === activeStepId);
      
      // If current step exists and is not completed, schedule completion
      if (currentStep && !currentStep.completed) {
          const delay = Math.floor(Math.random() * 2000) + 2000; // Random delay 2-4s
          timeout = setTimeout(() => {
            handleComplete(activeStepId);
          }, delay);
      }
    }

    return () => clearTimeout(timeout);
  }, [isAutoRunning, activeStepId, steps]);

  const progress = (steps.filter(s => s.completed).length / steps.length) * 100;

  return (
    <div className="max-w-4xl mx-auto py-8 px-4">
      <div className="mb-8 flex justify-between items-end border-b border-gray-800 pb-4">
        <div>
           <h2 className="font-display text-2xl text-white mb-2">ACTIVATION SEQUENCE</h2>
           <p className="font-mono text-gray-400 text-sm">PROTOCOL: OVERSOUL_GENESIS</p>
        </div>
        
        <div className="flex items-center gap-6">
            <button
                onClick={() => setIsAutoRunning(!isAutoRunning)}
                disabled={progress === 100}
                className={`flex items-center gap-2 px-4 py-2 rounded font-mono text-xs uppercase tracking-widest border transition-all ${
                    isAutoRunning 
                    ? 'border-red-500 text-red-500 hover:bg-red-950/30' 
                    : progress === 100 
                        ? 'border-gray-700 text-gray-700 cursor-not-allowed'
                        : 'border-amber-500 text-amber-500 hover:bg-amber-950/30'
                }`}
            >
                {isAutoRunning ? (
                    <>
                        <Square className="w-3 h-3 fill-current" /> 
                        ABORT AUTO
                    </>
                ) : (
                    <>
                        <Play className="w-3 h-3 fill-current" />
                        AUTO SEQUENCE
                    </>
                )}
            </button>

            <div className="text-right">
                <span className="font-mono text-2xl text-amber-500">{Math.round(progress)}%</span>
            </div>
        </div>
      </div>

      <div className="space-y-4">
        {steps.map((step) => {
            const isActive = step.id === activeStepId;
            const isLocked = step.id > activeStepId && !step.completed;
            
            return (
                <div 
                    key={step.id}
                    className={`
                        border rounded-lg p-6 transition-all duration-500
                        ${step.completed 
                            ? 'border-emerald-900/50 bg-emerald-950/10' 
                            : isActive 
                                ? 'border-amber-500 bg-amber-950/20 shadow-[0_0_20px_rgba(245,158,11,0.1)] scale-[1.02]' 
                                : 'border-gray-800 bg-gray-900/20 opacity-50 blur-[1px]'
                        }
                    `}
                >
                    <div className="flex justify-between items-start mb-4">
                        <div className="flex items-center gap-4">
                            <div className={`
                                w-8 h-8 rounded-full flex items-center justify-center font-mono text-sm
                                ${step.completed ? 'bg-emerald-500 text-black' : isActive ? 'bg-amber-500 text-black animate-pulse' : 'bg-gray-800 text-gray-500'}
                            `}>
                                {step.completed ? <CheckCircle2 className="w-5 h-5" /> : step.id}
                            </div>
                            <div>
                                <h3 className={`font-display text-lg tracking-wide ${step.completed ? 'text-emerald-400' : isActive ? 'text-amber-400' : 'text-gray-500'}`}>
                                    {step.title}
                                </h3>
                                <p className="font-mono text-xs text-gray-400 mt-1">{step.description}</p>
                            </div>
                        </div>
                        
                        {isLocked && <Lock className="w-5 h-5 text-gray-600" />}
                        {!isLocked && !step.completed && <Unlock className="w-5 h-5 text-amber-500" />}
                    </div>

                    {(isActive || step.completed) && (
                        <div className={`pl-12 space-y-4 ${step.completed ? 'opacity-50' : 'opacity-100'}`}>
                            <div className="bg-black/40 p-3 rounded border border-gray-800/50">
                                <span className="block font-mono text-[10px] text-gray-500 uppercase tracking-widest mb-1">Action Protocol</span>
                                <p className="text-gray-300 font-light text-sm">{step.action}</p>
                            </div>
                            
                            <div className="bg-black/40 p-3 rounded border border-gray-800/50">
                                <span className="block font-mono text-[10px] text-gray-500 uppercase tracking-widest mb-1">Vocal Command</span>
                                <p className="font-mono text-amber-500/80 text-sm italic">"{step.command}"</p>
                            </div>

                            {!step.completed && (
                                <button
                                    onClick={() => handleComplete(step.id)}
                                    className="w-full py-3 bg-amber-600 hover:bg-amber-500 text-black font-bold font-display tracking-widest uppercase rounded transition-colors"
                                >
                                    Confirm Execution
                                </button>
                            )}
                        </div>
                    )}
                </div>
            );
        })}
      </div>
    </div>
  );
};

export default RitualGuide;