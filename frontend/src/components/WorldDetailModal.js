import React, { useState } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { motion } from 'framer-motion';
import { Trash2, Sparkles, AlertTriangle, Globe, Zap, Wind, Activity } from 'lucide-react';
import { toast } from 'sonner';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const MetricCard = ({ label, value, unit = '', icon: Icon }) => (
  <div className="p-4 rounded-sm bg-muted/20 border border-border/50">
    <div className="flex items-center gap-2 mb-2">
      {Icon && <Icon className="w-4 h-4 text-muted-foreground" />}
      <span className="text-[10px] font-mono uppercase tracking-widest text-muted-foreground">{label}</span>
    </div>
    <p className="text-2xl font-mono font-bold">
      {typeof value === 'number' ? value.toFixed(3) : value}{unit}
    </p>
  </div>
);

export const WorldDetailModal = ({ world, open, onClose, onWorldDeleted }) => {
  const [deleting, setDeleting] = useState(false);
  const params = world.world_parameters;
  const metrics = world.substrate_metrics;

  const handleDelete = async () => {
    if (!window.confirm(`Are you sure you want to delete "${world.name}"? This action cannot be undone.`)) {
      return;
    }

    setDeleting(true);
    try {
      await axios.delete(`${API}/worlds/${world.id}`);
      toast.success(`World "${world.name}" deleted`);
      onWorldDeleted(world.id);
      onClose();
    } catch (error) {
      console.error('Error deleting world:', error);
      toast.error('Failed to delete world');
    } finally {
      setDeleting(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[900px] max-h-[90vh] overflow-y-auto bg-card/95 backdrop-blur-xl border-border/50" data-testid="world-detail-modal">
        <DialogHeader>
          <div className="flex items-start justify-between">
            <div>
              <DialogTitle className="text-3xl font-bold tracking-tight mb-2" style={{ fontFamily: 'Rajdhani, sans-serif' }}>
                {world.name}
              </DialogTitle>
              <DialogDescription className="sr-only">
                Detailed view of {world.name} - a {world.classification} at death-world level {world.death_world_level}
              </DialogDescription>
              <div className="flex items-center gap-3">
                <span className={`text-xs font-mono uppercase px-2 py-1 rounded-full border ${
                  world.classification.includes('Sanctuary') ? 'text-green-500 border-green-500/50' :
                  world.classification.includes('Garden') ? 'text-blue-500 border-blue-500/50' :
                  world.classification.includes('Earth') ? 'text-blue-500 border-blue-500/50' :
                  world.classification.includes('Death') ? 'text-red-500 border-red-500/50' :
                  'text-amber-500 border-amber-500/50'
                }`}>
                  {world.classification}
                </span>
                {world.apex_qualified && (
                  <span className="text-xs font-mono uppercase px-2 py-1 rounded-full border text-primary border-primary/50 flex items-center gap-1">
                    <Sparkles className="w-3 h-3" />
                    Apex Qualified
                  </span>
                )}
              </div>
            </div>
            <Button
              data-testid="delete-world-button"
              onClick={handleDelete}
              disabled={deleting}
              variant="outline"
              className="bg-red-500/20 text-red-500 hover:bg-red-500/30 border border-red-500/50 rounded-sm"
            >
              <Trash2 className="w-4 h-4" />
            </Button>
          </div>
        </DialogHeader>

        <div className="space-y-6 py-4">
          {/* Death World Level */}
          <div className="p-6 rounded-sm bg-card/40 backdrop-blur-md border border-border/50">
            <div className="flex items-center justify-between mb-4">
              <span className="text-sm font-mono uppercase tracking-widest text-muted-foreground">Death World Level</span>
              <span className="text-5xl font-mono font-bold text-primary">{world.death_world_level}</span>
            </div>
            <div className="h-2 bg-muted/50 rounded-full overflow-hidden">
              <div 
                className="h-full bg-primary rounded-full glow-primary"
                style={{ width: `${(world.death_world_level / 15) * 100}%` }}
              />
            </div>
            <div className="flex justify-between text-[10px] font-mono text-muted-foreground mt-2">
              <span>1 - Sanctuary</span>
              <span>10 - Earth</span>
              <span>15 - Apocalypse</span>
            </div>
          </div>

          {/* Tabs */}
          <Tabs defaultValue="world" className="w-full">
            <TabsList className="grid w-full grid-cols-2 bg-muted/20">
              <TabsTrigger value="world" data-testid="world-params-tab" className="font-mono uppercase text-xs">World Parameters</TabsTrigger>
              <TabsTrigger value="substrate" data-testid="substrate-metrics-tab" className="font-mono uppercase text-xs">Substrate Physics</TabsTrigger>
            </TabsList>

            <TabsContent value="world" className="space-y-6 mt-6">
              {/* Environmental */}
              <div>
                <h3 className="text-sm font-mono uppercase tracking-widest text-muted-foreground mb-4 flex items-center gap-2">
                  <Globe className="w-4 h-4" />
                  Environmental Parameters
                </h3>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                  <MetricCard label="Gravity" value={params.gravity} unit="G" />
                  <MetricCard label="Gravity Variance" value={params.gravity_variance} />
                  <MetricCard label="Temperature" value={params.temperature_mean} unit="K" />
                  <MetricCard label="Temp Extremes" value={params.temperature_extremes} unit="K" />
                  <MetricCard label="Atmos. Chaos" value={params.atmospheric_chaos} />
                  <MetricCard label="Rotation Var." value={params.rotational_variance} />
                </div>
              </div>

              {/* Energy & Fields */}
              <div>
                <h3 className="text-sm font-mono uppercase tracking-widest text-muted-foreground mb-4 flex items-center gap-2">
                  <Zap className="w-4 h-4" />
                  Energy & Field Dynamics
                </h3>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                  <MetricCard label="Energy Potential" value={params.energy_potential} />
                  <MetricCard label="EM Field Strength" value={params.em_field_strength} />
                  <MetricCard label="Magnetic Field" value={params.magnetic_field} />
                  <MetricCard label="Spatial Distortion" value={params.spatial_distortion} />
                  <MetricCard label="Quantum Stability" value={params.quantum_stability} />
                  <MetricCard label="Coherence Potential" value={params.consciousness_potential} />
                </div>
              </div>

              {/* Life & Survival */}
              <div>
                <h3 className="text-sm font-mono uppercase tracking-widest text-muted-foreground mb-4 flex items-center gap-2">
                  <Activity className="w-4 h-4" />
                  Biological & Survival Metrics
                </h3>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                  <MetricCard label="Bio Viability" value={(params.biological_viability * 100).toFixed(1)} unit="%" />
                  <MetricCard label="Resource Density" value={(params.resource_density * 100).toFixed(1)} unit="%" />
                  <MetricCard label="Hazard Density" value={(params.hazard_density * 100).toFixed(1)} unit="%" />
                  <div className="p-4 rounded-sm bg-muted/20 border border-border/50 md:col-span-3">
                    <div className="flex items-center gap-2 mb-2">
                      <AlertTriangle className="w-4 h-4 text-muted-foreground" />
                      <span className="text-[10px] font-mono uppercase tracking-widest text-muted-foreground">Survival Difficulty</span>
                    </div>
                    <div className="flex items-center gap-4">
                      <p className={`text-4xl font-mono font-bold ${
                        params.survival_difficulty < 3 ? 'text-green-500' :
                        params.survival_difficulty < 5 ? 'text-blue-500' :
                        params.survival_difficulty < 7 ? 'text-amber-500' :
                        params.survival_difficulty < 9 ? 'text-red-500' :
                        'text-purple-500'
                      }`}>
                        {params.survival_difficulty.toFixed(2)} / 10.00
                      </p>
                      <div className="flex-1 h-3 bg-muted/50 rounded-full overflow-hidden">
                        <div 
                          className={`h-full rounded-full ${
                            params.survival_difficulty < 3 ? 'bg-green-500' :
                            params.survival_difficulty < 5 ? 'bg-blue-500' :
                            params.survival_difficulty < 7 ? 'bg-amber-500' :
                            params.survival_difficulty < 9 ? 'bg-red-500' :
                            'bg-purple-500'
                          }`}
                          style={{ width: `${(params.survival_difficulty / 10) * 100}%` }}
                        />
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </TabsContent>

            <TabsContent value="substrate" className="space-y-6 mt-6">
              <div className="p-4 rounded-sm bg-primary/10 border border-primary/50">
                <p className="text-xs font-mono text-muted-foreground">
                  These metrics represent the raw QMRT substrate physics that generated this world. 
                  They show the underlying density, tension, torsion, and coherence phase properties.
                </p>
              </div>

              <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                <MetricCard label="ρΞ Mean Density" value={metrics.mean_density} />
                <MetricCard label="ρΞ Density STD" value={metrics.std_density} />
                <MetricCard label="TΞ Mean Tension" value={metrics.mean_tension} />
                <MetricCard label="TΞ Tension STD" value={metrics.std_tension} />
                <MetricCard label="τΞ Mean Torsion" value={metrics.mean_torsion} />
                <MetricCard label="τΞ Max Torsion" value={metrics.max_torsion} />
                <MetricCard label="ΦΞ Coherence Grad" value={metrics.mean_coherence_gradient} />
                <MetricCard label="ΦΞ Max Gradient" value={metrics.max_coherence_gradient} />
                <MetricCard label="T_eff Mean" value={metrics.mean_temperature} />
                <MetricCard label="T_eff Max" value={metrics.max_temperature} />
                <MetricCard label="Curvature Mean" value={metrics.mean_curvature} />
                <MetricCard label="Curvature Max" value={metrics.max_curvature} />
              </div>
            </TabsContent>
          </Tabs>

          {/* Metadata */}
          <div className="pt-6 border-t border-border/50 space-y-2">
            <div className="flex justify-between text-xs font-mono text-muted-foreground">
              <span>World ID:</span>
              <span>{world.id}</span>
            </div>
            {world.seed && (
              <div className="flex justify-between text-xs font-mono text-muted-foreground">
                <span>Seed:</span>
                <span>{world.seed}</span>
              </div>
            )}
            <div className="flex justify-between text-xs font-mono text-muted-foreground">
              <span>Generated:</span>
              <span>{new Date(world.created_at).toLocaleString()}</span>
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};
