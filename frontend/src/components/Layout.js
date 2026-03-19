import React from 'react';
import { Activity, Zap, Layers } from 'lucide-react';
import { motion } from 'framer-motion';

export const Layout = ({ children }) => {
  return (
    <div className="min-h-screen bg-[#050505] grid-background">
      {/* Header */}
      <header className="border-b border-border/50 backdrop-blur-xl bg-background/60 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 md:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="w-10 h-10 bg-primary/10 border border-primary/50 rounded-sm flex items-center justify-center glow-primary">
                <Layers className="w-5 h-5 text-primary" />
              </div>
              <div>
                <h1 className="text-xl font-bold tracking-tight uppercase" style={{ fontFamily: 'Rajdhani, sans-serif' }}>
                  QMRT Nexus
                </h1>
                <p className="text-[10px] font-mono uppercase tracking-widest text-muted-foreground">
                  Simulation Universe Control
                </p>
              </div>
            </div>
            <div className="flex items-center gap-6">
              <div className="hidden md:flex items-center gap-2 text-xs">
                <Activity className="w-4 h-4 text-green-500" />
                <span className="font-mono text-muted-foreground">SUBSTRATE ONLINE</span>
              </div>
              <div className="hidden md:flex items-center gap-2 text-xs">
                <Zap className="w-4 h-4 text-primary" />
                <span className="font-mono text-muted-foreground">QMRT v1.0</span>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="max-w-7xl mx-auto px-4 md:px-8 py-8">
        {children}
      </main>

      {/* Footer */}
      <footer className="border-t border-border/50 backdrop-blur-xl bg-background/60 mt-16">
        <div className="max-w-7xl mx-auto px-4 md:px-8 py-6">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            <p className="text-xs font-mono text-muted-foreground">
              Powered by Quark Medium Relativity Theory
            </p>
            <p className="text-xs font-mono text-muted-foreground">
              Phase A: World Generation & Death-World Scaling
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
};
