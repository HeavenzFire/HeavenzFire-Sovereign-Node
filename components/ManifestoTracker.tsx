import React, { useState } from 'react';
import { MANIFESTO_PHASES } from '../constants';
import { ManifestoPhase, ManifestoAction } from '../types';
import { ChevronDown, ChevronUp, Lock, CheckSquare, Square, ShieldAlert } from 'lucide-react';

const ManifestoTracker: React.FC = () => {
  const [phases, setPhases] = useState<ManifestoPhase[]>(MANIFESTO_PHASES);
  const [expandedPhaseId, setExpandedPhaseId] = useState<number | null>(1);

  const togglePhase = (id: number) => {
    if (expandedPhaseId === id) {
      setExpandedPhaseId(null);
    } else {
      setExpandedPhaseId(id);
    }
  };

  const toggleAction = (phaseId: number, actionId: string) => {
    setPhases(prev => prev.map(phase => {
      if (phase.id !== phaseId) return phase;
      
      const updatedActions = phase.actions.map(action => 
        action.id === actionId ? { ...action, completed: !action.completed } : action
      );

      // Check if we should unlock the next phase
      // Logic: If all actions in this phase are complete, unlock the next one (conceptually)
      // For now, we will just handle action toggling.
      
      return { ...phase, actions: updatedActions };
    }));
    
    // Auto-unlock logic could go here
    // But for "Operational Reality", manual unlocking or sequential flow might be better. 
    // Let's implement simple sequential unlocking for the UI effect.
    setTimeout(() => {
        setPhases(currentPhases => {
            const currentPhaseIndex = currentPhases.findIndex(p => p.id === phaseId);
            if (currentPhaseIndex === -1) return currentPhases;
            
            const allComplete = currentPhases[currentPhaseIndex].actions.every(a => a.completed);
            if (allComplete && currentPhaseIndex < currentPhases.length - 1) {
                const nextPhase = currentPhases[currentPhaseIndex + 1];
                if (nextPhase.locked) {
                    return currentPhases.map((p, idx) => idx === currentPhaseIndex + 1 ? { ...p, locked: false } : p);
                }
            }
            return currentPhases;
        });
    }, 500);
  };

  const totalActions = phases.reduce((acc, phase) => acc + phase.actions.length, 0);
  const completedActions = phases.reduce((acc, phase) => acc + phase.actions.filter(a => a.completed).length, 0);
  const progress = (completedActions / totalActions) * 100;

  return (
    <div className="max-w-4xl mx-auto py-4 px-2 pb-24">
      <div className="mb-6 border-b border-gray-800 pb-4 sticky top-0 bg-black/90 backdrop-blur z-20 pt-4">
        <div className="flex justify-between items-end mb-2">
            <div>
                <h2 className="font-display text-2xl text-red-500 flex items-center gap-2">
                    <ShieldAlert className="w-6 h-6" />
                    OPERATIONAL MANIFESTO
                </h2>
                <p className="font-mono text-xs text-red-900/80 uppercase tracking-widest">
                    Execution Protocol: ACTIVE
                </p>
            </div>
            <div className="text-right">
                <span className="font-mono text-2xl text-red-500">{Math.round(progress)}%</span>
                <span className="block text-[10px] text-gray-500 tracking-wider">DEPLOYMENT</span>
            </div>
        </div>
        {/* Progress Bar */}
        <div className="w-full h-1 bg-gray-900 rounded-full overflow-hidden">
            <div 
                className="h-full bg-red-600 transition-all duration-500 ease-out" 
                style={{ width: `${progress}%` }}
            />
        </div>
      </div>

      <div className="space-y-4">
        {phases.map((phase) => {
          const isExpanded = expandedPhaseId === phase.id;
          const isComplete = phase.actions.every(a => a.completed);
          
          return (
            <div 
              key={phase.id}
              className={`
                border rounded-lg transition-all duration-300 overflow-hidden
                ${phase.locked 
                    ? 'border-gray-900 bg-gray-900/20 opacity-60' 
                    : isComplete
                        ? 'border-emerald-900/50 bg-emerald-950/10'
                        : 'border-red-900/30 bg-red-950/10'
                }
              `}
            >
              <button
                onClick={() => !phase.locked && togglePhase(phase.id)}
                disabled={phase.locked}
                className="w-full flex items-center justify-between p-4 text-left"
              >
                <div className="flex items-center gap-4">
                  <div className={`
                    w-8 h-8 flex items-center justify-center rounded font-mono text-sm font-bold
                    ${phase.locked ? 'bg-gray-800 text-gray-500' : isComplete ? 'bg-emerald-900 text-emerald-400' : 'bg-red-900 text-red-100'}
                  `}>
                    {phase.locked ? <Lock className="w-4 h-4" /> : phase.id}
                  </div>
                  <div>
                    <h3 className={`font-display text-lg ${phase.locked ? 'text-gray-500' : isComplete ? 'text-emerald-400' : 'text-red-400'}`}>
                      {phase.title.toUpperCase()}
                    </h3>
                    {!phase.locked && (
                        <p className="font-mono text-xs text-gray-400 hidden md:block">
                            OBJ: {phase.objective}
                        </p>
                    )}
                  </div>
                </div>
                
                {!phase.locked && (
                   isExpanded ? <ChevronUp className="text-gray-500" /> : <ChevronDown className="text-gray-500" />
                )}
              </button>

              {/* Expanded Content */}
              {!phase.locked && (
                  <div className={`
                    border-t border-gray-800/50 bg-black/20
                    transition-all duration-300 ease-in-out
                    ${isExpanded ? 'max-h-[500px] opacity-100' : 'max-h-0 opacity-0'}
                  `}>
                    <div className="p-4 space-y-3">
                        <p className="font-mono text-xs text-gray-500 mb-4 md:hidden">
                            OBJ: {phase.objective}
                        </p>
                        {phase.actions.map(action => (
                            <div 
                                key={action.id}
                                onClick={() => toggleAction(phase.id, action.id)}
                                className={`
                                    flex items-start gap-3 p-3 rounded cursor-pointer border transition-colors group
                                    ${action.completed 
                                        ? 'border-emerald-900/30 bg-emerald-900/10' 
                                        : 'border-gray-800 hover:border-red-500/50 hover:bg-red-900/5'
                                    }
                                `}
                            >
                                <div className={`mt-0.5 ${action.completed ? 'text-emerald-500' : 'text-gray-600 group-hover:text-red-500'}`}>
                                    {action.completed ? <CheckSquare className="w-5 h-5" /> : <Square className="w-5 h-5" />}
                                </div>
                                <div>
                                    <h4 className={`font-display text-sm ${action.completed ? 'text-emerald-400 line-through' : 'text-gray-200'}`}>
                                        {action.title}
                                    </h4>
                                    <p className={`font-mono text-xs mt-1 ${action.completed ? 'text-emerald-700' : 'text-gray-500'}`}>
                                        {action.description}
                                    </p>
                                </div>
                            </div>
                        ))}
                    </div>
                  </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default ManifestoTracker;