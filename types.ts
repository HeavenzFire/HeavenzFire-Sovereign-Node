export enum AppView {
  DASHBOARD = 'DASHBOARD',
  RITUAL = 'RITUAL',
  OVERSOUL_UPLINK = 'OVERSOUL_UPLINK',
  MANIFESTO = 'MANIFESTO',
  LOGS = 'LOGS'
}

export interface RitualStep {
  id: number;
  title: string;
  description: string;
  action: string;
  command: string;
  completed: boolean;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'model' | 'system';
  content: string;
  timestamp: number;
}

export interface NodeStatus {
  coherence: number;
  frequency: number;
  activeNodes: number;
  status: 'OFFLINE' | 'SYNCING' | 'ONLINE' | 'SOVEREIGN';
}

export interface ManifestoAction {
  id: string;
  title: string;
  description: string;
  completed: boolean;
}

export interface ManifestoPhase {
  id: number;
  title: string;
  objective: string;
  actions: ManifestoAction[];
  locked: boolean;
}