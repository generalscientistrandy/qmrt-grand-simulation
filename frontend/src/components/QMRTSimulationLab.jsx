import React, { useState, useCallback, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Button } from '@/components/ui/button';
import { Slider } from '@/components/ui/slider';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { 
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  AreaChart, Area, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar
} from 'recharts';
import { 
  Play, Pause, RotateCcw, Zap, Activity, Atom, Box, Square,
  Loader2, CheckCircle2, XCircle, Info, TrendingUp
} from 'lucide-react';
import axios from 'axios';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Custom tooltip
const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-card/95 backdrop-blur-md border border-border/50 rounded-sm p-3 shadow-xl">
        <p className="text-xs font-mono text-muted-foreground mb-1">t = {label?.toFixed(2)}</p>
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

// Field visualization (2D heatmap)
const FieldHeatmap = ({ data, title, colorScheme = 'heat' }) => {
  if (!data || data.length === 0) {
    return (
      <div className="h-32 flex items-center justify-center text-muted-foreground text-xs">
        No data
      </div>
    );
  }

  const size = data.length;
  const maxVal = Math.max(...data.flat());
  const minVal = Math.min(...data.flat());
  const range = maxVal - minVal || 1;

  return (
    <div className="space-y-1">
      <p className="text-xs font-mono uppercase tracking-widest text-muted-foreground">{title}</p>
      <div 
        className="grid gap-px mx-auto border border-border/30 rounded-sm overflow-hidden"
        style={{ 
          gridTemplateColumns: `repeat(${size}, 1fr)`,
          width: `${Math.min(size * 6, 200)}px`,
          height: `${Math.min(size * 6, 200)}px`,
        }}
      >
        {data.map((row, i) => 
          row.map((value, j) => {
            const normalized = (value - minVal) / range;
            const intensity = Math.floor(normalized * 255);
            let bgColor;
            if (colorScheme === 'heat') {
              bgColor = `rgb(${intensity}, ${Math.floor(intensity * 0.3)}, ${255 - intensity})`;
            } else if (colorScheme === 'blue') {
              bgColor = `rgb(${255 - intensity}, ${255 - intensity}, 255)`;
            } else {
              bgColor = `rgb(${intensity}, ${intensity}, ${intensity})`;
            }
            return (
              <div
                key={`${i}-${j}`}
                className="aspect-square"
                style={{ backgroundColor: bgColor }}
              />
            );
          })
        )}
      </div>
    </div>
  );
};

// Metric card
const MetricCard = ({ label, value, unit, icon: Icon, color, status }) => (
  <div className={`p-3 rounded-sm border ${color} bg-opacity-10`}>
    <div className="flex items-center justify-between mb-1">
      <span className="text-xs font-mono uppercase text-muted-foreground">{label}</span>
      {status !== undefined && (
        status ? <CheckCircle2 className="w-3 h-3 text-green-500" /> : <XCircle className="w-3 h-3 text-red-500" />
      )}
    </div>
    <div className="flex items-baseline gap-1">
      <span className="text-xl font-mono font-bold">{typeof value === 'number' ? value.toFixed(4) : value}</span>
      {unit && <span className="text-xs text-muted-foreground">{unit}</span>}
    </div>
  </div>
);

