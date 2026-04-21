import React, { useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Button } from '@/components/ui/button';
import { Slider } from '@/components/ui/slider';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { 
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  AreaChart, Area, BarChart, Bar, ComposedChart, ScatterChart, Scatter
} from 'recharts';
import { 
  Play, Loader2, CheckCircle2, TrendingUp, TrendingDown, Activity, 
  BarChart3, GitBranch, Repeat, Clock, Zap, Target, Info
} from 'lucide-react';
import axios from 'axios';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Custom tooltip component
const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-card/95 backdrop-blur-md border border-border/50 rounded-sm p-3 shadow-xl">
        <p className="text-xs font-mono text-muted-foreground mb-1">t = {label?.toFixed(2)}</p>
        {payload.map((entry, index) => (
          <p key={index} className="text-xs font-mono" style={{ color: entry.color }}>
            {entry.name}: {typeof entry.value === 'number' ? entry.value.toFixed(3) : entry.value}
          </p>
        ))}
      </div>
    );
  }
  return null;
};

// Regime badge color mapping
const getRegimeBadgeColor = (regime) => {
  switch (regime) {
    case 'convergent': return 'bg-green-500/20 text-green-400 border-green-500/30';
    case 'oscillatory': return 'bg-blue-500/20 text-blue-400 border-blue-500/30';
    case 'steady_churn': return 'bg-orange-500/20 text-orange-400 border-orange-500/30';
    case 'transient': return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30';
    default: return 'bg-gray-500/20 text-gray-400 border-gray-500/30';
  }
};

// Trend icon component
const TrendIcon = ({ trend }) => {
  if (trend === 'increasing') return <TrendingUp className="w-3 h-3 text-green-400" />;
  if (trend === 'decreasing') return <TrendingDown className="w-3 h-3 text-red-400" />;
  if (trend === 'stable') return <Target className="w-3 h-3 text-blue-400" />;
  if (trend === 'oscillating') return <Repeat className="w-3 h-3 text-purple-400" />;
  return null;
};

