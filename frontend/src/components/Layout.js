import React from 'react';
import { Atom, Zap, Activity } from 'lucide-react';

export const Layout = ({ children }) => {
  return (
    <div className="min-h-screen bg-[#050505] grid-background">
      {/* Header */}
      <header className="border-b border-border/50 backdrop-blur-xl bg-background/60 sticky top-0 z-50">
        <div className="max-w-[1600px] mx-auto px-4 md:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="w-10 h-10 bg-primary/10 border border-primary/50 rounded-sm flex items-center justify-center glow-primary">
                <Atom className="w-5 h-5 text-primary" />
              </div>
              <div>
                <h1 className="text-xl font-bold tracking-tight uppercase" style={{ fontFamily: 'Rajdhani, sans-serif' }}>
                  QMRT Simulation
                </h1>
                <p className="text-[10px] font-mono uppercase tracking-widest text-muted-foreground">
                  Emergent Spacetime Physics
                </p>
              </div>
            </div>
            <div className="flex items-center gap-6">
              <div className="hidden md:flex items-center gap-2 text-xs">
                <Activity className="w-4 h-4 text-green-500" />
                <span className="font-mono text-muted-foreground">2D/3D READY</span>
              </div>
              <div className="hidden md:flex items-center gap-2 text-xs">
                <Zap className="w-4 h-4 text-primary" />
                <span className="font-mono text-muted-foreground">α = 2.0 VERIFIED</span>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="max-w-[1600px] mx-auto">
        {children}
      </main>

      {/* Footer */}
      <footer className="border-t border-border/50 backdrop-blur-xl bg-background/60 mt-8">
        <div className="max-w-[1600px] mx-auto px-4 md:px-8 py-4">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            <p className="text-xs font-mono text-muted-foreground">
              Quark Medium Relativity Theory — Driven-Dissipative Spacetime Emergence
            </p>
            <p className="text-xs font-mono text-muted-foreground">
              O ~ S² | Universal Exponent α = 2 | 3D Isotropy Confirmed
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
};