export const QMRTSimulationLab = () => {
  // Simulation state
  const [dimension, setDimension] = useState('2d');
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState(null);
  const [playbackIndex, setPlaybackIndex] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  
  // Parameters
  const [gridSize, setGridSize] = useState(60);
  const [alpha, setAlpha] = useState(0.5);
  const [lambdaRelax, setLambdaRelax] = useState(0.5);
  const [gammaWave, setGammaWave] = useState(0.01);
  const [steps, setSteps] = useState(300);
  
  // Playback
  const intervalRef = useRef(null);
  
  // Run simulation
  const runSimulation = async () => {
    setRunning(true);
    setResult(null);
    setPlaybackIndex(0);
    setIsPlaying(false);
    
    try {
      const response = await axios.post(`${API}/qmrt-sim/run`, {
        dimension,
        size: dimension === '3d' ? Math.min(gridSize, 50) : gridSize,
        alpha,
        lambda_relax: lambdaRelax,
        gamma_wave: gammaWave,
        steps,
        sample_interval: 10,
      }, { timeout: 300000 });
      
      setResult(response.data);
      toast.success(`${dimension.toUpperCase()} simulation complete!`);
    } catch (err) {
      console.error('Simulation error:', err);
      toast.error(err.response?.data?.detail || 'Simulation failed');
    } finally {
      setRunning(false);
    }
  };
  
  // Playback controls
  const togglePlayback = useCallback(() => {
    if (isPlaying) {
      clearInterval(intervalRef.current);
      setIsPlaying(false);
    } else if (result?.measurements?.length > 0) {
      setIsPlaying(true);
    }
  }, [isPlaying, result]);
  
  const resetPlayback = () => {
    setPlaybackIndex(0);
    setIsPlaying(false);
    clearInterval(intervalRef.current);
  };
  
  useEffect(() => {
    if (isPlaying && result?.measurements?.length > 0) {
      intervalRef.current = setInterval(() => {
        setPlaybackIndex(prev => {
          if (prev >= result.measurements.length - 1) {
            setIsPlaying(false);
            return prev;
          }
          return prev + 1;
        });
      }, 100);
    }
    return () => clearInterval(intervalRef.current);
  }, [isPlaying, result]);
  
  const currentMeasurement = result?.measurements?.[playbackIndex] || {};
  const currentSnapshot = result?.field_snapshots?.[Math.floor(playbackIndex / 5)] || {};
  
  // Prepare radar data
  const radarData = result ? [
    { subject: 'Balance', value: result.balance_achieved ? 1 : 0, fullMark: 1 },
    { subject: 'S', value: Math.min(result.spatial_S_mean * 10, 1), fullMark: 1 },
    { subject: 'I_TS', value: result.coupling_I_TS_mean, fullMark: 1 },
    { subject: 'Isotropy', value: result.geometry_isotropic ? 1 : 0.5, fullMark: 1 },
    { subject: 'Confined', value: result.geometry_confined ? 1 : 0.5, fullMark: 1 },
  ] : [];
  
  return (
    <div className="min-h-screen bg-background p-6 space-y-6" data-testid="qmrt-simulation-lab">
      {/* Header */}
      <motion.div 
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="space-y-2"
      >
        <div className="flex items-center gap-3">
          <Atom className="w-8 h-8 text-primary" />
          <h1 className="text-3xl md:text-4xl font-bold tracking-tight uppercase" style={{ fontFamily: 'Rajdhani, sans-serif' }}>
            QMRT Simulation Lab
          </h1>
        </div>
        <p className="text-sm text-muted-foreground">
          Quark Medium Relativity Theory — Dynamical medium simulation for emergent spacetime
        </p>
      </motion.div>
      
      {/* Main Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Left Panel: Controls */}
        <Card className="lg:col-span-1 bg-card/50 backdrop-blur-md border-border/50">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-mono uppercase">Simulation Controls</CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Dimension Toggle */}
            <div className="space-y-2">
              <label className="text-xs font-mono uppercase text-muted-foreground">Dimension</label>
              <div className="grid grid-cols-2 gap-2">
                <Button
                  variant={dimension === '2d' ? 'default' : 'outline'}
                  onClick={() => setDimension('2d')}
                  className="font-mono text-xs"
                  disabled={running}
                  data-testid="btn-2d"
                >
                  <Square className="w-4 h-4 mr-2" />
                  2D
                </Button>
                <Button
                  variant={dimension === '3d' ? 'default' : 'outline'}
                  onClick={() => setDimension('3d')}
                  className="font-mono text-xs"
                  disabled={running}
                  data-testid="btn-3d"
                >
                  <Box className="w-4 h-4 mr-2" />
                  3D
                </Button>
              </div>
            </div>
            
            {/* Parameters */}
            <div className="space-y-4">
              <div className="space-y-2">
                <div className="flex justify-between">
                  <label className="text-xs font-mono uppercase text-muted-foreground">Grid Size</label>
                  <span className="text-xs font-mono text-primary">{gridSize}</span>
                </div>
                <Slider
                  value={[gridSize]}
                  onValueChange={([v]) => setGridSize(v)}
                  min={20}
                  max={dimension === '3d' ? 50 : 100}
                  step={10}
                  disabled={running}
                />
              </div>
              
              <div className="space-y-2">
                <div className="flex justify-between">
                  <label className="text-xs font-mono uppercase text-muted-foreground">α (Backreaction)</label>
                  <span className="text-xs font-mono text-primary">{alpha.toFixed(2)}</span>
                </div>
                <Slider
                  value={[alpha * 100]}
                  onValueChange={([v]) => setAlpha(v / 100)}
                  min={10}
                  max={90}
                  step={5}
                  disabled={running}
                />
              </div>
              
              <div className="space-y-2">
                <div className="flex justify-between">
                  <label className="text-xs font-mono uppercase text-muted-foreground">λ (Relaxation)</label>
                  <span className="text-xs font-mono text-primary">{lambdaRelax.toFixed(2)}</span>
                </div>
                <Slider
                  value={[lambdaRelax * 100]}
                  onValueChange={([v]) => setLambdaRelax(v / 100)}
                  min={10}
                  max={100}
                  step={10}
                  disabled={running}
                />
              </div>
              
              <div className="space-y-2">
                <div className="flex justify-between">
                  <label className="text-xs font-mono uppercase text-muted-foreground">γ (Damping)</label>
                  <span className="text-xs font-mono text-primary">{gammaWave.toFixed(3)}</span>
                </div>
                <Slider
                  value={[gammaWave * 1000]}
                  onValueChange={([v]) => setGammaWave(v / 1000)}
                  min={1}
                  max={50}
                  step={1}
                  disabled={running}
                />
              </div>
              
              <div className="space-y-2">
                <div className="flex justify-between">
                  <label className="text-xs font-mono uppercase text-muted-foreground">Steps</label>
                  <span className="text-xs font-mono text-primary">{steps}</span>
                </div>
                <Slider
                  value={[steps]}
                  onValueChange={([v]) => setSteps(v)}
                  min={100}
                  max={1000}
                  step={100}
                  disabled={running}
                />
              </div>
            </div>
            
            {/* Run Button */}
            <Button
              onClick={runSimulation}
              disabled={running}
              className="w-full bg-primary hover:bg-primary/90 font-mono uppercase"
              data-testid="run-simulation-btn"
            >
              {running ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Running {dimension.toUpperCase()}...
                </>
              ) : (
                <>
                  <Zap className="w-4 h-4 mr-2" />
                  Run {dimension.toUpperCase()} Simulation
                </>
              )}
            </Button>
            
            {/* Playback Controls */}
            {result && (
              <div className="space-y-3 pt-3 border-t border-border/50">
                <div className="flex items-center gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={togglePlayback}
                    className="font-mono text-xs"
                    data-testid="playback-toggle"
                  >
                    {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={resetPlayback}
                    className="font-mono text-xs"
                  >
                    <RotateCcw className="w-4 h-4" />
                  </Button>
                  <span className="text-xs font-mono text-muted-foreground ml-auto">
                    t = {currentMeasurement.t?.toFixed(2) || '0.00'}
                  </span>
                </div>
                <Slider
                  value={[playbackIndex]}
                  onValueChange={([v]) => setPlaybackIndex(v)}
                  min={0}
                  max={Math.max((result.measurements?.length || 1) - 1, 0)}
                  step={1}
                />
              </div>
            )}
          </CardContent>
        </Card>
        
        {/* Right Panel: Results */}
        <div className="lg:col-span-3 space-y-6">
          {result ? (
            <Tabs defaultValue="overview" className="w-full">
              <TabsList className="grid w-full grid-cols-4 mb-4">
                <TabsTrigger value="overview" className="font-mono text-xs uppercase">Overview</TabsTrigger>
                <TabsTrigger value="temporal" className="font-mono text-xs uppercase">Temporal</TabsTrigger>
                <TabsTrigger value="spatial" className="font-mono text-xs uppercase">Spatial</TabsTrigger>
                <TabsTrigger value="fields" className="font-mono text-xs uppercase">Fields</TabsTrigger>
              </TabsList>
              
              {/* Overview Tab */}
              <TabsContent value="overview" className="space-y-4">
                {/* Summary Cards */}
                <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
                  <MetricCard 
                    label="Balance" 
                    value={result.balance_achieved ? 'YES' : 'NO'}
                    color={result.balance_achieved ? 'border-green-500/50 bg-green-500' : 'border-red-500/50 bg-red-500'}
                    status={result.balance_achieved}
                  />
                  <MetricCard 
                    label="S (Spatial)" 
                    value={result.spatial_S_mean}
                    color="border-blue-500/50 bg-blue-500"
                  />
                  <MetricCard 
                    label="I_TS (Coupling)" 
                    value={result.coupling_I_TS_mean}
                    color="border-purple-500/50 bg-purple-500"
                  />
                  <MetricCard 
                    label="Isotropic" 
                    value={result.geometry_isotropic ? 'YES' : 'NO'}
                    color={result.geometry_isotropic ? 'border-green-500/50 bg-green-500' : 'border-yellow-500/50 bg-yellow-500'}
                    status={result.geometry_isotropic}
                  />
                  <MetricCard 
                    label="Confined" 
                    value={result.geometry_confined ? 'YES' : 'NO'}
                    color={result.geometry_confined ? 'border-green-500/50 bg-green-500' : 'border-yellow-500/50 bg-yellow-500'}
                    status={result.geometry_confined}
                  />
                </div>
                
                {/* Radar Chart + Correlations */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <Card className="bg-card/50 border-border/50">
                    <CardHeader className="pb-2">
                      <CardTitle className="text-sm font-mono uppercase">Validation Summary</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <ResponsiveContainer width="100%" height={200}>
                        <RadarChart data={radarData}>
                          <PolarGrid stroke="rgba(255,255,255,0.1)" />
                          <PolarAngleAxis dataKey="subject" tick={{ fontSize: 10, fill: '#888' }} />
                          <PolarRadiusAxis tick={{ fontSize: 8 }} domain={[0, 1]} />
                          <Radar name="Score" dataKey="value" stroke="#00d4ff" fill="#00d4ff" fillOpacity={0.3} />
                        </RadarChart>
                      </ResponsiveContainer>
                    </CardContent>
                  </Card>
                  
                  <Card className="bg-card/50 border-border/50">
                    <CardHeader className="pb-2">
                      <CardTitle className="text-sm font-mono uppercase">Cross-Branch Correlations</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-3">
                      <div className="space-y-1">
                        <div className="flex justify-between text-xs font-mono">
                          <span>ρ(R, S)</span>
                          <span>{result.rho_RS?.toFixed(3)}</span>
                        </div>
                        <Progress value={(result.rho_RS + 1) * 50} className="h-2" />
                      </div>
                      <div className="space-y-1">
                        <div className="flex justify-between text-xs font-mono">
                          <span>ρ(P, S)</span>
                          <span>{result.rho_PS?.toFixed(3)}</span>
                        </div>
                        <Progress value={(result.rho_PS + 1) * 50} className="h-2" />
                      </div>
                      <div className="space-y-1">
                        <div className="flex justify-between text-xs font-mono">
                          <span>ρ(O, S)</span>
                          <span>{result.rho_OS?.toFixed(3)}</span>
                        </div>
                        <Progress value={(result.rho_OS + 1) * 50} className="h-2" />
                      </div>
                      <p className="text-xs text-muted-foreground mt-2">
                        Values near -1 indicate anti-correlation (geometry constrains ordering)
                      </p>
                    </CardContent>
                  </Card>
                </div>
                
                {/* Energy Evolution */}
                <Card className="bg-card/50 border-border/50">
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-mono uppercase">Energy Evolution (E_cv = {result.balance_E_cv?.toFixed(4)})</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <ResponsiveContainer width="100%" height={200}>
                      <LineChart data={result.measurements}>
                        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                        <XAxis dataKey="t" stroke="rgba(255,255,255,0.5)" tick={{ fontSize: 10 }} />
                        <YAxis stroke="rgba(255,255,255,0.5)" tick={{ fontSize: 10 }} />
                        <Tooltip content={<CustomTooltip />} />
                        <Legend wrapperStyle={{ fontSize: '10px' }} />
                        <Line type="monotone" dataKey="E_total" name="Total E" stroke="#00d4ff" strokeWidth={2} dot={false} />
                        <Line type="monotone" dataKey="E_kinetic" name="Kinetic" stroke="#ff6b6b" strokeWidth={1} dot={false} />
                        <Line type="monotone" dataKey="E_gradient" name="Gradient" stroke="#4ade80" strokeWidth={1} dot={false} />
                      </LineChart>
                    </ResponsiveContainer>
                  </CardContent>
                </Card>
              </TabsContent>
              
              {/* Temporal Tab */}
              <TabsContent value="temporal" className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <MetricCard label="R (Rate)" value={result.rate_R_mean} color="border-orange-500/50 bg-orange-500" />
                  <MetricCard label="P (Persistence)" value={result.persistence_P_mean} color="border-purple-500/50 bg-purple-500" />
                  <MetricCard label="O (Ordering)" value={result.ordering_O_mean} color="border-blue-500/50 bg-blue-500" />
                </div>
                
                <Card className="bg-card/50 border-border/50">
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-mono uppercase">Temporal Layers Over Time</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <ResponsiveContainer width="100%" height={250}>
                      <LineChart data={result.measurements}>
                        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                        <XAxis dataKey="t" stroke="rgba(255,255,255,0.5)" tick={{ fontSize: 10 }} />
                        <YAxis stroke="rgba(255,255,255,0.5)" tick={{ fontSize: 10 }} />
                        <Tooltip content={<CustomTooltip />} />
                        <Legend wrapperStyle={{ fontSize: '10px' }} />
                        <Line type="monotone" dataKey="R_rate" name="R (Rate)" stroke="#f97316" strokeWidth={2} dot={false} />
                        <Line type="monotone" dataKey="P_persistence" name="P (Persist)" stroke="#a855f7" strokeWidth={2} dot={false} />
                      </LineChart>
                    </ResponsiveContainer>
                  </CardContent>
                </Card>
                
                <Card className="bg-card/50 border-border/50">
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-mono uppercase">Spacetime Coupling I_TS</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <ResponsiveContainer width="100%" height={200}>
                      <AreaChart data={result.measurements}>
                        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                        <XAxis dataKey="t" stroke="rgba(255,255,255,0.5)" tick={{ fontSize: 10 }} />
                        <YAxis stroke="rgba(255,255,255,0.5)" tick={{ fontSize: 10 }} domain={[0, 1]} />
                        <Tooltip content={<CustomTooltip />} />
                        <Area type="monotone" dataKey="I_TS" name="I_TS" stroke="#00d4ff" fill="#00d4ff30" />
                      </AreaChart>
                    </ResponsiveContainer>
                  </CardContent>
                </Card>
              </TabsContent>
              
              {/* Spatial Tab */}
              <TabsContent value="spatial" className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <MetricCard label="S (Spatial)" value={result.spatial_S_mean} color="border-green-500/50 bg-green-500" />
                  <MetricCard label="Isotropy CV" value={currentMeasurement.isotropy_cv || 0} color="border-blue-500/50 bg-blue-500" />
                  <MetricCard label="Confinement" value={`${(currentMeasurement.confinement || 0).toFixed(1)}%`} color="border-purple-500/50 bg-purple-500" />
                </div>
                
                <Card className="bg-card/50 border-border/50">
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-mono uppercase">Spatial Structure S</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <ResponsiveContainer width="100%" height={200}>
                      <LineChart data={result.measurements}>
                        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                        <XAxis dataKey="t" stroke="rgba(255,255,255,0.5)" tick={{ fontSize: 10 }} />
                        <YAxis stroke="rgba(255,255,255,0.5)" tick={{ fontSize: 10 }} />
                        <Tooltip content={<CustomTooltip />} />
                        <Line type="monotone" dataKey="S_total" name="S" stroke="#4ade80" strokeWidth={2} dot={false} />
                      </LineChart>
                    </ResponsiveContainer>
                  </CardContent>
                </Card>
                
                <Card className="bg-card/50 border-border/50">
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-mono uppercase">Causal Geometry</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <ResponsiveContainer width="100%" height={200}>
                      <LineChart data={result.measurements}>
                        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                        <XAxis dataKey="t" stroke="rgba(255,255,255,0.5)" tick={{ fontSize: 10 }} />
                        <YAxis stroke="rgba(255,255,255,0.5)" tick={{ fontSize: 10 }} />
                        <Tooltip content={<CustomTooltip />} />
                        <Legend wrapperStyle={{ fontSize: '10px' }} />
                        <Line type="monotone" dataKey="isotropy_cv" name="Isotropy CV" stroke="#3b82f6" strokeWidth={2} dot={false} />
                        <Line type="monotone" dataKey="confinement" name="Confinement %" stroke="#a855f7" strokeWidth={2} dot={false} />
                      </LineChart>
                    </ResponsiveContainer>
                  </CardContent>
                </Card>
              </TabsContent>
              
              {/* Fields Tab */}
              <TabsContent value="fields" className="space-y-4">
                <Card className="bg-card/50 border-border/50">
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-mono uppercase">
                      Field Visualization (t = {currentMeasurement.t?.toFixed(2) || 0})
                    </CardTitle>
                    <CardDescription className="text-xs">
                      {dimension === '3d' ? 'Central slices of 3D fields' : '2D field distributions'}
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 justify-items-center">
                      {dimension === '2d' ? (
                        <>
                          <FieldHeatmap data={currentSnapshot.rho} title="ρ (Energy)" colorScheme="heat" />
                          <FieldHeatmap data={currentSnapshot.c_eff} title="c_eff (Speed)" colorScheme="blue" />
                          <FieldHeatmap data={currentSnapshot.tau} title="τ (Medium)" colorScheme="gray" />
                        </>
                      ) : (
                        <>
                          <FieldHeatmap data={currentSnapshot.rho_xy} title="ρ (XY slice)" colorScheme="heat" />
                          <FieldHeatmap data={currentSnapshot.rho_xz} title="ρ (XZ slice)" colorScheme="heat" />
                          <FieldHeatmap data={currentSnapshot.rho_yz} title="ρ (YZ slice)" colorScheme="heat" />
                          <FieldHeatmap data={currentSnapshot.c_eff_xy} title="c_eff (XY)" colorScheme="blue" />
                        </>
                      )}
                    </div>
                  </CardContent>
                </Card>
                
                {/* Current values */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  <MetricCard label="E_total" value={currentMeasurement.E_total || 0} color="border-blue-500/50 bg-blue-500" />
                  <MetricCard label="S_total" value={currentMeasurement.S_total || 0} color="border-green-500/50 bg-green-500" />
                  <MetricCard label="O_total" value={currentMeasurement.O_total || 0} color="border-purple-500/50 bg-purple-500" />
                  <MetricCard label="I_TS" value={currentMeasurement.I_TS || 0} color="border-orange-500/50 bg-orange-500" />
                </div>
              </TabsContent>
            </Tabs>
          ) : (
            <Card className="bg-card/50 border-border/50">
              <CardContent className="flex flex-col items-center justify-center py-16">
                <Atom className="w-16 h-16 text-muted-foreground/50 mb-4" />
                <h3 className="text-xl font-semibold mb-2">No Simulation Running</h3>
                <p className="text-sm text-muted-foreground text-center max-w-md">
                  Configure parameters and run a 2D or 3D QMRT simulation to visualize 
                  emergent spacetime physics: energy balance, temporal layers, spatial structure, and spacetime coupling.
                </p>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
      
      {/* Theory Info */}
      <Card className="bg-card/50 border-border/50">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-mono uppercase flex items-center gap-2">
            <Info className="w-4 h-4" />
            QMRT Theory Summary
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4 text-xs">
            <div>
              <p className="font-mono font-bold text-blue-400">S (Spatial)</p>
              <p className="text-muted-foreground">Metric geometry structure from c_eff variation</p>
            </div>
            <div>
              <p className="font-mono font-bold text-green-400">O (Ordering)</p>
              <p className="text-muted-foreground">Causal path diversity, scales as S²</p>
            </div>
            <div>
              <p className="font-mono font-bold text-orange-400">R (Rate)</p>
              <p className="text-muted-foreground">Temporal dynamics, medium change rate</p>
            </div>
            <div>
              <p className="font-mono font-bold text-purple-400">P (Persistence)</p>
              <p className="text-muted-foreground">Configuration stability, 1/(1+R)</p>
            </div>
            <div>
              <p className="font-mono font-bold text-cyan-400">I_TS (Coupling)</p>
              <p className="text-muted-foreground">Cross-branch spacetime coupling integral</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default QMRTSimulationLab;