const LongPathDynamics = () => {
  // Configuration state
  const [config, setConfig] = useState({
    dimension: '2d',
    size: 50,
    alpha: 0.5,
    lambda_relax: 0.5,
    gamma_wave: 0.01,
    steps: 3000,
    sample_interval: 10,
    seed: null
  });
  
  // Multi-seed config
  const [multiSeedConfig, setMultiSeedConfig] = useState({
    n_seeds: 5
  });
  
  // State
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState(null);
  const [multiResult, setMultiResult] = useState(null);
  const [mode, setMode] = useState('single'); // 'single' or 'multi'
  
  // Run single long-path simulation
  const runSingleSimulation = useCallback(async () => {
    setRunning(true);
    setResult(null);
    
    try {
      const response = await axios.post(`${API}/qmrt-sim/longpath/run`, {
        ...config,
        seed: config.seed || Math.floor(Math.random() * 100000)
      });
      
      setResult(response.data);
      toast.success(`Long-path simulation complete: ${response.data.analysis.regime} regime`);
    } catch (error) {
      console.error('Simulation error:', error);
      toast.error('Simulation failed: ' + (error.response?.data?.detail || error.message));
    } finally {
      setRunning(false);
    }
  }, [config]);
  
  // Run multi-seed simulations
  const runMultiSeedSimulation = useCallback(async () => {
    setRunning(true);
    setMultiResult(null);
    
    try {
      const response = await axios.post(`${API}/qmrt-sim/longpath/multi-seed`, {
        ...config,
        n_seeds: multiSeedConfig.n_seeds
      });
      
      setMultiResult(response.data);
      toast.success(`Multi-seed complete: ${response.data.dominant_regime} (${(response.data.regime_agreement * 100).toFixed(0)}% agreement)`);
    } catch (error) {
      console.error('Multi-seed error:', error);
      toast.error('Multi-seed simulation failed: ' + (error.response?.data?.detail || error.message));
    } finally {
      setRunning(false);
    }
  }, [config, multiSeedConfig]);
  
  // Prepare chart data
  const structureCountData = result?.time_series?.map(p => ({
    t: p.t,
    total: p.total_structures,
    strain: p.strain_node_count,
    cluster: p.cluster_count,
    vortex: p.vortex_count,
    particle: p.particle_node_count
  })) || [];
  
  const eventRateData = result?.time_series?.map(p => ({
    t: p.t,
    births: p.births,
    deaths: p.deaths,
    merges: p.merges,
    splits: p.splits,
    total: p.births + p.deaths + p.merges + p.splits
  })) || [];
  
  const metricsData = result?.time_series?.map(p => ({
    t: p.t,
    S: p.S_mean,
    I_TS: p.I_TS,
    rho_mean: p.rho_mean / (Math.max(...result.time_series.map(x => x.rho_mean)) || 1), // Normalize
    E_total: p.E_total / (Math.max(...result.time_series.map(x => x.E_total)) || 1)
  })) || [];
  
  const lifetimeData = result?.time_series?.map(p => ({
    t: p.t,
    mean: p.mean_lifetime,
    max: p.max_lifetime,
    median: p.median_lifetime
  })) || [];
  
  // Lifetime histogram data
  const lifetimeHistogram = React.useMemo(() => {
    if (!result?.all_lifetimes?.length) return [];
    
    const lifetimes = result.all_lifetimes;
    const maxLt = Math.max(...lifetimes);
    const bins = 20;
    const binWidth = maxLt / bins;
    
    const counts = new Array(bins).fill(0);
    lifetimes.forEach(lt => {
      const bin = Math.min(Math.floor(lt / binWidth), bins - 1);
      counts[bin]++;
    });
    
    return counts.map((count, i) => ({
      range: `${(i * binWidth).toFixed(1)}-${((i + 1) * binWidth).toFixed(1)}`,
      count,
      midpoint: (i + 0.5) * binWidth
    }));
  }, [result]);
  
  return (
    <div className="min-h-screen bg-background text-foreground p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold tracking-tight">
              <span className="text-cyan-400">PAPER 2:</span> Long-Path Dynamics
            </h1>
            <p className="text-sm text-muted-foreground mt-1">
              Extended time simulations to analyze steady state, oscillation, and structure lifecycle behavior
            </p>
          </div>
          <Badge variant="outline" className="font-mono text-xs">
            Phase 1 / 3
          </Badge>
        </div>
        
        {/* Configuration Panel */}
        <Card className="bg-card/50 border-border/50">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-mono uppercase flex items-center gap-2">
              <Activity className="w-4 h-4 text-cyan-400" />
              Simulation Configuration
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Mode Toggle */}
            <div className="flex gap-2 mb-4">
              <Button
                variant={mode === 'single' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setMode('single')}
                className="font-mono text-xs"
              >
                Single Run
              </Button>
              <Button
                variant={mode === 'multi' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setMode('multi')}
                className="font-mono text-xs"
              >
                Multi-Seed
              </Button>
            </div>
            
            <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
              {/* Dimension */}
              <div className="space-y-1">
                <label className="text-xs font-mono text-muted-foreground">Dimension</label>
                <div className="flex gap-1">
                  <Button
                    variant={config.dimension === '2d' ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setConfig(c => ({ ...c, dimension: '2d' }))}
                    className="flex-1 font-mono text-xs"
                  >
                    2D
                  </Button>
                  <Button
                    variant={config.dimension === '3d' ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setConfig(c => ({ ...c, dimension: '3d' }))}
                    className="flex-1 font-mono text-xs"
                  >
                    3D
                  </Button>
                </div>
              </div>
              
              {/* Grid Size */}
              <div className="space-y-1">
                <label className="text-xs font-mono text-muted-foreground">Grid Size: {config.size}</label>
                <Slider
                  value={[config.size]}
                  onValueChange={([v]) => setConfig(c => ({ ...c, size: v }))}
                  min={30}
                  max={80}
                  step={5}
                  className="py-2"
                />
              </div>
              
              {/* Alpha */}
              <div className="space-y-1">
                <label className="text-xs font-mono text-muted-foreground">Alpha (α): {config.alpha.toFixed(2)}</label>
                <Slider
                  value={[config.alpha]}
                  onValueChange={([v]) => setConfig(c => ({ ...c, alpha: v }))}
                  min={0.1}
                  max={0.9}
                  step={0.05}
                  className="py-2"
                />
              </div>
              
              {/* Steps */}
              <div className="space-y-1">
                <label className="text-xs font-mono text-muted-foreground">Steps: {config.steps}</label>
                <Slider
                  value={[config.steps]}
                  onValueChange={([v]) => setConfig(c => ({ ...c, steps: v }))}
                  min={500}
                  max={6000}
                  step={500}
                  className="py-2"
                />
              </div>
              
              {/* Sample Interval */}
              <div className="space-y-1">
                <label className="text-xs font-mono text-muted-foreground">Sample: {config.sample_interval}</label>
                <Slider
                  value={[config.sample_interval]}
                  onValueChange={([v]) => setConfig(c => ({ ...c, sample_interval: v }))}
                  min={5}
                  max={50}
                  step={5}
                  className="py-2"
                />
              </div>
              
              {/* Multi-seed: N Seeds */}
              {mode === 'multi' && (
                <div className="space-y-1">
                  <label className="text-xs font-mono text-muted-foreground">Seeds: {multiSeedConfig.n_seeds}</label>
                  <Slider
                    value={[multiSeedConfig.n_seeds]}
                    onValueChange={([v]) => setMultiSeedConfig(c => ({ ...c, n_seeds: v }))}
                    min={2}
                    max={10}
                    step={1}
                    className="py-2"
                  />
                </div>
              )}
            </div>
            
            {/* Run Button */}
            <div className="flex gap-2 pt-2">
              <Button
                onClick={mode === 'single' ? runSingleSimulation : runMultiSeedSimulation}
                disabled={running}
                className="font-mono"
                data-testid="run-longpath-btn"
              >
                {running ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Running...
                  </>
                ) : (
                  <>
                    <Play className="w-4 h-4 mr-2" />
                    {mode === 'single' ? 'Run Long-Path' : `Run ${multiSeedConfig.n_seeds} Seeds`}
                  </>
                )}
              </Button>
              
              <div className="flex items-center gap-2 text-xs text-muted-foreground">
                <Clock className="w-3 h-3" />
                Est: {mode === 'single' 
                  ? `${(config.steps / 1000 * 1.5).toFixed(0)}s`
                  : `${(config.steps / 1000 * 1.5 * multiSeedConfig.n_seeds).toFixed(0)}s`
                }
              </div>
            </div>
          </CardContent>
        </Card>
        
        {/* Results Section */}
        {(result || multiResult) && (
          <div className="space-y-6">
            {/* Analysis Summary */}
            {result?.analysis && mode === 'single' && (
              <Card className="bg-card/50 border-border/50">
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm font-mono uppercase flex items-center gap-2">
                    <BarChart3 className="w-4 h-4 text-purple-400" />
                    Analysis Summary
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
                    {/* Regime */}
                    <div className="p-3 rounded-sm border border-border/50 bg-background/50">
                      <div className="text-xs text-muted-foreground mb-1">Regime</div>
                      <Badge className={`font-mono text-xs ${getRegimeBadgeColor(result.analysis.regime)}`}>
                        {result.analysis.regime.toUpperCase()}
                      </Badge>
                      <div className="text-xs text-muted-foreground mt-1">
                        {(result.analysis.regime_confidence * 100).toFixed(0)}% conf
                      </div>
                    </div>
                    
                    {/* Stabilized */}
                    <div className="p-3 rounded-sm border border-border/50 bg-background/50">
                      <div className="text-xs text-muted-foreground mb-1">Stabilized</div>
                      <div className={`text-lg font-mono font-bold ${result.analysis.structure_count_stabilized ? 'text-green-400' : 'text-yellow-400'}`}>
                        {result.analysis.structure_count_stabilized ? 'YES' : 'NO'}
                      </div>
                      {result.analysis.stabilization_time && (
                        <div className="text-xs text-muted-foreground">@ t={result.analysis.stabilization_time.toFixed(1)}</div>
                      )}
                    </div>
                    
                    {/* Structure Count */}
                    <div className="p-3 rounded-sm border border-border/50 bg-background/50">
                      <div className="text-xs text-muted-foreground mb-1">Structures (late)</div>
                      <div className="text-lg font-mono font-bold text-cyan-400">
                        {result.analysis.structure_count_mean.toFixed(1)}
                      </div>
                      <div className="text-xs text-muted-foreground">
                        CV={result.analysis.structure_count_cv.toFixed(3)}
                      </div>
                    </div>
                    
                    {/* Lifetime */}
                    <div className="p-3 rounded-sm border border-border/50 bg-background/50">
                      <div className="text-xs text-muted-foreground mb-1">Lifetime Type</div>
                      <div className="text-lg font-mono font-bold text-orange-400">
                        {result.analysis.lifetime_distribution_type}
                      </div>
                      <div className="text-xs text-muted-foreground">
                        mean={result.analysis.lifetime_mean.toFixed(2)}
                      </div>
                    </div>
                    
                    {/* S Trend */}
                    <div className="p-3 rounded-sm border border-border/50 bg-background/50">
                      <div className="text-xs text-muted-foreground mb-1 flex items-center gap-1">
                        S Trend <TrendIcon trend={result.analysis.S_trend} />
                      </div>
                      <div className="text-sm font-mono">
                        {result.analysis.S_early_mean.toFixed(4)} → {result.analysis.S_late_mean.toFixed(4)}
                      </div>
                      <div className="text-xs text-muted-foreground">{result.analysis.S_trend}</div>
                    </div>
                    
                    {/* I_TS Trend */}
                    <div className="p-3 rounded-sm border border-border/50 bg-background/50">
                      <div className="text-xs text-muted-foreground mb-1 flex items-center gap-1">
                        I_TS Trend <TrendIcon trend={result.analysis.I_TS_trend} />
                      </div>
                      <div className="text-sm font-mono">
                        {result.analysis.I_TS_early_mean.toFixed(4)} → {result.analysis.I_TS_late_mean.toFixed(4)}
                      </div>
                      <div className="text-xs text-muted-foreground">{result.analysis.I_TS_trend}</div>
                    </div>
                  </div>
                  
                  {/* Autocorrelation */}
                  <div className="mt-4 p-3 rounded-sm border border-border/50 bg-background/50">
                    <div className="text-xs text-muted-foreground mb-2">Autocorrelation (structure count)</div>
                    <div className="flex gap-4 text-xs font-mono">
                      <span>lag1: <span className="text-cyan-400">{result.analysis.structure_count_autocorr_lag1.toFixed(3)}</span></span>
                      <span>lag5: <span className="text-cyan-400">{result.analysis.structure_count_autocorr_lag5.toFixed(3)}</span></span>
                      <span>lag10: <span className="text-cyan-400">{result.analysis.structure_count_autocorr_lag10.toFixed(3)}</span></span>
                      <span className="text-muted-foreground">|</span>
                      <span>event lag1: <span className="text-orange-400">{result.analysis.event_rate_autocorr_lag1.toFixed(3)}</span></span>
                    </div>
                  </div>
                  
                  {/* Interpretation */}
                  <div className="mt-4 p-3 rounded-sm border border-cyan-500/30 bg-cyan-500/5">
                    <div className="text-xs text-cyan-400 font-mono">{result.analysis.interpretation}</div>
                  </div>
                </CardContent>
              </Card>
            )}
            
            {/* Multi-Seed Summary */}
            {multiResult && mode === 'multi' && (
              <Card className="bg-card/50 border-border/50">
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm font-mono uppercase flex items-center gap-2">
                    <GitBranch className="w-4 h-4 text-green-400" />
                    Multi-Seed Analysis ({multiResult.n_seeds} seeds)
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    {/* Dominant Regime */}
                    <div className="p-3 rounded-sm border border-border/50 bg-background/50">
                      <div className="text-xs text-muted-foreground mb-1">Dominant Regime</div>
                      <Badge className={`font-mono text-xs ${getRegimeBadgeColor(multiResult.dominant_regime)}`}>
                        {multiResult.dominant_regime.toUpperCase()}
                      </Badge>
                      <div className="text-xs text-muted-foreground mt-1">
                        {(multiResult.regime_agreement * 100).toFixed(0)}% agreement
                      </div>
                    </div>
                    
                    {/* Lifetime */}
                    <div className="p-3 rounded-sm border border-border/50 bg-background/50">
                      <div className="text-xs text-muted-foreground mb-1">Lifetime (mean)</div>
                      <div className="text-lg font-mono font-bold text-orange-400">
                        {multiResult.lifetime_mean_across_seeds.toFixed(2)}
                      </div>
                      <div className="text-xs text-muted-foreground">
                        ± {multiResult.lifetime_std_across_seeds.toFixed(2)}
                      </div>
                    </div>
                    
                    {/* Structure Count */}
                    <div className="p-3 rounded-sm border border-border/50 bg-background/50">
                      <div className="text-xs text-muted-foreground mb-1">Structure Count</div>
                      <div className="text-lg font-mono font-bold text-cyan-400">
                        {multiResult.structure_count_mean_across_seeds.toFixed(1)}
                      </div>
                      <div className="text-xs text-muted-foreground">
                        ± {multiResult.structure_count_std_across_seeds.toFixed(1)}
                      </div>
                    </div>
                    
                    {/* Duration */}
                    <div className="p-3 rounded-sm border border-border/50 bg-background/50">
                      <div className="text-xs text-muted-foreground mb-1">Total Time</div>
                      <div className="text-lg font-mono font-bold text-purple-400">
                        {multiResult.total_duration_seconds.toFixed(1)}s
                      </div>
                    </div>
                  </div>
                  
                  {/* Regime Distribution */}
                  <div className="mt-4 p-3 rounded-sm border border-border/50 bg-background/50">
                    <div className="text-xs text-muted-foreground mb-2">Regime Distribution</div>
                    <div className="flex gap-4">
                      {Object.entries(multiResult.regime_distribution).map(([regime, count]) => (
                        <Badge key={regime} className={`font-mono text-xs ${getRegimeBadgeColor(regime)}`}>
                          {regime}: {count}
                        </Badge>
                      ))}
                    </div>
                  </div>
                  
                  {/* Per-Seed Table */}
                  <div className="mt-4 overflow-x-auto">
                    <table className="w-full text-xs font-mono">
                      <thead>
                        <tr className="border-b border-border/50">
                          <th className="text-left p-2 text-muted-foreground">Seed</th>
                          <th className="text-left p-2 text-muted-foreground">Regime</th>
                          <th className="text-left p-2 text-muted-foreground">Lifetime</th>
                          <th className="text-left p-2 text-muted-foreground">Structures</th>
                          <th className="text-left p-2 text-muted-foreground">Births</th>
                          <th className="text-left p-2 text-muted-foreground">Deaths</th>
                        </tr>
                      </thead>
                      <tbody>
                        {multiResult.per_seed_summaries.map((s, i) => (
                          <tr key={i} className="border-b border-border/30">
                            <td className="p-2 text-muted-foreground">{s.seed}</td>
                            <td className="p-2">
                              <Badge className={`text-xs ${getRegimeBadgeColor(s.regime)}`}>{s.regime}</Badge>
                            </td>
                            <td className="p-2">{s.lifetime_mean.toFixed(2)}</td>
                            <td className="p-2">{s.structure_count_mean.toFixed(1)}</td>
                            <td className="p-2 text-green-400">{s.total_births}</td>
                            <td className="p-2 text-red-400">{s.total_deaths}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                  
                  {/* Interpretation */}
                  <div className="mt-4 p-3 rounded-sm border border-green-500/30 bg-green-500/5">
                    <div className="text-xs text-green-400 font-mono">{multiResult.interpretation}</div>
                  </div>
                </CardContent>
              </Card>
            )}
            
            {/* Charts - Only for single run */}
            {result && mode === 'single' && (
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Plot 1: Structure Count vs Time */}
                <Card className="bg-card/50 border-border/50">
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-mono uppercase">Structure Count vs Time</CardTitle>
                    <CardDescription className="text-xs">Total and per-type structure counts over simulation</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <ResponsiveContainer width="100%" height={280}>
                      <AreaChart data={structureCountData}>
                        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                        <XAxis dataKey="t" tick={{ fontSize: 10 }} stroke="#666" />
                        <YAxis tick={{ fontSize: 10 }} stroke="#666" />
                        <Tooltip content={<CustomTooltip />} />
                        <Legend wrapperStyle={{ fontSize: '10px' }} />
                        <Area type="monotone" dataKey="total" stackId="1" stroke="#00d4ff" fill="#00d4ff" fillOpacity={0.3} name="Total" />
                        <Area type="monotone" dataKey="strain" stackId="2" stroke="#f97316" fill="#f97316" fillOpacity={0.2} name="Strain" />
                        <Area type="monotone" dataKey="cluster" stackId="2" stroke="#22c55e" fill="#22c55e" fillOpacity={0.2} name="Cluster" />
                        <Area type="monotone" dataKey="vortex" stackId="2" stroke="#06b6d4" fill="#06b6d4" fillOpacity={0.2} name="Vortex" />
                      </AreaChart>
                    </ResponsiveContainer>
                  </CardContent>
                </Card>
                
                {/* Plot 2: Event Rates vs Time */}
                <Card className="bg-card/50 border-border/50">
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-mono uppercase">Event Rates vs Time</CardTitle>
                    <CardDescription className="text-xs">Births, deaths, merges, splits per timestep</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <ResponsiveContainer width="100%" height={280}>
                      <ComposedChart data={eventRateData}>
                        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                        <XAxis dataKey="t" tick={{ fontSize: 10 }} stroke="#666" />
                        <YAxis tick={{ fontSize: 10 }} stroke="#666" />
                        <Tooltip content={<CustomTooltip />} />
                        <Legend wrapperStyle={{ fontSize: '10px' }} />
                        <Bar dataKey="births" fill="#22c55e" fillOpacity={0.7} name="Births" />
                        <Bar dataKey="deaths" fill="#ef4444" fillOpacity={0.7} name="Deaths" />
                        <Bar dataKey="merges" fill="#eab308" fillOpacity={0.7} name="Merges" />
                        <Bar dataKey="splits" fill="#f97316" fillOpacity={0.7} name="Splits" />
                        <Line type="monotone" dataKey="total" stroke="#00d4ff" strokeWidth={2} dot={false} name="Total Events" />
                      </ComposedChart>
                    </ResponsiveContainer>
                  </CardContent>
                </Card>
                
                {/* Plot 3: S and I_TS vs Time */}
                <Card className="bg-card/50 border-border/50">
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-mono uppercase">S and I_TS vs Time</CardTitle>
                    <CardDescription className="text-xs">Spatial structure and spacetime coupling evolution</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <ResponsiveContainer width="100%" height={280}>
                      <LineChart data={metricsData}>
                        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                        <XAxis dataKey="t" tick={{ fontSize: 10 }} stroke="#666" />
                        <YAxis tick={{ fontSize: 10 }} stroke="#666" domain={[0, 1]} />
                        <Tooltip content={<CustomTooltip />} />
                        <Legend wrapperStyle={{ fontSize: '10px' }} />
                        <Line type="monotone" dataKey="S" stroke="#3b82f6" strokeWidth={2} dot={false} name="S (Spatial)" />
                        <Line type="monotone" dataKey="I_TS" stroke="#8b5cf6" strokeWidth={2} dot={false} name="I_TS (Coupling)" />
                        <Line type="monotone" dataKey="rho_mean" stroke="#f97316" strokeWidth={1} strokeDasharray="3 3" dot={false} name="ρ (norm)" />
                      </LineChart>
                    </ResponsiveContainer>
                  </CardContent>
                </Card>
                
                {/* Plot 4: Lifetime Evolution */}
                <Card className="bg-card/50 border-border/50">
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-mono uppercase">Lifetime Evolution</CardTitle>
                    <CardDescription className="text-xs">Mean, median, and max structure lifetimes over time</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <ResponsiveContainer width="100%" height={280}>
                      <AreaChart data={lifetimeData}>
                        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                        <XAxis dataKey="t" tick={{ fontSize: 10 }} stroke="#666" />
                        <YAxis tick={{ fontSize: 10 }} stroke="#666" />
                        <Tooltip content={<CustomTooltip />} />
                        <Legend wrapperStyle={{ fontSize: '10px' }} />
                        <Area type="monotone" dataKey="max" stroke="#ef4444" fill="#ef4444" fillOpacity={0.1} name="Max" />
                        <Area type="monotone" dataKey="mean" stroke="#22c55e" fill="#22c55e" fillOpacity={0.2} name="Mean" />
                        <Line type="monotone" dataKey="median" stroke="#eab308" strokeWidth={2} dot={false} name="Median" />
                      </AreaChart>
                    </ResponsiveContainer>
                  </CardContent>
                </Card>
                
                {/* Plot 5: Lifetime Histogram */}
                <Card className="bg-card/50 border-border/50 lg:col-span-2">
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-mono uppercase">Lifetime Distribution Histogram</CardTitle>
                    <CardDescription className="text-xs">
                      Distribution type: <span className="text-orange-400 font-mono">{result.analysis.lifetime_distribution_type}</span>
                      {' | '}n={result.all_lifetimes?.length || 0} structures
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <ResponsiveContainer width="100%" height={200}>
                      <BarChart data={lifetimeHistogram}>
                        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
                        <XAxis dataKey="range" tick={{ fontSize: 8 }} stroke="#666" interval={1} />
                        <YAxis tick={{ fontSize: 10 }} stroke="#666" />
                        <Tooltip content={<CustomTooltip />} />
                        <Bar dataKey="count" fill="#8b5cf6" fillOpacity={0.7} name="Count" />
                      </BarChart>
                    </ResponsiveContainer>
                  </CardContent>
                </Card>
              </div>
            )}
            
            {/* Summary Stats */}
            {result && mode === 'single' && (
              <Card className="bg-card/50 border-border/50">
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-mono uppercase flex items-center gap-2">
                    <Zap className="w-4 h-4 text-yellow-400" />
                    Simulation Summary
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-3 md:grid-cols-6 gap-3">
                    <div className="p-2 rounded-sm border border-border/50 bg-background/50 text-center">
                      <div className="text-lg font-mono font-bold text-green-400">{result.total_births}</div>
                      <div className="text-xs text-muted-foreground">Births</div>
                    </div>
                    <div className="p-2 rounded-sm border border-border/50 bg-background/50 text-center">
                      <div className="text-lg font-mono font-bold text-red-400">{result.total_deaths}</div>
                      <div className="text-xs text-muted-foreground">Deaths</div>
                    </div>
                    <div className="p-2 rounded-sm border border-border/50 bg-background/50 text-center">
                      <div className="text-lg font-mono font-bold text-yellow-400">{result.total_merges}</div>
                      <div className="text-xs text-muted-foreground">Merges</div>
                    </div>
                    <div className="p-2 rounded-sm border border-border/50 bg-background/50 text-center">
                      <div className="text-lg font-mono font-bold text-orange-400">{result.total_splits}</div>
                      <div className="text-xs text-muted-foreground">Splits</div>
                    </div>
                    <div className="p-2 rounded-sm border border-border/50 bg-background/50 text-center">
                      <div className="text-lg font-mono font-bold text-cyan-400">{result.final_structure_count}</div>
                      <div className="text-xs text-muted-foreground">Final Count</div>
                    </div>
                    <div className="p-2 rounded-sm border border-border/50 bg-background/50 text-center">
                      <div className="text-lg font-mono font-bold text-purple-400">{result.duration_seconds.toFixed(2)}s</div>
                      <div className="text-xs text-muted-foreground">Duration</div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        )}
        
        {/* No Results Yet */}
        {!result && !multiResult && !running && (
          <Card className="bg-card/50 border-border/50">
            <CardContent className="flex flex-col items-center justify-center py-16">
              <Activity className="w-16 h-16 text-muted-foreground/50 mb-4" />
              <h3 className="text-xl font-semibold mb-2">Long-Path Dynamics Analysis</h3>
              <p className="text-sm text-muted-foreground text-center max-w-md">
                Run extended simulations (10-20x normal length) to analyze:
                steady state convergence, oscillatory behavior, lifetime distributions,
                and structure population dynamics.
              </p>
              <div className="mt-6 grid grid-cols-2 gap-4 text-xs text-muted-foreground">
                <div className="p-3 rounded border border-border/50">
                  <div className="font-mono text-cyan-400 mb-1">Core Questions</div>
                  <ul className="space-y-1">
                    <li>• Does structure count stabilize?</li>
                    <li>• Heavy-tail vs exponential lifetimes?</li>
                    <li>• Event rates decay, plateau, or oscillate?</li>
                  </ul>
                </div>
                <div className="p-3 rounded border border-border/50">
                  <div className="font-mono text-purple-400 mb-1">Regime Classification</div>
                  <ul className="space-y-1">
                    <li>• <span className="text-green-400">Convergent</span>: reaches steady state</li>
                    <li>• <span className="text-blue-400">Oscillatory</span>: periodic fluctuations</li>
                    <li>• <span className="text-orange-400">Steady churn</span>: continuous reorganization</li>
                  </ul>
                </div>
              </div>
            </CardContent>
          </Card>
        )}
        
        {/* Info Footer */}
        <Card className="bg-card/50 border-border/50">
          <CardContent className="py-3">
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              <Info className="w-4 h-4" />
              <span>
                Paper 2 Phase 1: Long-path dynamics establishes temporal behavior before spatial pattern interpretation.
                Next phases: Clustering/filament detection, Regime mapping across (α, λ, noise).
              </span>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default LongPathDynamics;
