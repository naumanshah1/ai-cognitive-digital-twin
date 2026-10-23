import React, { createContext, useContext, useState, useMemo } from 'react';
import {
  DEMO_PERSONAS,
  type DemoPersona,
  type DailyTelemetry,
  generatePersonaTelemetry,
} from '../services/demoData';

interface DemoContextType {
  isDemoMode: boolean;
  activePersonaId: string;
  activePersona: DemoPersona;
  personas: DemoPersona[];
  activeTelemetry: DailyTelemetry[];
  setActivePersonaId: (id: string) => void;
  toggleDemoMode: () => void;
  setDemoMode: (enabled: boolean) => void;
}

const DemoContext = createContext<DemoContextType | undefined>(undefined);

export const DemoProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  // Demo mode defaults to true to ensure every reviewer / demo session sees rich, complete reports
  const [isDemoMode, setIsDemoMode] = useState<boolean>(() => {
    const saved = localStorage.getItem('cognitive_twin_demo_mode');
    return saved !== null ? saved === 'true' : true;
  });

  const [activePersonaId, setActivePersonaIdState] = useState<string>(() => {
    const saved = localStorage.getItem('cognitive_twin_demo_persona');
    return saved && DEMO_PERSONAS[saved] ? saved : 'balanced_work';
  });

  const setActivePersonaId = (id: string) => {
    if (DEMO_PERSONAS[id]) {
      setActivePersonaIdState(id);
      localStorage.setItem('cognitive_twin_demo_persona', id);
    }
  };

  const toggleDemoMode = () => {
    setIsDemoMode((prev) => {
      const next = !prev;
      localStorage.setItem('cognitive_twin_demo_mode', String(next));
      return next;
    });
  };

  const setDemoMode = (enabled: boolean) => {
    setIsDemoMode(enabled);
    localStorage.setItem('cognitive_twin_demo_mode', String(enabled));
  };

  const activePersona = useMemo(() => {
    return DEMO_PERSONAS[activePersonaId] || DEMO_PERSONAS['balanced_work'];
  }, [activePersonaId]);

  const activeTelemetry = useMemo(() => {
    return generatePersonaTelemetry(activePersonaId, 90);
  }, [activePersonaId]);

  const personas = useMemo(() => {
    return Object.values(DEMO_PERSONAS);
  }, []);

  return (
    <DemoContext.Provider
      value={{
        isDemoMode,
        activePersonaId,
        activePersona,
        personas,
        activeTelemetry,
        setActivePersonaId,
        toggleDemoMode,
        setDemoMode,
      }}
    >
      {children}
    </DemoContext.Provider>
  );
};

export const useDemo = (): DemoContextType => {
  const context = useContext(DemoContext);
  if (!context) {
    throw new Error('useDemo must be used within a DemoProvider');
  }
  return context;
};
