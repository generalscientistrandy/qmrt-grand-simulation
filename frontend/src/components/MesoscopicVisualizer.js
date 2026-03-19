import React, { useState, useEffect, useCallback, useRef } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Slider } from '@/components/ui/slider';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  AreaChart, Area, BarChart, Bar
} from 'recharts';
import { 
  Play, Pause, RotateCcw, Zap, Activity, Wind, Atom, 
  CircleDot, Loader2, AlertCircle, CheckCircle2
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import axios from 'axios';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Custom tooltip for charts
const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-card/95 backdrop-blur-md border border-border/50 rounded-sm p-3 shadow-xl">
        <p className="text-xs font-mono text-muted-foreground mb-1">t = {label?.toFixed(2)}s</p>
        {payload.map((entry, index) => (
          <p key={index} className="text-xs font-mono" style={{ color: entry.color }}>
            {entry.name}: {typeof entry.value === 'number' ? entry.value.toFixed(4) : entry.value}
          </p>
        ))}
      </div>
    );
  }
  return null;
};

// Field visualization grid (2D slice)
const FieldGrid = ({ data, title, colorScale }) => {
  const gridSize = Math.min(data?.length || 0, 32);
  
  if (!data || data.length === 0) {
    return (
      <div className="h-40 flex items-center justify-center text-muted-foreground text-sm">
        No field data
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <p className="text-xs font-mono uppercase tracking-widest text-muted-foreground">{title}</p>
      <div 
        className="grid gap-0.5 mx-auto"
        style={{ 
          gridTemplateColumns: `repeat(${gridSize}, 1fr)`,
          maxWidth: '200px'
        }}
      >
        {data.slice(0, gridSize).map((row, i) => 
          row.slice(0, gridSize).map((value, j) => {
            const normalizedValue = Math.min(1, Math.max(0, (value - 0.5) / 1));
            const intensity = Math.floor(normalizedValue * 255);
            return (
              <div
                key={`${i}-${j}`}
                className="aspect-square rounded-[1px]"
                style={{
                  backgroundColor: colorScale === 'heat' 
                    ? `rgb(${intensity}, ${Math.floor(intensity * 0.3)}, ${255 - intensity})`
                    : `rgb(${intensity}, ${intensity}, ${intensity})`
                }}
              />
            );
          })
        )}
      </div>
    </div>
  );
};

// Structure count indicator
const StructureIndicator = ({ icon: Icon, label, count, color }) => (
  <div className="flex items-center gap-2 p-2 rounded-sm bg-muted/20 border border-border/50">
    <Icon className={`w-4 h-4 ${color}`} />
    <div className="flex-1 min-w-0">
      <p className="text-xs font-mono truncate">{label}</p>
    </div>
    <Badge variant="outline" className="font-mono text-xs">
      {count}
    </Badge>
  </div>
);

export const MesoscopicVisualizer = ({ open, onClose }) => {
  // Simulation state
  const [isRunning, setIsRunning] = useState(false);
  const [simulationData, setSimulationData] = useState(null);
  const [evolutionHistory, setEvolutionHistory] = useState([]);
  const [currentStep, setCurrentStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  // Parameters
  const [gridSize, setGridSize] = useState(32);
  const [amplitude, setAmplitude] = useState(0.1);
  const [totalTime, setTotalTime] = useState(10);
  
  // Animation
  const intervalRef = useRef(null);
  const [playbackSpeed, setPlaybackSpeed] = useState(1);

  // Run simulation
  const runSimulation = async () => {
    setLoading(true);
    setError(null);
    setIsRunning(false);
    setCurrentStep(0);
    setEvolutionHistory([]);
    
    try {
      const response = await axios.post(`${API}/mesoscopic/run`, {
        name: `Visualization_${Date.now()}`,
        grid_size: gridSize,
        amplitude: amplitude,
        total_time: totalTime,
        dt: 0.01,
        seed: Math.floor(Math.random() * 10000)
      }, {
        timeout: 120000  // 2 minute timeout for long simulations
      });
      
      setSimulationData(response.data);
      
      // Process evolution samples for visualization
      const samples = response.data.evolution_samples || [];
      setEvolutionHistory(samples.map((s, idx) => ({
        ...s,
        index: idx,
        time: s.time || idx * (totalTime / samples.length)
      })));
      
      toast.success('Simulation complete!');
    } catch (err) {
      console.error('Simulation error:', err);
      const errorMsg = err.code === 'ECONNABORTED' 
        ? 'Simulation timed out - try reducing duration'
        : (err.response?.data?.detail || 'Simulation failed');
      setError(errorMsg);
      toast.error(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  // Playback controls
  const togglePlayback = useCallback(() => {
    if (isRunning) {
      clearInterval(intervalRef.current);
      setIsRunning(false);
    } else if (evolutionHistory.length > 0) {
      setIsRunning(true);
    }
  }, [isRunning, evolutionHistory.length]);

  const resetPlayback = () => {
    setCurrentStep(0);
    setIsRunning(false);
    clearInterval(intervalRef.current);
  };

  // Animation loop
  useEffect(() => {
    if (isRunning && evolutionHistory.length > 0) {
      intervalRef.current = setInterval(() => {
        setCurrentStep(prev => {
          if (prev >= evolutionHistory.length - 1) {
            setIsRunning(false);
            return prev;
          }
          return prev + 1;
        });
      }, 200 / playbackSpeed);
    }
    
    return () => clearInterval(intervalRef.current);
  }, [isRunning, playbackSpeed, evolutionHistory.length]);

  // Cleanup on close
  useEffect(() => {
    if (!open) {
      clearInterval(intervalRef.current);
      setIsRunning(false);
    }
  }, [open]);

  const currentData = evolutionHistory[currentStep] || {};
  const structures = simulationData?.emergent_structures || {};
  const stability = simulationData?.stability_analysis || {};

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[1200px] max-h-[95vh] overflow-y-auto bg-card/95 backdrop-blur-xl border-border/50" data-testid="mesoscopic-visualizer">
        <DialogHeader>
          <DialogTitle className="text-2xl font-bold tracking-tight uppercase flex items-center gap-3" style={{ fontFamily: 'Rajdhani, sans-serif' }}>
            <Atom className="w-6 h-6 text-primary" />
            Mesoscopic Substrate Visualizer
          </DialogTitle>
          <DialogDescription className="text-sm text-muted-foreground">
            Real-time visualization of QMRT substrate evolution and emergent structure formation
          </DialogDescription>
        </DialogHeader>

        <Tabs defaultValue="simulation" className="w-full">
          <TabsList className="grid w-full grid-cols-3 mb-4">
            <TabsTrigger value="simulation" className="font-mono text-xs uppercase">Simulation</TabsTrigger>
            <TabsTrigger value="structures" className="font-mono text-xs uppercase">Structures</TabsTrigger>
            <TabsTrigger value="energy" className="font-mono text-xs uppercase">Energy</TabsTrigger>
          </TabsList>

          {/* Simulation Tab */}
          <TabsContent value="simulation" className="space-y-4">
            {/* Controls */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 p-4 rounded-sm bg-muted/10 border border-border/50">
              <div className="space-y-2">
                <label className="text-xs font-mono uppercase tracking-widest text-muted-foreground">
                  Grid Size: {gridSize}
                </label>
                <Slider
                  value={[gridSize]}
                  onValueChange={([v]) => setGridSize(v)}
                  min={16}
                  max={64}
                  step={8}
                  disabled={loading}
                  className="w-full"
                />
              </div>
              <div className="space-y-2">
                <label className="text-xs font-mono uppercase tracking-widest text-muted-foreground">
                  Amplitude: {amplitude.toFixed(2)}
                </label>
                <Slider
                  value={[amplitude * 100]}
                  onValueChange={([v]) => setAmplitude(v / 100)}
                  min={5}
                  max={20}
                  step={1}
                  disabled={loading}
                  className="w-full"
                />
              </div>
              <div className="space-y-2">
                <label className="text-xs font-mono uppercase tracking-widest text-muted-foreground">
                  Duration: {totalTime}s
                </label>
                <Slider
                  value={[totalTime]}
                  onValueChange={([v]) => setTotalTime(v)}
                  min={5}
                  max={30}
                  step={5}
                  disabled={loading}
                  className="w-full"
                />
              </div>
            </div>

            {/* Action buttons */}
            <div className="flex items-center gap-3">
              <Button
                onClick={runSimulation}
                disabled={loading}
                className="bg-primary hover:bg-primary/90 font-mono uppercase text-xs"
                data-testid="run-simulation-btn"
              >
                {loading ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Simulating...
                  </>
                ) : (
                  <>
                    <Zap className="w-4 h-4 mr-2" />
                    Run Simulation
                  </>
                )}
              </Button>
              
              {evolutionHistory.length > 0 && (
                <>
                  <Button
                    onClick={togglePlayback}
                    variant="outline"
                    className="font-mono uppercase text-xs"
                    data-testid="playback-toggle-btn"
                  >
                    {isRunning ? (
                      <><Pause className="w-4 h-4 mr-2" /> Pause</>
                    ) : (
                      <><Play className="w-4 h-4 mr-2" /> Play</>
                    )}
                  </Button>
                  <Button
                    onClick={resetPlayback}
                    variant="outline"
                    className="font-mono uppercase text-xs"
                  >
                    <RotateCcw className="w-4 h-4 mr-2" />
                    Reset
                  </Button>
                </>
              )}
            </div>

            {/* Error display */}
            {error && (
              <div className="p-4 rounded-sm bg-destructive/10 border border-destructive/50 flex items-center gap-3">
                <AlertCircle className="w-5 h-5 text-destructive" />
                <p className="text-sm text-destructive">{error}</p>
              </div>
            )}

            {/* Results display */}
            {simulationData && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="space-y-4"
              >
                {/* Progress and current state */}
                <div className="p-4 rounded-sm bg-muted/10 border border-border/50">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-mono uppercase text-muted-foreground">
                      Evolution Progress
                    </span>
                    <span className="text-xs font-mono text-primary">
                      t = {currentData.time?.toFixed(2) || 0}s
                    </span>
                  </div>
                  <Progress 
                    value={(currentStep / Math.max(evolutionHistory.length - 1, 1)) * 100} 
                    className="h-2"
                  />
                  
                  {/* Playback slider */}
                  <Slider
                    value={[currentStep]}
                    onValueChange={([v]) => setCurrentStep(v)}
                    min={0}
                    max={Math.max(evolutionHistory.length - 1, 0)}
                    step={1}
                    className="mt-3"
                  />
                </div>

                {/* Current metrics */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  <div className="p-3 rounded-sm bg-primary/10 border border-primary/50">
                    <p className="text-xs font-mono uppercase text-muted-foreground">Density</p>
                    <p className="text-xl font-mono font-bold text-primary">
                      {currentData.mean_density?.toFixed(4) || '1.0000'}
                    </p>
                  </div>
                  <div className="p-3 rounded-sm bg-secondary/10 border border-secondary/50">
                    <p className="text-xs font-mono uppercase text-muted-foreground">Variance</p>
                    <p className="text-xl font-mono font-bold text-secondary">
                      {currentData.density_variance?.toFixed(6) || '0.000000'}
                    </p>
                  </div>
                  <div className="p-3 rounded-sm bg-orange-500/10 border border-orange-500/50">
                    <p className="text-xs font-mono uppercase text-muted-foreground">Vortices</p>
                    <p className="text-xl font-mono font-bold text-orange-500">
                      {currentData.vortices || 0}
                    </p>
                  </div>
                  <div className="p-3 rounded-sm bg-purple-500/10 border border-purple-500/50">
                    <p className="text-xs font-mono uppercase text-muted-foreground">Particles</p>
                    <p className="text-xl font-mono font-bold text-purple-500">
                      {currentData.particle_nodes || 0}
                    </p>
                  </div>
                </div>

                {/* Field dynamics chart */}
                <div className="p-4 rounded-sm bg-muted/10 border border-border/50">
                  <h4 className="text-sm font-mono uppercase mb-4">Field Dynamics Over Time</h4>
                  <ResponsiveContainer width="100%" height={200}>
                    <LineChart data={evolutionHistory}>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                      <XAxis 
                        dataKey="time" 
                        stroke="rgba(255,255,255,0.5)"
                        tick={{ fontSize: 10 }}
                        tickFormatter={(v) => v.toFixed(1)}
                      />
                      <YAxis 
                        stroke="rgba(255,255,255,0.5)"
                        tick={{ fontSize: 10 }}
                        domain={['auto', 'auto']}
                      />
                      <Tooltip content={<CustomTooltip />} />
                      <Legend wrapperStyle={{ fontSize: '10px' }} />
                      <Line 
                        type="monotone" 
                        dataKey="mean_density" 
                        name="Density"
                        stroke="#00d4ff" 
                        strokeWidth={2}
                        dot={false}
                      />
                      <Line 
                        type="monotone" 
                        dataKey="density_variance" 
                        name="Variance"
                        stroke="#ff6b6b" 
                        strokeWidth={2}
                        dot={false}
                        yAxisId={0}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </motion.div>
            )}
          </TabsContent>

          {/* Structures Tab */}
          <TabsContent value="structures" className="space-y-4">
            {simulationData ? (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="space-y-4"
              >
                {/* Structure summary */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  <StructureIndicator
                    icon={Wind}
                    label="Torsion Vortices"
                    count={structures.torsion_vortices?.count || 0}
                    color="text-orange-500"
                  />
                  <StructureIndicator
                    icon={Zap}
                    label="Strain Nodes"
                    count={structures.strain_nodes?.count || 0}
                    color="text-yellow-500"
                  />
                  <StructureIndicator
                    icon={Activity}
                    label="Coherence Clusters"
                    count={structures.coherence_clusters?.count || 0}
                    color="text-blue-500"
                  />
                  <StructureIndicator
                    icon={CircleDot}
                    label="Particle Nodes"
                    count={structures.particle_nodes?.count || 0}
                    color="text-purple-500"
                  />
                </div>

                {/* Particle classification */}
                <div className="p-4 rounded-sm bg-muted/10 border border-border/50">
                  <h4 className="text-sm font-mono uppercase mb-4">Particle Classification</h4>
                  <div className="grid grid-cols-3 gap-3">
                    <div className="p-3 rounded-sm bg-green-500/10 border border-green-500/50 text-center">
                      <p className="text-2xl font-mono font-bold text-green-500">
                        {structures.particle_nodes?.stable || 0}
                      </p>
                      <p className="text-xs font-mono uppercase text-muted-foreground">Stable</p>
                    </div>
                    <div className="p-3 rounded-sm bg-yellow-500/10 border border-yellow-500/50 text-center">
                      <p className="text-2xl font-mono font-bold text-yellow-500">
                        {structures.particle_nodes?.proto_particle || 0}
                      </p>
                      <p className="text-xs font-mono uppercase text-muted-foreground">Proto</p>
                    </div>
                    <div className="p-3 rounded-sm bg-red-500/10 border border-red-500/50 text-center">
                      <p className="text-2xl font-mono font-bold text-red-500">
                        {structures.particle_nodes?.transient || 0}
                      </p>
                      <p className="text-xs font-mono uppercase text-muted-foreground">Transient</p>
                    </div>
                  </div>
                </div>

                {/* Structure evolution chart */}
                <div className="p-4 rounded-sm bg-muted/10 border border-border/50">
                  <h4 className="text-sm font-mono uppercase mb-4">Structure Formation Over Time</h4>
                  <ResponsiveContainer width="100%" height={200}>
                    <AreaChart data={evolutionHistory}>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                      <XAxis 
                        dataKey="time" 
                        stroke="rgba(255,255,255,0.5)"
                        tick={{ fontSize: 10 }}
                        tickFormatter={(v) => v.toFixed(1)}
                      />
                      <YAxis stroke="rgba(255,255,255,0.5)" tick={{ fontSize: 10 }} />
                      <Tooltip content={<CustomTooltip />} />
                      <Legend wrapperStyle={{ fontSize: '10px' }} />
                      <Area 
                        type="monotone" 
                        dataKey="vortices" 
                        name="Vortices"
                        stackId="1"
                        stroke="#f97316" 
                        fill="#f9731630"
                      />
                      <Area 
                        type="monotone" 
                        dataKey="strain_nodes" 
                        name="Strain Nodes"
                        stackId="2"
                        stroke="#eab308" 
                        fill="#eab30830"
                      />
                      <Area 
                        type="monotone" 
                        dataKey="particle_nodes" 
                        name="Particles"
                        stackId="3"
                        stroke="#a855f7" 
                        fill="#a855f730"
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </motion.div>
            ) : (
              <div className="flex flex-col items-center justify-center py-16 text-muted-foreground">
                <Atom className="w-12 h-12 mb-4 opacity-50" />
                <p className="text-sm">Run a simulation to see emergent structures</p>
              </div>
            )}
          </TabsContent>

          {/* Energy Tab */}
          <TabsContent value="energy" className="space-y-4">
            {simulationData ? (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="space-y-4"
              >
                {/* Energy conservation status */}
                <div className="p-4 rounded-sm bg-muted/10 border border-border/50">
                  <div className="flex items-center gap-3 mb-4">
                    {stability.stable ? (
                      <CheckCircle2 className="w-6 h-6 text-green-500" />
                    ) : (
                      <AlertCircle className="w-6 h-6 text-red-500" />
                    )}
                    <div>
                      <h4 className="font-semibold">
                        {stability.stable ? 'Energy Conserved' : 'Energy Drift Detected'}
                      </h4>
                      <p className="text-xs text-muted-foreground">
                        Zero-balance principle {stability.stable ? 'maintained' : 'violated'}
                      </p>
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-2 gap-4">
                    <div className="p-3 rounded-sm bg-card/40">
                      <p className="text-xs font-mono uppercase text-muted-foreground">Initial Energy</p>
                      <p className="text-lg font-mono font-bold">
                        {simulationData.initial_state?.energy_total?.toFixed(2) || 'N/A'}
                      </p>
                    </div>
                    <div className="p-3 rounded-sm bg-card/40">
                      <p className="text-xs font-mono uppercase text-muted-foreground">Final Energy</p>
                      <p className="text-lg font-mono font-bold">
                        {simulationData.final_state?.energy_total?.toFixed(2) || 'N/A'}
                      </p>
                    </div>
                  </div>
                  
                  {simulationData.initial_state?.energy_total > 0 && (
                    <div className="mt-4">
                      <p className="text-xs font-mono uppercase text-muted-foreground mb-2">
                        Energy Drift
                      </p>
                      <div className="flex items-center gap-3">
                        <Progress 
                          value={Math.min(100, Math.abs(
                            ((simulationData.final_state?.energy_total - simulationData.initial_state?.energy_total) 
                            / simulationData.initial_state?.energy_total) * 100
                          ) * 20)}
                          className="flex-1 h-2"
                        />
                        <span className="text-sm font-mono">
                          {(((simulationData.final_state?.energy_total - simulationData.initial_state?.energy_total) 
                            / simulationData.initial_state?.energy_total) * 100).toFixed(2)}%
                        </span>
                      </div>
                    </div>
                  )}
                </div>

                {/* Energy components visualization */}
                <div className="p-4 rounded-sm bg-muted/10 border border-border/50">
                  <h4 className="text-sm font-mono uppercase mb-4">QMRT Zero-Balance Principle</h4>
                  <p className="text-xs text-muted-foreground mb-4">
                    In the QMRT framework, the universe maintains a finite zero balance. Energy is never 
                    created or destroyed, only transformed between different forms: kinetic, gradient 
                    (potential), torsion, and coherence.
                  </p>
                  
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                    <div className="p-2 rounded-sm bg-primary/10 border border-primary/30 text-center">
                      <p className="text-xs font-mono">Kinetic</p>
                      <p className="text-xs text-muted-foreground">v fields</p>
                    </div>
                    <div className="p-2 rounded-sm bg-secondary/10 border border-secondary/30 text-center">
                      <p className="text-xs font-mono">Gradient</p>
                      <p className="text-xs text-muted-foreground">nabla fields</p>
                    </div>
                    <div className="p-2 rounded-sm bg-orange-500/10 border border-orange-500/30 text-center">
                      <p className="text-xs font-mono">Torsion</p>
                      <p className="text-xs text-muted-foreground">tau_Xi</p>
                    </div>
                    <div className="p-2 rounded-sm bg-purple-500/10 border border-purple-500/30 text-center">
                      <p className="text-xs font-mono">Coherence</p>
                      <p className="text-xs text-muted-foreground">Phi_Xi</p>
                    </div>
                  </div>
                </div>

                {/* Strain energy over time */}
                <div className="p-4 rounded-sm bg-muted/10 border border-border/50">
                  <h4 className="text-sm font-mono uppercase mb-4">Maximum Strain Energy</h4>
                  <ResponsiveContainer width="100%" height={150}>
                    <AreaChart data={evolutionHistory}>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                      <XAxis 
                        dataKey="time" 
                        stroke="rgba(255,255,255,0.5)"
                        tick={{ fontSize: 10 }}
                      />
                      <YAxis stroke="rgba(255,255,255,0.5)" tick={{ fontSize: 10 }} />
                      <Tooltip content={<CustomTooltip />} />
                      <Area 
                        type="monotone" 
                        dataKey="max_strain" 
                        name="Max Strain"
                        stroke="#00d4ff" 
                        fill="#00d4ff30"
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </motion.div>
            ) : (
              <div className="flex flex-col items-center justify-center py-16 text-muted-foreground">
                <Zap className="w-12 h-12 mb-4 opacity-50" />
                <p className="text-sm">Run a simulation to analyze energy conservation</p>
              </div>
            )}
          </TabsContent>
        </Tabs>
      </DialogContent>
    </Dialog>
  );
};
