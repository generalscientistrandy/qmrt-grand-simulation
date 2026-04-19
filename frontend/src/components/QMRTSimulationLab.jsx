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
  AreaChart, Area, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar,
  ScatterChart, Scatter, ZAxis
} from 'recharts';
import { 
  Play, Pause, RotateCcw, Zap, Activity, Atom, Box, Square,
  Loader2, CheckCircle2, XCircle, Info, TrendingUp, CircleDot, 
  Hexagon, Target, Flame
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

// Enhanced Field visualization with structure overlays
const FieldHeatmapWithOverlays = ({ 
  data, 
  title, 
  colorScheme = 'heat',
  structures = {},
  gridSize,
  showStrainNodes = false,
  showClusters = false,
  showParticleNodes = false,
  showVortices = false,
  onStructureClick = () => {}
}) => {
  const [hoveredStructure, setHoveredStructure] = useState(null);
  
  if (!data || data.length === 0) {
    return (
      <div className="h-32 flex items-center justify-center text-muted-foreground text-xs">
        No data
      </div>
    );
  }

  const displaySize = data.length;
  const maxVal = Math.max(...data.flat());
  const minVal = Math.min(...data.flat());
  const range = maxVal - minVal || 1;
  
  // Scale factor from original grid to display grid
  const scale = gridSize ? displaySize / gridSize : 1;
  const pixelSize = Math.min(displaySize * 6, 200);
  const cellSize = pixelSize / displaySize;

  // Convert grid position to pixel position
  const toPixel = (pos) => {
    if (!pos || pos.length < 2) return { x: 0, y: 0 };
    return {
      x: (pos[0] * scale) * cellSize,
      y: (pos[1] * scale) * cellSize
    };
  };

  return (
    <div className="space-y-1 relative">
      <p className="text-xs font-mono uppercase tracking-widest text-muted-foreground">{title}</p>
      <div 
        className="relative mx-auto border border-border/30 rounded-sm overflow-hidden"
        style={{ width: `${pixelSize}px`, height: `${pixelSize}px` }}
      >
        {/* Base heatmap grid */}
        <div 
          className="grid gap-0 absolute inset-0"
          style={{ gridTemplateColumns: `repeat(${displaySize}, 1fr)` }}
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
        
        {/* SVG Overlay for structures */}
        <svg 
          className="absolute inset-0" 
          width={pixelSize} 
          height={pixelSize}
          style={{ pointerEvents: 'none' }}
        >
          {/* Strain Nodes - Orange diamonds */}
          {showStrainNodes && structures.strain_nodes?.map((node, i) => {
            const { x, y } = toPixel(node.position);
            const size = 4 + node.stability * 4;
            return (
              <g key={`strain-${i}`} style={{ pointerEvents: 'visiblePainted', cursor: 'pointer' }}>
                <polygon
                  points={`${x},${y-size} ${x+size},${y} ${x},${y+size} ${x-size},${y}`}
                  fill="rgba(249, 115, 22, 0.8)"
                  stroke="#fff"
                  strokeWidth="0.5"
                  onMouseEnter={() => setHoveredStructure({ type: 'strain', data: node, x, y })}
                  onMouseLeave={() => setHoveredStructure(null)}
                  onClick={(e) => { e.stopPropagation(); onStructureClick({ type: 'strain', data: node }); }}
                />
              </g>
            );
          })}
          
          {/* Coherence Clusters - Green circles with radius */}
          {showClusters && structures.coherence_clusters?.map((cluster, i) => {
            const { x, y } = toPixel(cluster.center);
            const radius = Math.max(4, cluster.size * scale * cellSize);
            return (
              <g key={`cluster-${i}`} style={{ pointerEvents: 'visiblePainted', cursor: 'pointer' }}>
                <circle
                  cx={x}
                  cy={y}
                  r={radius}
                  fill="rgba(74, 222, 128, 0.2)"
                  stroke="#4ade80"
                  strokeWidth="1.5"
                  strokeDasharray="3,2"
                  onMouseEnter={() => setHoveredStructure({ type: 'cluster', data: cluster, x, y })}
                  onMouseLeave={() => setHoveredStructure(null)}
                  onClick={(e) => { e.stopPropagation(); onStructureClick({ type: 'cluster', data: cluster }); }}
                />
                <circle
                  cx={x}
                  cy={y}
                  r={3}
                  fill="#4ade80"
                  style={{ pointerEvents: 'none' }}
                />
              </g>
            );
          })}
          
          {/* Particle Nodes - Colored by type */}
          {showParticleNodes && structures.particle_nodes?.map((particle, i) => {
            const { x, y } = toPixel(particle.position);
            let fill, stroke;
            switch(particle.structure_type) {
              case 'stable':
                fill = 'rgba(168, 85, 247, 0.9)';
                stroke = '#fff';
                break;
              case 'proto-particle':
                fill = 'rgba(234, 179, 8, 0.9)';
                stroke = '#fff';
                break;
              default: // transient
                fill = 'rgba(156, 163, 175, 0.7)';
                stroke = '#9ca3af';
            }
            return (
              <g key={`particle-${i}`} style={{ pointerEvents: 'visiblePainted', cursor: 'pointer' }}>
                <circle
                  cx={x}
                  cy={y}
                  r={6}
                  fill={fill}
                  stroke={stroke}
                  strokeWidth="1.5"
                  onMouseEnter={() => setHoveredStructure({ type: 'particle', data: particle, x, y })}
                  onMouseLeave={() => setHoveredStructure(null)}
                  onClick={(e) => { e.stopPropagation(); onStructureClick({ type: 'particle', data: particle }); }}
                />
                {/* Inner dot for stable particles */}
                {particle.structure_type === 'stable' && (
                  <circle cx={x} cy={y} r={2} fill="#fff" style={{ pointerEvents: 'none' }} />
                )}
              </g>
            );
          })}
          
          {/* Torsion Vortices - Cyan spirals with chirality indicator */}
          {showVortices && structures.torsion_vortices?.map((vortex, i) => {
            const { x, y } = toPixel(vortex.position);
            const r = Math.max(4, vortex.radius * scale * cellSize);
            const chirality = vortex.chirality > 0 ? 1 : -1;
            return (
              <g key={`vortex-${i}`} style={{ pointerEvents: 'visiblePainted', cursor: 'pointer' }}>
                <circle
                  cx={x}
                  cy={y}
                  r={r}
                  fill="rgba(0, 212, 255, 0.1)"
                  stroke="#00d4ff"
                  strokeWidth="2"
                  onMouseEnter={() => setHoveredStructure({ type: 'vortex', data: vortex, x, y })}
                  onMouseLeave={() => setHoveredStructure(null)}
                  onClick={(e) => { e.stopPropagation(); onStructureClick({ type: 'vortex', data: vortex }); }}
                />
                {/* Chirality arrow */}
                <path
                  d={chirality > 0 
                    ? `M${x-3},${y-1} L${x},${y-4} L${x+3},${y-1}` 
                    : `M${x-3},${y+1} L${x},${y+4} L${x+3},${y+1}`}
                  fill="none"
                  stroke="#00d4ff"
                  strokeWidth="1.5"
                  style={{ pointerEvents: 'none' }}
                />
              </g>
            );
          })}
        </svg>
        
        {/* Hover tooltip */}
        {hoveredStructure && (
          <div 
            className="absolute z-50 bg-card/95 backdrop-blur-md border border-border rounded-sm p-2 shadow-xl pointer-events-none"
            style={{ 
              left: Math.min(hoveredStructure.x + 10, pixelSize - 120),
              top: Math.min(hoveredStructure.y + 10, pixelSize - 80),
              minWidth: '110px'
            }}
          >
            <div className="text-xs font-mono uppercase font-bold mb-1" style={{
              color: hoveredStructure.type === 'strain' ? '#f97316' :
                     hoveredStructure.type === 'cluster' ? '#4ade80' :
                     hoveredStructure.type === 'particle' ? '#a855f7' : '#00d4ff'
            }}>
              {hoveredStructure.type}
            </div>
            {hoveredStructure.type === 'strain' && (
              <>
                <div className="text-xs">E: {hoveredStructure.data.energy_density?.toFixed(3)}</div>
                <div className="text-xs">σ: {(hoveredStructure.data.stability * 100).toFixed(0)}%</div>
              </>
            )}
            {hoveredStructure.type === 'cluster' && (
              <>
                <div className="text-xs">Φ: {hoveredStructure.data.coherence_strength?.toFixed(3)}</div>
                <div className="text-xs">n: {hoveredStructure.data.member_count}</div>
              </>
            )}
            {hoveredStructure.type === 'particle' && (
              <>
                <div className="text-xs">type: {hoveredStructure.data.structure_type}</div>
                <div className="text-xs">m: {hoveredStructure.data.effective_mass?.toFixed(2)}</div>
                <div className="text-xs text-muted-foreground">
                  {hoveredStructure.data.has_vortex && '+vortex '}
                  {hoveredStructure.data.has_cluster && '+cluster'}
                </div>
              </>
            )}
            {hoveredStructure.type === 'vortex' && (
              <>
                <div className="text-xs">ω: {hoveredStructure.data.strength?.toFixed(3)}</div>
                <div className="text-xs">χ: {hoveredStructure.data.chirality > 0 ? '+1' : '-1'}</div>
              </>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

// Simple Field visualization (2D heatmap) - kept for backward compatibility
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

// Structure count card
const StructureCountCard = ({ label, count, icon: Icon, color, description }) => (
  <div className={`p-4 rounded-sm border ${color} bg-opacity-10`}>
    <div className="flex items-center gap-2 mb-2">
      <Icon className="w-5 h-5" style={{ color: color.includes('cyan') ? '#00d4ff' : color.includes('orange') ? '#f97316' : color.includes('green') ? '#4ade80' : '#a855f7' }} />
      <span className="text-sm font-mono uppercase">{label}</span>
    </div>
    <div className="text-3xl font-mono font-bold mb-1">{count}</div>
    <p className="text-xs text-muted-foreground">{description}</p>
  </div>
);

// Structure list item
const StructureItem = ({ type, data, index }) => {
  const getTypeIcon = () => {
    switch(type) {
      case 'vortex': return <Hexagon className="w-4 h-4 text-cyan-400" />;
      case 'strain': return <Flame className="w-4 h-4 text-orange-400" />;
      case 'cluster': return <CircleDot className="w-4 h-4 text-green-400" />;
      case 'particle': return <Target className="w-4 h-4 text-purple-400" />;
      default: return <Atom className="w-4 h-4" />;
    }
  };

  const formatPosition = (pos) => {
    if (!pos) return 'N/A';
    return `(${pos.map(p => typeof p === 'number' ? p.toFixed(1) : p).join(', ')})`;
  };

  return (
    <div className="flex items-center gap-3 p-2 rounded-sm bg-card/30 border border-border/30">
      {getTypeIcon()}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="text-xs font-mono uppercase text-muted-foreground">#{index + 1}</span>
          <span className="text-xs font-mono">{formatPosition(data.position || data.center)}</span>
        </div>
        <div className="flex flex-wrap gap-2 mt-1">
          {type === 'vortex' && (
            <>
              <Badge variant="outline" className="text-xs">ω: {data.strength?.toFixed(3)}</Badge>
              <Badge variant="outline" className="text-xs">r: {data.radius?.toFixed(1)}</Badge>
              <Badge variant={data.chirality > 0 ? "default" : "secondary"} className="text-xs">
                {data.chirality > 0 ? '+' : '-'}χ
              </Badge>
            </>
          )}
          {type === 'strain' && (
            <>
              <Badge variant="outline" className="text-xs">E: {data.energy_density?.toFixed(4)}</Badge>
              <Badge variant="outline" className="text-xs">∇: {data.gradient_magnitude?.toFixed(3)}</Badge>
              <Badge variant="outline" className="text-xs">σ: {(data.stability * 100).toFixed(0)}%</Badge>
            </>
          )}
          {type === 'cluster' && (
            <>
              <Badge variant="outline" className="text-xs">Φ: {data.coherence_strength?.toFixed(3)}</Badge>
              <Badge variant="outline" className="text-xs">n: {data.member_count}</Badge>
              <Badge variant="outline" className="text-xs">r: {data.size?.toFixed(1)}</Badge>
            </>
          )}
          {type === 'particle' && (
            <>
              <Badge 
                variant={data.structure_type === 'stable' ? 'default' : data.structure_type === 'proto-particle' ? 'secondary' : 'outline'}
                className="text-xs"
              >
                {data.structure_type}
              </Badge>
              <Badge variant="outline" className="text-xs">m: {data.effective_mass?.toFixed(3)}</Badge>
              {data.has_vortex && <Badge variant="outline" className="text-xs text-cyan-400">+vortex</Badge>}
              {data.has_cluster && <Badge variant="outline" className="text-xs text-green-400">+cluster</Badge>}
            </>
          )}
        </div>
      </div>
    </div>
  );
};

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
  
  // Overlay toggles
  const [showStrainNodes, setShowStrainNodes] = useState(true);
  const [showClusters, setShowClusters] = useState(true);
  const [showParticleNodes, setShowParticleNodes] = useState(true);
  const [showVortices, setShowVortices] = useState(true);
  
  // Selected structure for inspector
  const [selectedStructure, setSelectedStructure] = useState(null);
  
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
              <TabsList className="grid w-full grid-cols-5 mb-4">
                <TabsTrigger value="overview" className="font-mono text-xs uppercase">Overview</TabsTrigger>
                <TabsTrigger value="temporal" className="font-mono text-xs uppercase">Temporal</TabsTrigger>
                <TabsTrigger value="spatial" className="font-mono text-xs uppercase">Spatial</TabsTrigger>
                <TabsTrigger value="structures" className="font-mono text-xs uppercase" data-testid="tab-structures">Structures</TabsTrigger>
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
                
                {/* Structure Summary Row */}
                <div className="grid grid-cols-4 gap-3">
                  <div className="p-2 rounded-sm border border-cyan-500/30 bg-cyan-500/5 text-center">
                    <div className="text-lg font-mono font-bold text-cyan-400">{result.total_vortices || 0}</div>
                    <div className="text-xs text-muted-foreground">Vortices</div>
                  </div>
                  <div className="p-2 rounded-sm border border-orange-500/30 bg-orange-500/5 text-center">
                    <div className="text-lg font-mono font-bold text-orange-400">{result.total_strain_nodes || 0}</div>
                    <div className="text-xs text-muted-foreground">Strain Nodes</div>
                  </div>
                  <div className="p-2 rounded-sm border border-green-500/30 bg-green-500/5 text-center">
                    <div className="text-lg font-mono font-bold text-green-400">{result.total_clusters || 0}</div>
                    <div className="text-xs text-muted-foreground">Clusters</div>
                  </div>
                  <div className="p-2 rounded-sm border border-purple-500/30 bg-purple-500/5 text-center">
                    <div className="text-lg font-mono font-bold text-purple-400">{result.total_particle_nodes || 0}</div>
                    <div className="text-xs text-muted-foreground">Particles</div>
                  </div>
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
              
              {/* Structures Tab (Mesoscopic Legacy Data) */}
              <TabsContent value="structures" className="space-y-4" data-testid="structures-tab-content">
                {/* Structure Summary Cards */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <StructureCountCard 
                    label="Torsion Vortices" 
                    count={result.total_vortices || 0}
                    icon={Hexagon}
                    color="border-cyan-500/50 bg-cyan-500"
                    description="Rotational flow structures in the medium"
                  />
                  <StructureCountCard 
                    label="Strain Nodes" 
                    count={result.total_strain_nodes || 0}
                    icon={Flame}
                    color="border-orange-500/50 bg-orange-500"
                    description="Localized energy concentrations"
                  />
                  <StructureCountCard 
                    label="Coherence Clusters" 
                    count={result.total_clusters || 0}
                    icon={CircleDot}
                    color="border-green-500/50 bg-green-500"
                    description="Phase-correlated regions"
                  />
                  <StructureCountCard 
                    label="Particle Nodes" 
                    count={result.total_particle_nodes || 0}
                    icon={Target}
                    color="border-purple-500/50 bg-purple-500"
                    description="Emergent particle-like structures"
                  />
                </div>
                
                {/* Particle Node Type Breakdown */}
                {result.total_particle_nodes > 0 && (
                  <Card className="bg-card/50 border-border/50">
                    <CardHeader className="pb-2">
                      <CardTitle className="text-sm font-mono uppercase">Particle Node Classification</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="grid grid-cols-3 gap-4">
                        <div className="text-center p-3 rounded-sm bg-green-500/10 border border-green-500/30">
                          <div className="text-2xl font-mono font-bold text-green-400">{result.stable_nodes || 0}</div>
                          <div className="text-xs text-muted-foreground">Stable</div>
                        </div>
                        <div className="text-center p-3 rounded-sm bg-yellow-500/10 border border-yellow-500/30">
                          <div className="text-2xl font-mono font-bold text-yellow-400">{result.proto_nodes || 0}</div>
                          <div className="text-xs text-muted-foreground">Proto-particle</div>
                        </div>
                        <div className="text-center p-3 rounded-sm bg-gray-500/10 border border-gray-500/30">
                          <div className="text-2xl font-mono font-bold text-gray-400">{result.transient_nodes || 0}</div>
                          <div className="text-xs text-muted-foreground">Transient</div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                )}
                
                {/* Structure Evolution Chart */}
                <Card className="bg-card/50 border-border/50">
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-mono uppercase">Structure Count Evolution</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <ResponsiveContainer width="100%" height={200}>
                      <LineChart data={result.measurements}>
                        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                        <XAxis dataKey="t" stroke="rgba(255,255,255,0.5)" tick={{ fontSize: 10 }} />
                        <YAxis stroke="rgba(255,255,255,0.5)" tick={{ fontSize: 10 }} />
                        <Tooltip content={<CustomTooltip />} />
                        <Legend wrapperStyle={{ fontSize: '10px' }} />
                        <Line type="monotone" dataKey="vortex_count" name="Vortices" stroke="#00d4ff" strokeWidth={2} dot={false} />
                        <Line type="monotone" dataKey="cluster_count" name="Clusters" stroke="#4ade80" strokeWidth={2} dot={false} />
                        <Line type="monotone" dataKey="strain_node_count" name="Strain" stroke="#f97316" strokeWidth={2} dot={false} />
                        <Line type="monotone" dataKey="particle_node_count" name="Particles" stroke="#a855f7" strokeWidth={2} dot={false} />
                      </LineChart>
                    </ResponsiveContainer>
                  </CardContent>
                </Card>
                
                {/* Detailed Structure Lists */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {/* Torsion Vortices */}
                  <Card className="bg-card/50 border-border/50">
                    <CardHeader className="pb-2">
                      <CardTitle className="text-sm font-mono uppercase flex items-center gap-2">
                        <Hexagon className="w-4 h-4 text-cyan-400" />
                        Torsion Vortices ({result.structures?.torsion_vortices?.length || 0})
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-2 max-h-48 overflow-y-auto">
                        {result.structures?.torsion_vortices?.length > 0 ? (
                          result.structures.torsion_vortices.slice(0, 10).map((v, i) => (
                            <StructureItem key={i} type="vortex" data={v} index={i} />
                          ))
                        ) : (
                          <p className="text-xs text-muted-foreground text-center py-4">No vortices detected</p>
                        )}
                        {(result.structures?.torsion_vortices?.length || 0) > 10 && (
                          <p className="text-xs text-muted-foreground text-center">
                            +{result.structures.torsion_vortices.length - 10} more
                          </p>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                  
                  {/* Coherence Clusters */}
                  <Card className="bg-card/50 border-border/50">
                    <CardHeader className="pb-2">
                      <CardTitle className="text-sm font-mono uppercase flex items-center gap-2">
                        <CircleDot className="w-4 h-4 text-green-400" />
                        Coherence Clusters ({result.structures?.coherence_clusters?.length || 0})
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-2 max-h-48 overflow-y-auto">
                        {result.structures?.coherence_clusters?.length > 0 ? (
                          result.structures.coherence_clusters.slice(0, 10).map((c, i) => (
                            <StructureItem key={i} type="cluster" data={c} index={i} />
                          ))
                        ) : (
                          <p className="text-xs text-muted-foreground text-center py-4">No clusters detected</p>
                        )}
                        {(result.structures?.coherence_clusters?.length || 0) > 10 && (
                          <p className="text-xs text-muted-foreground text-center">
                            +{result.structures.coherence_clusters.length - 10} more
                          </p>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                  
                  {/* Strain Nodes */}
                  <Card className="bg-card/50 border-border/50">
                    <CardHeader className="pb-2">
                      <CardTitle className="text-sm font-mono uppercase flex items-center gap-2">
                        <Flame className="w-4 h-4 text-orange-400" />
                        Strain Energy Nodes ({result.structures?.strain_nodes?.length || 0})
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-2 max-h-48 overflow-y-auto">
                        {result.structures?.strain_nodes?.length > 0 ? (
                          result.structures.strain_nodes.slice(0, 10).map((s, i) => (
                            <StructureItem key={i} type="strain" data={s} index={i} />
                          ))
                        ) : (
                          <p className="text-xs text-muted-foreground text-center py-4">No strain nodes detected</p>
                        )}
                        {(result.structures?.strain_nodes?.length || 0) > 10 && (
                          <p className="text-xs text-muted-foreground text-center">
                            +{result.structures.strain_nodes.length - 10} more
                          </p>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                  
                  {/* Particle Nodes */}
                  <Card className="bg-card/50 border-border/50">
                    <CardHeader className="pb-2">
                      <CardTitle className="text-sm font-mono uppercase flex items-center gap-2">
                        <Target className="w-4 h-4 text-purple-400" />
                        Particle-Like Nodes ({result.structures?.particle_nodes?.length || 0})
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-2 max-h-48 overflow-y-auto">
                        {result.structures?.particle_nodes?.length > 0 ? (
                          result.structures.particle_nodes.slice(0, 10).map((p, i) => (
                            <StructureItem key={i} type="particle" data={p} index={i} />
                          ))
                        ) : (
                          <p className="text-xs text-muted-foreground text-center py-4">No particle nodes detected</p>
                        )}
                        {(result.structures?.particle_nodes?.length || 0) > 10 && (
                          <p className="text-xs text-muted-foreground text-center">
                            +{result.structures.particle_nodes.length - 10} more
                          </p>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                </div>
              </TabsContent>
              
              {/* Fields Tab */}
              <TabsContent value="fields" className="space-y-4" data-testid="fields-tab-content">
                {/* Overlay Toggles */}
                <Card className="bg-card/50 border-border/50">
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-mono uppercase">Structure Overlays</CardTitle>
                    <CardDescription className="text-xs">Toggle structure markers on field heatmaps</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="flex flex-wrap gap-4">
                      <label className="flex items-center gap-2 cursor-pointer">
                        <input 
                          type="checkbox" 
                          checked={showStrainNodes} 
                          onChange={(e) => setShowStrainNodes(e.target.checked)}
                          className="w-4 h-4 accent-orange-500"
                          data-testid="toggle-strain"
                        />
                        <Flame className="w-4 h-4 text-orange-400" />
                        <span className="text-xs font-mono">Strain Nodes</span>
                      </label>
                      <label className="flex items-center gap-2 cursor-pointer">
                        <input 
                          type="checkbox" 
                          checked={showClusters} 
                          onChange={(e) => setShowClusters(e.target.checked)}
                          className="w-4 h-4 accent-green-500"
                          data-testid="toggle-clusters"
                        />
                        <CircleDot className="w-4 h-4 text-green-400" />
                        <span className="text-xs font-mono">Clusters</span>
                      </label>
                      <label className="flex items-center gap-2 cursor-pointer">
                        <input 
                          type="checkbox" 
                          checked={showParticleNodes} 
                          onChange={(e) => setShowParticleNodes(e.target.checked)}
                          className="w-4 h-4 accent-purple-500"
                          data-testid="toggle-particles"
                        />
                        <Target className="w-4 h-4 text-purple-400" />
                        <span className="text-xs font-mono">Particle Nodes</span>
                      </label>
                      <label className="flex items-center gap-2 cursor-pointer">
                        <input 
                          type="checkbox" 
                          checked={showVortices} 
                          onChange={(e) => setShowVortices(e.target.checked)}
                          className="w-4 h-4 accent-cyan-500"
                          data-testid="toggle-vortices"
                        />
                        <Hexagon className="w-4 h-4 text-cyan-400" />
                        <span className="text-xs font-mono">Vortices</span>
                      </label>
                    </div>
                  </CardContent>
                </Card>
                
                {/* Field Visualization with Overlays */}
                <Card className="bg-card/50 border-border/50">
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-mono uppercase">
                      Field Visualization (t = {currentMeasurement.t?.toFixed(2) || 0})
                    </CardTitle>
                    <CardDescription className="text-xs">
                      {dimension === '3d' ? 'Central slices of 3D fields (hover structures for details)' : '2D field distributions (hover structures for details)'}
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-6 justify-items-center">
                      {dimension === '2d' ? (
                        <>
                          <FieldHeatmapWithOverlays 
                            data={currentSnapshot.rho} 
                            title="ρ (Energy)" 
                            colorScheme="heat"
                            structures={result?.structures}
                            gridSize={gridSize}
                            showStrainNodes={showStrainNodes}
                            showClusters={showClusters}
                            showParticleNodes={showParticleNodes}
                            showVortices={showVortices}
                            onStructureClick={setSelectedStructure}
                          />
                          <FieldHeatmapWithOverlays 
                            data={currentSnapshot.c_eff} 
                            title="c_eff (Speed)" 
                            colorScheme="blue"
                            structures={result?.structures}
                            gridSize={gridSize}
                            showStrainNodes={showStrainNodes}
                            showClusters={showClusters}
                            showParticleNodes={showParticleNodes}
                            showVortices={showVortices}
                            onStructureClick={setSelectedStructure}
                          />
                          <FieldHeatmapWithOverlays 
                            data={currentSnapshot.tau} 
                            title="τ (Medium)" 
                            colorScheme="gray"
                            structures={result?.structures}
                            gridSize={gridSize}
                            showStrainNodes={showStrainNodes}
                            showClusters={showClusters}
                            showParticleNodes={showParticleNodes}
                            showVortices={showVortices}
                            onStructureClick={setSelectedStructure}
                          />
                        </>
                      ) : (
                        <>
                          <FieldHeatmapWithOverlays 
                            data={currentSnapshot.rho_xy} 
                            title="ρ (XY slice)" 
                            colorScheme="heat"
                            structures={result?.structures}
                            gridSize={Math.min(gridSize, 50)}
                            showStrainNodes={showStrainNodes}
                            showClusters={showClusters}
                            showParticleNodes={showParticleNodes}
                            showVortices={showVortices}
                            onStructureClick={setSelectedStructure}
                          />
                          <FieldHeatmapWithOverlays 
                            data={currentSnapshot.rho_xz} 
                            title="ρ (XZ slice)" 
                            colorScheme="heat"
                            structures={result?.structures}
                            gridSize={Math.min(gridSize, 50)}
                            showStrainNodes={showStrainNodes}
                            showClusters={showClusters}
                            showParticleNodes={showParticleNodes}
                            showVortices={showVortices}
                            onStructureClick={setSelectedStructure}
                          />
                          <FieldHeatmapWithOverlays 
                            data={currentSnapshot.rho_yz} 
                            title="ρ (YZ slice)" 
                            colorScheme="heat"
                            structures={result?.structures}
                            gridSize={Math.min(gridSize, 50)}
                            showStrainNodes={showStrainNodes}
                            showClusters={showClusters}
                            showParticleNodes={showParticleNodes}
                            showVortices={showVortices}
                            onStructureClick={setSelectedStructure}
                          />
                          <FieldHeatmapWithOverlays 
                            data={currentSnapshot.c_eff_xy} 
                            title="c_eff (XY)" 
                            colorScheme="blue"
                            structures={result?.structures}
                            gridSize={Math.min(gridSize, 50)}
                            showStrainNodes={showStrainNodes}
                            showClusters={showClusters}
                            showParticleNodes={showParticleNodes}
                            showVortices={showVortices}
                            onStructureClick={setSelectedStructure}
                          />
                        </>
                      )}
                    </div>
                  </CardContent>
                </Card>
                
                {/* Structure Inspector Panel */}
                {selectedStructure && (
                  <Card className="bg-card/50 border-border/50 border-l-4" style={{
                    borderLeftColor: selectedStructure.type === 'strain' ? '#f97316' :
                                     selectedStructure.type === 'cluster' ? '#4ade80' :
                                     selectedStructure.type === 'particle' ? '#a855f7' : '#00d4ff'
                  }}>
                    <CardHeader className="pb-2">
                      <div className="flex items-center justify-between">
                        <CardTitle className="text-sm font-mono uppercase flex items-center gap-2">
                          {selectedStructure.type === 'strain' && <Flame className="w-4 h-4 text-orange-400" />}
                          {selectedStructure.type === 'cluster' && <CircleDot className="w-4 h-4 text-green-400" />}
                          {selectedStructure.type === 'particle' && <Target className="w-4 h-4 text-purple-400" />}
                          {selectedStructure.type === 'vortex' && <Hexagon className="w-4 h-4 text-cyan-400" />}
                          {selectedStructure.type} Inspector
                        </CardTitle>
                        <Button 
                          variant="ghost" 
                          size="sm" 
                          onClick={() => setSelectedStructure(null)}
                          className="h-6 w-6 p-0"
                          data-testid="inspector-close-btn"
                        >
                          <XCircle className="w-4 h-4" />
                        </Button>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs font-mono">
                        <div>
                          <span className="text-muted-foreground">Position:</span>
                          <div className="font-bold">
                            ({(selectedStructure.data.position || selectedStructure.data.center)?.map(p => 
                              typeof p === 'number' ? p.toFixed(1) : p
                            ).join(', ')})
                          </div>
                        </div>
                        
                        {selectedStructure.type === 'strain' && (
                          <>
                            <div>
                              <span className="text-muted-foreground">Energy Density:</span>
                              <div className="font-bold">{selectedStructure.data.energy_density?.toFixed(4)}</div>
                            </div>
                            <div>
                              <span className="text-muted-foreground">Gradient:</span>
                              <div className="font-bold">{selectedStructure.data.gradient_magnitude?.toFixed(4)}</div>
                            </div>
                            <div>
                              <span className="text-muted-foreground">Stability:</span>
                              <div className="font-bold">{(selectedStructure.data.stability * 100).toFixed(1)}%</div>
                            </div>
                          </>
                        )}
                        
                        {selectedStructure.type === 'cluster' && (
                          <>
                            <div>
                              <span className="text-muted-foreground">Coherence:</span>
                              <div className="font-bold">{selectedStructure.data.coherence_strength?.toFixed(4)}</div>
                            </div>
                            <div>
                              <span className="text-muted-foreground">Members:</span>
                              <div className="font-bold">{selectedStructure.data.member_count}</div>
                            </div>
                            <div>
                              <span className="text-muted-foreground">Size:</span>
                              <div className="font-bold">{selectedStructure.data.size?.toFixed(2)}</div>
                            </div>
                          </>
                        )}
                        
                        {selectedStructure.type === 'particle' && (
                          <>
                            <div>
                              <span className="text-muted-foreground">Type:</span>
                              <div className="font-bold">{selectedStructure.data.structure_type}</div>
                            </div>
                            <div>
                              <span className="text-muted-foreground">Effective Mass:</span>
                              <div className="font-bold">{selectedStructure.data.effective_mass?.toFixed(3)}</div>
                            </div>
                            <div>
                              <span className="text-muted-foreground">Stability:</span>
                              <div className="font-bold">{(selectedStructure.data.stability_score * 100).toFixed(1)}%</div>
                            </div>
                            <div>
                              <span className="text-muted-foreground">Linked:</span>
                              <div className="font-bold">
                                {selectedStructure.data.has_vortex && <Badge variant="outline" className="mr-1 text-cyan-400">+vortex</Badge>}
                                {selectedStructure.data.has_cluster && <Badge variant="outline" className="text-green-400">+cluster</Badge>}
                                {!selectedStructure.data.has_vortex && !selectedStructure.data.has_cluster && 'None'}
                              </div>
                            </div>
                          </>
                        )}
                        
                        {selectedStructure.type === 'vortex' && (
                          <>
                            <div>
                              <span className="text-muted-foreground">Strength:</span>
                              <div className="font-bold">{selectedStructure.data.strength?.toFixed(4)}</div>
                            </div>
                            <div>
                              <span className="text-muted-foreground">Radius:</span>
                              <div className="font-bold">{selectedStructure.data.radius?.toFixed(2)}</div>
                            </div>
                            <div>
                              <span className="text-muted-foreground">Chirality:</span>
                              <div className="font-bold">{selectedStructure.data.chirality > 0 ? '+1 (CW)' : '-1 (CCW)'}</div>
                            </div>
                          </>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                )}
                
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
