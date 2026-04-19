import React, { useState, useCallback, useRef, useEffect, useMemo } from 'react';
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
  Hexagon, Target, Flame, SkipForward, SkipBack, FastForward, Sparkles
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
  trajectories = [],
  showTrajectories = false,
  selectedTrackedId = null,
  getStructureState = () => 'active',
  eventFilter = { showBirths: true, showDeaths: true, showActive: true, selectedOnly: false },
  trackedStructures = null,
  // 3D slice projection props
  sliceAxis = null, // 'xy', 'xz', 'yz', or null for 2D
  slicePosition = 0, // Position of the slice center (e.g., z value for XY slice)
  sliceThickness = 3, // How far from center to include structures
  showAllZ = false, // Debug mode to show all structures regardless of slice
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

  // ============================================
  // 3D SLICE PROJECTION HELPERS
  // ============================================
  
  // Get the perpendicular axis index for each slice type
  const getSliceAxisIndex = () => {
    if (sliceAxis === 'xy') return 2; // z is perpendicular
    if (sliceAxis === 'xz') return 1; // y is perpendicular
    if (sliceAxis === 'yz') return 0; // x is perpendicular
    return null;
  };
  
  // Project 3D position to 2D based on slice type
  const projectPosition = (pos) => {
    if (!pos || pos.length < 2) return { x: 0, y: 0, sliceDistance: 0, inSlice: true };
    
    // 2D mode - no projection needed
    if (!sliceAxis || pos.length < 3) {
      return { 
        x: pos[0], 
        y: pos[1], 
        sliceDistance: 0, 
        inSlice: true,
        opacity: 1.0
      };
    }
    
    // 3D slice projection
    let projX, projY, sliceDistance;
    const perpAxis = getSliceAxisIndex();
    
    if (sliceAxis === 'xy') {
      // XY slice: show x,y, filter by z
      projX = pos[0];
      projY = pos[1];
      sliceDistance = Math.abs(pos[2] - slicePosition);
    } else if (sliceAxis === 'xz') {
      // XZ slice: show x,z (z maps to y in display), filter by y
      projX = pos[0];
      projY = pos[2];
      sliceDistance = Math.abs(pos[1] - slicePosition);
    } else if (sliceAxis === 'yz') {
      // YZ slice: show y,z (y maps to x, z maps to y in display), filter by x
      projX = pos[1];
      projY = pos[2];
      sliceDistance = Math.abs(pos[0] - slicePosition);
    }
    
    // Check if within slice thickness
    const inSlice = showAllZ || sliceDistance <= sliceThickness;
    
    // Calculate opacity based on distance (normalized fade)
    // opacity = max(0, 1 - |d| / δ)
    const opacity = showAllZ ? 0.3 : Math.max(0, 1 - sliceDistance / sliceThickness);
    
    return {
      x: projX,
      y: projY,
      sliceDistance,
      inSlice,
      opacity
    };
  };
  
  // Convert projected position to pixel coordinates
  const toPixel = (pos) => {
    const projected = projectPosition(pos);
    return {
      x: (projected.x * scale) * cellSize,
      y: (projected.y * scale) * cellSize,
      sliceDistance: projected.sliceDistance,
      inSlice: projected.inSlice,
      opacity: projected.opacity
    };
  };
  
  // Convert trajectory to SVG path (2D only for now)
  const trajectoryToPath = (points) => {
    if (!points || points.length < 2) return '';
    // For 3D, only show trajectory if most points are in slice
    if (sliceAxis && points[0]?.length >= 3) {
      const inSliceCount = points.filter(p => {
        const proj = projectPosition(p);
        return proj.inSlice;
      }).length;
      if (inSliceCount < points.length * 0.3) return ''; // Skip if <30% in slice
    }
    const scaled = points.map(p => {
      const proj = projectPosition(p);
      return { x: (proj.x * scale) * cellSize, y: (proj.y * scale) * cellSize };
    });
    return scaled.map((pt, i) => `${i === 0 ? 'M' : 'L'}${pt.x},${pt.y}`).join(' ');
  };
  
  // Find tracked structure for a given structure position
  const findTrackedForStruct = (pos, structType) => {
    if (!trackedStructures) return null;
    const list = trackedStructures[structType] || [];
    let closest = null;
    let minDist = 5;
    for (const t of list) {
      const tPos = t.current_position;
      if (tPos && pos) {
        const dist = Math.sqrt(Math.pow(tPos[0]-pos[0],2) + Math.pow(tPos[1]-pos[1],2));
        if (dist < minDist) {
          minDist = dist;
          closest = t;
        }
      }
    }
    return closest;
  };
  
  // Check if structure should be visible based on filter and state
  const shouldShowStructure = (tracked, structId = null) => {
    if (eventFilter.selectedOnly && selectedTrackedId && structId !== selectedTrackedId) {
      return false;
    }
    if (!tracked) return eventFilter.showActive;
    
    const state = getStructureState(tracked);
    if (state === 'birth') return eventFilter.showBirths;
    if (state === 'death') return eventFilter.showDeaths;
    if (state === 'active') return eventFilter.showActive;
    if (state === 'unborn' || state === 'dead') return false;
    return eventFilter.showActive;
  };
  
  // Get animation style based on state
  const getAnimationStyle = (tracked) => {
    if (!tracked) return {};
    const state = getStructureState(tracked);
    
    if (state === 'birth') {
      return { 
        filter: 'drop-shadow(0 0 4px rgba(74, 222, 128, 0.8))',
        animation: 'pulse 0.5s ease-in-out'
      };
    }
    if (state === 'death') {
      return { 
        opacity: 0.4,
        filter: 'grayscale(0.5)'
      };
    }
    return {};
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
          {/* Trajectories (rendered first, behind structures) */}
          {showTrajectories && trajectories.map((traj, i) => (
            <path
              key={`traj-${traj.id}`}
              d={trajectoryToPath(traj.points)}
              fill="none"
              stroke={traj.isSelected ? '#fff' : traj.color}
              strokeWidth={traj.isSelected ? 2 : 1}
              strokeOpacity={traj.isSelected ? 0.9 : 0.4}
              strokeDasharray={traj.status === 'disappeared' ? '2,2' : 'none'}
            />
          ))}
          
          {/* Strain Nodes - Orange diamonds */}
          {showStrainNodes && structures.strain_nodes?.map((node, i) => {
            const pixelData = toPixel(node.position);
            const { x, y, sliceDistance, inSlice, opacity: sliceOpacity } = pixelData;
            
            // Skip if not in slice (unless showAllZ)
            if (!inSlice) return null;
            
            const size = 4 + (node.stability || 0.5) * 4;
            const tracked = findTrackedForStruct(node.position, 'strain_nodes');
            
            if (!shouldShowStructure(tracked, tracked?.id)) return null;
            
            const animStyle = getAnimationStyle(tracked);
            const state = tracked ? getStructureState(tracked) : 'active';
            const baseOpacity = state === 'death' ? 0.4 : 0.8;
            const finalOpacity = baseOpacity * sliceOpacity;
            
            return (
              <g key={`strain-${i}`} style={{ pointerEvents: 'visiblePainted', cursor: 'pointer', ...animStyle, opacity: finalOpacity }}>
                <polygon
                  points={`${x},${y-size} ${x+size},${y} ${x},${y+size} ${x-size},${y}`}
                  fill={state === 'birth' ? 'rgba(74, 222, 128, 0.9)' : state === 'death' ? 'rgba(249, 115, 22, 0.5)' : 'rgba(249, 115, 22, 1)'}
                  stroke={state === 'birth' ? '#4ade80' : '#fff'}
                  strokeWidth={state === 'birth' ? 2 : 0.5}
                  onMouseEnter={() => setHoveredStructure({ 
                    type: 'strain', data: node, x, y, state,
                    sliceDistance: sliceAxis ? sliceDistance : null,
                    sliceAxis,
                    showAllZ
                  })}
                  onMouseLeave={() => setHoveredStructure(null)}
                  onClick={(e) => { e.stopPropagation(); onStructureClick({ type: 'strain', data: node }); }}
                />
                {state === 'birth' && (
                  <circle cx={x} cy={y} r={size + 4} fill="none" stroke="#4ade80" strokeWidth="1" opacity="0.5">
                    <animate attributeName="r" from={size} to={size + 8} dur="0.5s" repeatCount="1" />
                    <animate attributeName="opacity" from="0.8" to="0" dur="0.5s" repeatCount="1" />
                  </circle>
                )}
              </g>
            );
          })}
          
          {/* Coherence Clusters - Green circles with radius */}
          {showClusters && structures.coherence_clusters?.map((cluster, i) => {
            const pixelData = toPixel(cluster.center);
            const { x, y, sliceDistance, inSlice, opacity: sliceOpacity } = pixelData;
            
            // Skip if not in slice
            if (!inSlice) return null;
            
            // For 3D, scale radius based on how much of the cluster intersects the slice
            // This is an approximation: radius visible ≈ sqrt(r² - d²) where d is slice distance
            let effectiveRadius = cluster.size || 2;
            if (sliceAxis && sliceDistance > 0 && effectiveRadius > sliceDistance) {
              effectiveRadius = Math.sqrt(Math.pow(effectiveRadius, 2) - Math.pow(sliceDistance, 2));
            }
            const radius = Math.max(4, effectiveRadius * scale * cellSize);
            
            const tracked = findTrackedForStruct(cluster.center, 'coherence_clusters');
            
            if (!shouldShowStructure(tracked, tracked?.id)) return null;
            
            const animStyle = getAnimationStyle(tracked);
            const state = tracked ? getStructureState(tracked) : 'active';
            const finalOpacity = sliceOpacity;
            
            return (
              <g key={`cluster-${i}`} style={{ pointerEvents: 'visiblePainted', cursor: 'pointer', ...animStyle, opacity: finalOpacity }}>
                <circle
                  cx={x}
                  cy={y}
                  r={radius}
                  fill={state === 'birth' ? 'rgba(74, 222, 128, 0.4)' : state === 'death' ? 'rgba(74, 222, 128, 0.1)' : 'rgba(74, 222, 128, 0.2)'}
                  stroke={state === 'birth' ? '#fff' : '#4ade80'}
                  strokeWidth={state === 'birth' ? 2 : 1.5}
                  strokeDasharray="3,2"
                  onMouseEnter={() => setHoveredStructure({ 
                    type: 'cluster', data: cluster, x, y, state,
                    sliceDistance: sliceAxis ? sliceDistance : null,
                    sliceAxis,
                    showAllZ,
                    isSliceProjection: sliceAxis !== null && sliceDistance > 0
                  })}
                  onMouseLeave={() => setHoveredStructure(null)}
                  onClick={(e) => { e.stopPropagation(); onStructureClick({ type: 'cluster', data: cluster }); }}
                />
                <circle
                  cx={x}
                  cy={y}
                  r={3}
                  fill={state === 'death' ? 'rgba(74, 222, 128, 0.4)' : '#4ade80'}
                  style={{ pointerEvents: 'none' }}
                />
                {state === 'birth' && (
                  <circle cx={x} cy={y} r={radius} fill="none" stroke="#fff" strokeWidth="2" opacity="0.5">
                    <animate attributeName="r" from={radius} to={radius + 10} dur="0.5s" repeatCount="1" />
                    <animate attributeName="opacity" from="0.8" to="0" dur="0.5s" repeatCount="1" />
                  </circle>
                )}
              </g>
            );
          })}
          
          {/* Particle Nodes - Colored by type */}
          {showParticleNodes && structures.particle_nodes?.map((particle, i) => {
            const pixelData = toPixel(particle.position);
            const { x, y, sliceDistance, inSlice, opacity: sliceOpacity } = pixelData;
            
            // Skip if not in slice
            if (!inSlice) return null;
            
            const tracked = findTrackedForStruct(particle.position, 'particle_nodes');
            
            if (!shouldShowStructure(tracked, tracked?.id)) return null;
            
            const animStyle = getAnimationStyle(tracked);
            const state = tracked ? getStructureState(tracked) : 'active';
            
            let fill, stroke;
            if (state === 'birth') {
              fill = 'rgba(74, 222, 128, 0.9)';
              stroke = '#fff';
            } else if (state === 'death') {
              fill = 'rgba(156, 163, 175, 0.4)';
              stroke = '#666';
            } else {
              switch(particle.structure_type) {
                case 'stable':
                  fill = 'rgba(168, 85, 247, 0.9)';
                  stroke = '#fff';
                  break;
                case 'proto-particle':
                  fill = 'rgba(234, 179, 8, 0.9)';
                  stroke = '#fff';
                  break;
                default:
                  fill = 'rgba(156, 163, 175, 0.7)';
                  stroke = '#9ca3af';
              }
            }
            
            const finalOpacity = sliceOpacity;
            
            return (
              <g key={`particle-${i}`} style={{ pointerEvents: 'visiblePainted', cursor: 'pointer', ...animStyle, opacity: finalOpacity }}>
                <circle
                  cx={x}
                  cy={y}
                  r={6}
                  fill={fill}
                  stroke={stroke}
                  strokeWidth={state === 'birth' ? 2.5 : 1.5}
                  onMouseEnter={() => setHoveredStructure({ 
                    type: 'particle', data: particle, x, y, state,
                    sliceDistance: sliceAxis ? sliceDistance : null,
                    sliceAxis,
                    showAllZ
                  })}
                  onMouseLeave={() => setHoveredStructure(null)}
                  onClick={(e) => { e.stopPropagation(); onStructureClick({ type: 'particle', data: particle }); }}
                />
                {particle.structure_type === 'stable' && state !== 'death' && (
                  <circle cx={x} cy={y} r={2} fill="#fff" style={{ pointerEvents: 'none' }} />
                )}
                {state === 'birth' && (
                  <circle cx={x} cy={y} r={6} fill="none" stroke="#4ade80" strokeWidth="2" opacity="0.5">
                    <animate attributeName="r" from="6" to="14" dur="0.5s" repeatCount="1" />
                    <animate attributeName="opacity" from="0.8" to="0" dur="0.5s" repeatCount="1" />
                  </circle>
                )}
              </g>
            );
          })}
          
          {/* Torsion Vortices - Cyan spirals with chirality indicator */}
          {showVortices && structures.torsion_vortices?.map((vortex, i) => {
            const pixelData = toPixel(vortex.position);
            const { x, y, sliceDistance, inSlice, opacity: sliceOpacity } = pixelData;
            
            // Skip if not in slice
            if (!inSlice) return null;
            
            const r = Math.max(4, (vortex.radius || 1) * scale * cellSize);
            const chirality = vortex.chirality > 0 ? 1 : -1;
            const tracked = findTrackedForStruct(vortex.position, 'torsion_vortices');
            
            if (!shouldShowStructure(tracked, tracked?.id)) return null;
            
            const animStyle = getAnimationStyle(tracked);
            const state = tracked ? getStructureState(tracked) : 'active';
            const finalOpacity = sliceOpacity;
            
            return (
              <g key={`vortex-${i}`} style={{ pointerEvents: 'visiblePainted', cursor: 'pointer', ...animStyle, opacity: finalOpacity }}>
                <circle
                  cx={x}
                  cy={y}
                  r={r}
                  fill={state === 'birth' ? 'rgba(74, 222, 128, 0.2)' : state === 'death' ? 'rgba(0, 212, 255, 0.05)' : 'rgba(0, 212, 255, 0.1)'}
                  stroke={state === 'birth' ? '#4ade80' : state === 'death' ? 'rgba(0, 212, 255, 0.4)' : '#00d4ff'}
                  strokeWidth={state === 'birth' ? 3 : 2}
                  onMouseEnter={() => setHoveredStructure({ 
                    type: 'vortex', data: vortex, x, y, state,
                    sliceDistance: sliceAxis ? sliceDistance : null,
                    sliceAxis,
                    showAllZ
                  })}
                  onMouseLeave={() => setHoveredStructure(null)}
                  onClick={(e) => { e.stopPropagation(); onStructureClick({ type: 'vortex', data: vortex }); }}
                />
                <path
                  d={chirality > 0 
                    ? `M${x-3},${y-1} L${x},${y-4} L${x+3},${y-1}` 
                    : `M${x-3},${y+1} L${x},${y+4} L${x+3},${y+1}`}
                  fill="none"
                  stroke={state === 'death' ? 'rgba(0, 212, 255, 0.4)' : '#00d4ff'}
                  strokeWidth="1.5"
                  style={{ pointerEvents: 'none' }}
                />
                {state === 'birth' && (
                  <circle cx={x} cy={y} r={r} fill="none" stroke="#4ade80" strokeWidth="2" opacity="0.5">
                    <animate attributeName="r" from={r} to={r + 8} dur="0.5s" repeatCount="1" />
                    <animate attributeName="opacity" from="0.8" to="0" dur="0.5s" repeatCount="1" />
                  </circle>
                )}
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
            <div className="text-xs font-mono uppercase font-bold mb-1 flex items-center gap-1" style={{
              color: hoveredStructure.type === 'strain' ? '#f97316' :
                     hoveredStructure.type === 'cluster' ? '#4ade80' :
                     hoveredStructure.type === 'particle' ? '#a855f7' : '#00d4ff'
            }}>
              {hoveredStructure.type}
              {hoveredStructure.state && hoveredStructure.state !== 'active' && (
                <span className={`text-[10px] px-1 rounded ${
                  hoveredStructure.state === 'birth' ? 'bg-green-500/20 text-green-400' :
                  hoveredStructure.state === 'death' ? 'bg-red-500/20 text-red-400' : ''
                }`}>
                  {hoveredStructure.state}
                </span>
              )}
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
            {/* Slice distance info for 3D */}
            {hoveredStructure.sliceAxis && (
              <div className="mt-1 pt-1 border-t border-border/30">
                <div className="text-xs text-muted-foreground">
                  {hoveredStructure.sliceAxis.toUpperCase()} slice
                </div>
                <div className="text-xs">
                  d: {hoveredStructure.sliceDistance?.toFixed(1)}
                  {hoveredStructure.showAllZ && <span className="text-yellow-400 ml-1">(debug)</span>}
                </div>
                {hoveredStructure.isSliceProjection && (
                  <div className="text-xs text-yellow-500">⚠ projected</div>
                )}
              </div>
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
  const [showTrajectories, setShowTrajectories] = useState(true);
  
  // 3D slice projection controls
  const [sliceThickness, setSliceThickness] = useState(3);
  const [showAllZ, setShowAllZ] = useState(false);
  
  // Selected structure for inspector
  const [selectedStructure, setSelectedStructure] = useState(null);
  const [selectedTrackedId, setSelectedTrackedId] = useState(null);
  
  // Animation state
  const [animationSpeed, setAnimationSpeed] = useState(100); // ms per frame
  const [eventFilter, setEventFilter] = useState({
    showBirths: true,
    showDeaths: true,
    showActive: true,
    selectedOnly: false
  });
  
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
      }, animationSpeed);
    }
    return () => clearInterval(intervalRef.current);
  }, [isPlaying, result, animationSpeed]);
  
  // Current frame data - MUST be defined BEFORE any dependent hooks
  const currentMeasurement = result?.measurements?.[playbackIndex] || {};
  const currentSnapshot = result?.field_snapshots?.[Math.floor(playbackIndex / 5)] || {};
  const currentTimelineFrame = result?.structures_timeline?.[playbackIndex] || null;
  
  // Get current timeline time
  const currentTime = currentMeasurement.t || 0;
  
  // Find structures that are active/born/died at current time
  const getStructureState = useCallback((tracked) => {
    if (!tracked || currentTime === undefined) return 'unknown';
    
    const birthTime = tracked.birth_time;
    const lastSeen = tracked.last_seen_time;
    const epsilon = 0.05; // Time tolerance
    
    if (Math.abs(currentTime - birthTime) < epsilon) return 'birth';
    if (tracked.status === 'disappeared' && Math.abs(currentTime - lastSeen) < epsilon) return 'death';
    if (currentTime >= birthTime && currentTime <= lastSeen) return 'active';
    if (currentTime < birthTime) return 'unborn';
    return 'dead';
  }, [currentTime]);
  
  // Get structures visible at current timeline frame
  const currentFrameStructures = useMemo(() => {
    if (!currentTimelineFrame) return null;
    return {
      strain_nodes: currentTimelineFrame.strain_nodes || [],
      particle_nodes: currentTimelineFrame.particle_nodes || [],
      coherence_clusters: currentTimelineFrame.coherence_clusters || [],
      torsion_vortices: currentTimelineFrame.torsion_vortices || []
    };
  }, [currentTimelineFrame]);
  
  // Find events (births/deaths) at current time
  const currentEvents = useMemo(() => {
    if (!result?.tracked_structures) return { births: [], deaths: [] };
    
    const births = [];
    const deaths = [];
    const epsilon = 0.05;
    
    for (const structType of ['strain_nodes', 'particle_nodes', 'coherence_clusters', 'torsion_vortices']) {
      for (const tracked of (result.tracked_structures[structType] || [])) {
        if (Math.abs(currentTime - tracked.birth_time) < epsilon) {
          births.push({ ...tracked, structType });
        }
        if (tracked.status === 'disappeared' && Math.abs(currentTime - tracked.last_seen_time) < epsilon) {
          deaths.push({ ...tracked, structType });
        }
      }
    }
    
    return { births, deaths };
  }, [result, currentTime]);
  
  // Jump to specific events
  const jumpToFirstBirth = useCallback(() => {
    if (!result?.tracked_structures) return;
    
    let minBirthTime = Infinity;
    for (const structType of ['strain_nodes', 'particle_nodes', 'coherence_clusters', 'torsion_vortices']) {
      for (const tracked of (result.tracked_structures[structType] || [])) {
        if (tracked.birth_time < minBirthTime) {
          minBirthTime = tracked.birth_time;
        }
      }
    }
    
    if (minBirthTime < Infinity && result.measurements) {
      const idx = result.measurements.findIndex(m => m.t >= minBirthTime);
      if (idx >= 0) setPlaybackIndex(idx);
    }
  }, [result]);
  
  const jumpToNextEvent = useCallback(() => {
    if (!result?.tracked_structures || !result.measurements) return;
    
    const events = [];
    for (const structType of ['strain_nodes', 'particle_nodes', 'coherence_clusters', 'torsion_vortices']) {
      for (const tracked of (result.tracked_structures[structType] || [])) {
        events.push({ t: tracked.birth_time, type: 'birth' });
        if (tracked.status === 'disappeared') {
          events.push({ t: tracked.last_seen_time, type: 'death' });
        }
      }
    }
    
    events.sort((a, b) => a.t - b.t);
    const nextEvent = events.find(e => e.t > currentTime + 0.01);
    
    if (nextEvent) {
      const idx = result.measurements.findIndex(m => m.t >= nextEvent.t);
      if (idx >= 0) setPlaybackIndex(idx);
    }
  }, [result, currentTime]);
  
  const jumpToFinalFrame = useCallback(() => {
    if (result?.measurements) {
      setPlaybackIndex(result.measurements.length - 1);
    }
  }, [result]);
  
  // Find tracked structure by ID or approximate position match
  const findTrackedStructure = useCallback((type, data) => {
    if (!result?.tracked_structures) return null;
    
    const structMap = {
      'strain': 'strain_nodes',
      'cluster': 'coherence_clusters', 
      'particle': 'particle_nodes',
      'vortex': 'torsion_vortices'
    };
    
    const structList = result.tracked_structures[structMap[type]] || [];
    const pos = data.position || data.center;
    
    // Find by closest current position
    let closest = null;
    let minDist = Infinity;
    
    for (const tracked of structList) {
      const tPos = tracked.current_position;
      if (tPos && pos) {
        const dist = Math.sqrt(
          Math.pow(tPos[0] - pos[0], 2) + 
          Math.pow(tPos[1] - pos[1], 2)
        );
        if (dist < minDist && dist < 5) {
          minDist = dist;
          closest = tracked;
        }
      }
    }
    
    return closest;
  }, [result]);
  
  // Handle structure selection with tracking lookup
  const handleStructureClick = useCallback((structInfo) => {
    setSelectedStructure(structInfo);
    const tracked = findTrackedStructure(structInfo.type, structInfo.data);
    setSelectedTrackedId(tracked?.id || null);
  }, [findTrackedStructure]);
  
  // Get all trajectories for overlay
  const allTrajectories = useMemo(() => {
    if (!result?.tracked_structures || !showTrajectories) return [];
    
    const trajectories = [];
    for (const structType of ['strain_nodes', 'particle_nodes', 'coherence_clusters', 'torsion_vortices']) {
      const color = structType === 'strain_nodes' ? '#f97316' :
                    structType === 'particle_nodes' ? '#a855f7' :
                    structType === 'coherence_clusters' ? '#4ade80' : '#00d4ff';
      
      for (const tracked of (result.tracked_structures[structType] || [])) {
        if (tracked.trajectory && tracked.trajectory.length > 1) {
          trajectories.push({
            id: tracked.id,
            points: tracked.trajectory,
            color,
            status: tracked.status,
            isSelected: tracked.id === selectedTrackedId
          });
        }
      }
    }
    return trajectories;
  }, [result, showTrajectories, selectedTrackedId]);
  
  // Get current tracked structure for inspector
  const selectedTracked = useMemo(() => {
    if (!selectedTrackedId || !result?.tracked_structures) return null;
    
    for (const structType of ['strain_nodes', 'particle_nodes', 'coherence_clusters', 'torsion_vortices']) {
      const found = (result.tracked_structures[structType] || []).find(s => s.id === selectedTrackedId);
      if (found) return found;
    }
    return null;
  }, [selectedTrackedId, result]);
  
  // Helper to find any tracked structure by ID (for lineage navigation)
  const findTrackedById = useCallback((structId) => {
    if (!structId || !result?.tracked_structures) return null;
    
    for (const structType of ['strain_nodes', 'particle_nodes', 'coherence_clusters', 'torsion_vortices']) {
      const found = (result.tracked_structures[structType] || []).find(s => s.id === structId);
      if (found) return found;
    }
    return null;
  }, [result]);
  
  // Navigate to a related structure (parent or child) and optionally jump to its birth time
  const navigateToStructure = useCallback((structId, jumpToTime = true) => {
    const targetStruct = findTrackedById(structId);
    if (targetStruct) {
      setSelectedTrackedId(structId);
      
      if (jumpToTime && targetStruct.birth_time != null && result?.measurements) {
        // Find the closest timeline index to the birth time
        const targetTime = targetStruct.birth_time;
        let closestIdx = 0;
        let minDiff = Math.abs((result.measurements[0]?.t || 0) - targetTime);
        
        for (let i = 1; i < result.measurements.length; i++) {
          const diff = Math.abs((result.measurements[i]?.t || 0) - targetTime);
          if (diff < minDiff) {
            minDiff = diff;
            closestIdx = i;
          }
        }
        
        setPlaybackIndex(closestIdx);
      }
      
      toast.info(`Navigated to ${structId}`);
    }
  }, [findTrackedById, result, setSelectedTrackedId, setPlaybackIndex]);
  
  // Derive lineage info for selected structure
  const selectedLineageInfo = useMemo(() => {
    if (!selectedTracked) return null;
    
    const info = {
      eventType: 'none',
      eventTime: null,
      parents: [],
      children: []
    };
    
    // Determine event type based on parent_ids and child_ids
    const hasParents = selectedTracked.parent_ids?.length > 0;
    const hasChildren = selectedTracked.child_ids?.length > 0;
    
    if (hasParents && selectedTracked.parent_ids.length >= 2) {
      // This structure was created from a merge
      info.eventType = 'merge';
      info.eventTime = selectedTracked.birth_time; // Merge happened at birth
    } else if (hasChildren && selectedTracked.child_ids.length >= 2) {
      // This structure split into children
      info.eventType = 'split';
      // Find the split time from the first child's birth
      const firstChild = findTrackedById(selectedTracked.child_ids[0]);
      if (firstChild) {
        info.eventTime = firstChild.birth_time;
      }
    } else if (hasParents && selectedTracked.parent_ids.length === 1) {
      // Single parent - could be from a split
      const parent = findTrackedById(selectedTracked.parent_ids[0]);
      if (parent && parent.child_ids?.length >= 2) {
        info.eventType = 'split-child';
        info.eventTime = selectedTracked.birth_time;
      }
    } else if (hasChildren && selectedTracked.child_ids.length === 1) {
      // Single child - could be from a merge
      const child = findTrackedById(selectedTracked.child_ids[0]);
      if (child && child.parent_ids?.length >= 2) {
        info.eventType = 'merge-parent';
        info.eventTime = child.birth_time;
      }
    }
    
    // Resolve parent details
    if (hasParents) {
      info.parents = selectedTracked.parent_ids.map(pid => {
        const parent = findTrackedById(pid);
        return {
          id: pid,
          birthTime: parent?.birth_time,
          lastSeenTime: parent?.last_seen_time,
          status: parent?.status || 'unknown'
        };
      });
    }
    
    // Resolve children details
    if (hasChildren) {
      info.children = selectedTracked.child_ids.map(cid => {
        const child = findTrackedById(cid);
        return {
          id: cid,
          birthTime: child?.birth_time,
          lastSeenTime: child?.last_seen_time,
          status: child?.status || 'unknown'
        };
      });
    }
    
    return info;
  }, [selectedTracked, findTrackedById]);
  
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
                {/* Main playback controls */}
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
                    title="Reset to start"
                  >
                    <RotateCcw className="w-4 h-4" />
                  </Button>
                  <span className="text-xs font-mono text-muted-foreground ml-auto">
                    t = {currentMeasurement.t?.toFixed(2) || '0.00'}
                  </span>
                </div>
                
                {/* Timeline scrubber */}
                <Slider
                  value={[playbackIndex]}
                  onValueChange={([v]) => setPlaybackIndex(v)}
                  min={0}
                  max={Math.max((result.measurements?.length || 1) - 1, 0)}
                  step={1}
                />
                
                {/* Event navigation */}
                <div className="flex items-center gap-2">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={jumpToFirstBirth}
                    className="font-mono text-xs h-7 px-2"
                    title="Jump to first birth"
                  >
                    <SkipBack className="w-3 h-3 mr-1" />
                    <Sparkles className="w-3 h-3" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={jumpToNextEvent}
                    className="font-mono text-xs h-7 px-2"
                    title="Jump to next event"
                  >
                    <SkipForward className="w-3 h-3" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={jumpToFinalFrame}
                    className="font-mono text-xs h-7 px-2"
                    title="Jump to end"
                  >
                    <FastForward className="w-3 h-3" />
                  </Button>
                  
                  {/* Current events indicator */}
                  <div className="ml-auto flex items-center gap-1 text-xs">
                    {currentEvents.births.length > 0 && (
                      <Badge variant="outline" className="text-green-400 h-5 px-1">
                        +{currentEvents.births.length}
                      </Badge>
                    )}
                    {currentEvents.deaths.length > 0 && (
                      <Badge variant="outline" className="text-red-400 h-5 px-1">
                        -{currentEvents.deaths.length}
                      </Badge>
                    )}
                  </div>
                </div>
                
                {/* Speed control */}
                <div className="space-y-1">
                  <div className="flex justify-between text-xs">
                    <span className="text-muted-foreground">Speed</span>
                    <span className="font-mono">{(1000/animationSpeed).toFixed(1)}x</span>
                  </div>
                  <Slider
                    value={[animationSpeed]}
                    onValueChange={([v]) => setAnimationSpeed(v)}
                    min={20}
                    max={500}
                    step={20}
                  />
                </div>
                
                {/* Event filters */}
                <div className="space-y-2">
                  <div className="text-xs text-muted-foreground">Animation Filters</div>
                  <div className="flex flex-wrap gap-2">
                    <label className="flex items-center gap-1 cursor-pointer">
                      <input 
                        type="checkbox" 
                        checked={eventFilter.showBirths}
                        onChange={(e) => setEventFilter(f => ({...f, showBirths: e.target.checked}))}
                        className="w-3 h-3 accent-green-500"
                      />
                      <span className="text-xs text-green-400">Births</span>
                    </label>
                    <label className="flex items-center gap-1 cursor-pointer">
                      <input 
                        type="checkbox" 
                        checked={eventFilter.showDeaths}
                        onChange={(e) => setEventFilter(f => ({...f, showDeaths: e.target.checked}))}
                        className="w-3 h-3 accent-red-500"
                      />
                      <span className="text-xs text-red-400">Deaths</span>
                    </label>
                    <label className="flex items-center gap-1 cursor-pointer">
                      <input 
                        type="checkbox" 
                        checked={eventFilter.showActive}
                        onChange={(e) => setEventFilter(f => ({...f, showActive: e.target.checked}))}
                        className="w-3 h-3 accent-blue-500"
                      />
                      <span className="text-xs text-blue-400">Active</span>
                    </label>
                    <label className="flex items-center gap-1 cursor-pointer">
                      <input 
                        type="checkbox" 
                        checked={eventFilter.selectedOnly}
                        onChange={(e) => setEventFilter(f => ({...f, selectedOnly: e.target.checked}))}
                        className="w-3 h-3 accent-purple-500"
                      />
                      <span className="text-xs text-purple-400">Selected</span>
                    </label>
                  </div>
                </div>
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
                {/* Tracking Statistics */}
                {result?.tracked_structures && (
                  <Card className="bg-card/50 border-border/50 border-l-4 border-l-primary">
                    <CardHeader className="pb-2">
                      <CardTitle className="text-sm font-mono uppercase flex items-center gap-2">
                        <Activity className="w-4 h-4" />
                        Structure Time Tracking
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="grid grid-cols-5 gap-4 text-center">
                        <div>
                          <div className="text-xl font-mono font-bold text-green-400">{result.tracking_births}</div>
                          <div className="text-xs text-muted-foreground">Births</div>
                        </div>
                        <div>
                          <div className="text-xl font-mono font-bold text-red-400">{result.tracking_deaths}</div>
                          <div className="text-xs text-muted-foreground">Deaths</div>
                        </div>
                        <div>
                          <div className="text-xl font-mono font-bold text-yellow-400">{result.tracking_merges}</div>
                          <div className="text-xs text-muted-foreground">Merges</div>
                        </div>
                        <div>
                          <div className="text-xl font-mono font-bold text-blue-400">{result.tracking_splits}</div>
                          <div className="text-xs text-muted-foreground">Splits</div>
                        </div>
                        <div>
                          <div className="text-xl font-mono font-bold text-purple-400">{result.tracking_avg_lifetime?.toFixed(2)}</div>
                          <div className="text-xs text-muted-foreground">Avg Life</div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                )}
                
                {/* Overlay Toggles */}
                <Card className="bg-card/50 border-border/50">
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-mono uppercase">Structure Overlays</CardTitle>
                    <CardDescription className="text-xs">Toggle structure markers and trajectories on field heatmaps</CardDescription>
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
                      <div className="border-l border-border/50 pl-4">
                        <label className="flex items-center gap-2 cursor-pointer">
                          <input 
                            type="checkbox" 
                            checked={showTrajectories} 
                            onChange={(e) => setShowTrajectories(e.target.checked)}
                            className="w-4 h-4 accent-white"
                            data-testid="toggle-trajectories"
                          />
                          <TrendingUp className="w-4 h-4 text-white" />
                          <span className="text-xs font-mono">Trajectories</span>
                        </label>
                      </div>
                    </div>
                    
                    {/* 3D Slice Controls - only show for 3D mode */}
                    {dimension === '3d' && (
                      <div className="mt-4 pt-3 border-t border-border/30">
                        <div className="flex items-center gap-4">
                          <div className="flex-1">
                            <div className="flex justify-between text-xs mb-1">
                              <span className="text-muted-foreground">Slice Thickness</span>
                              <span className="font-mono">{sliceThickness} units</span>
                            </div>
                            <Slider
                              value={[sliceThickness]}
                              onValueChange={([v]) => setSliceThickness(v)}
                              min={1}
                              max={10}
                              step={1}
                            />
                          </div>
                          <label className="flex items-center gap-2 cursor-pointer border-l border-border/50 pl-4">
                            <input 
                              type="checkbox" 
                              checked={showAllZ}
                              onChange={(e) => setShowAllZ(e.target.checked)}
                              className="w-4 h-4 accent-yellow-500"
                            />
                            <span className="text-xs font-mono text-yellow-400">Debug: Show all z</span>
                          </label>
                        </div>
                      </div>
                    )}
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
                            structures={currentFrameStructures || result?.structures}
                            gridSize={gridSize}
                            showStrainNodes={showStrainNodes}
                            showClusters={showClusters}
                            showParticleNodes={showParticleNodes}
                            showVortices={showVortices}
                            trajectories={allTrajectories}
                            showTrajectories={showTrajectories}
                            selectedTrackedId={selectedTrackedId}
                            getStructureState={getStructureState}
                            eventFilter={eventFilter}
                            trackedStructures={result?.tracked_structures}
                            onStructureClick={handleStructureClick}
                          />
                          <FieldHeatmapWithOverlays 
                            data={currentSnapshot.c_eff} 
                            title="c_eff (Speed)" 
                            colorScheme="blue"
                            structures={currentFrameStructures || result?.structures}
                            gridSize={gridSize}
                            showStrainNodes={showStrainNodes}
                            showClusters={showClusters}
                            showParticleNodes={showParticleNodes}
                            showVortices={showVortices}
                            trajectories={allTrajectories}
                            showTrajectories={showTrajectories}
                            selectedTrackedId={selectedTrackedId}
                            getStructureState={getStructureState}
                            eventFilter={eventFilter}
                            trackedStructures={result?.tracked_structures}
                            onStructureClick={handleStructureClick}
                          />
                          <FieldHeatmapWithOverlays 
                            data={currentSnapshot.tau} 
                            title="τ (Medium)" 
                            colorScheme="gray"
                            structures={currentFrameStructures || result?.structures}
                            gridSize={gridSize}
                            showStrainNodes={showStrainNodes}
                            showClusters={showClusters}
                            showParticleNodes={showParticleNodes}
                            showVortices={showVortices}
                            trajectories={allTrajectories}
                            showTrajectories={showTrajectories}
                            selectedTrackedId={selectedTrackedId}
                            getStructureState={getStructureState}
                            eventFilter={eventFilter}
                            trackedStructures={result?.tracked_structures}
                            onStructureClick={handleStructureClick}
                          />
                        </>
                      ) : (
                        <>
                          <FieldHeatmapWithOverlays 
                            data={currentSnapshot.rho_xy} 
                            title="ρ (XY slice)" 
                            colorScheme="heat"
                            structures={currentFrameStructures || result?.structures}
                            gridSize={Math.min(gridSize, 50)}
                            showStrainNodes={showStrainNodes}
                            showClusters={showClusters}
                            showParticleNodes={showParticleNodes}
                            showVortices={showVortices}
                            trajectories={allTrajectories}
                            showTrajectories={showTrajectories}
                            selectedTrackedId={selectedTrackedId}
                            getStructureState={getStructureState}
                            eventFilter={eventFilter}
                            trackedStructures={result?.tracked_structures}
                            sliceAxis="xy"
                            slicePosition={Math.min(gridSize, 50) / 2}
                            sliceThickness={sliceThickness}
                            showAllZ={showAllZ}
                            onStructureClick={handleStructureClick}
                          />
                          <FieldHeatmapWithOverlays 
                            data={currentSnapshot.rho_xz} 
                            title="ρ (XZ slice)" 
                            colorScheme="heat"
                            structures={currentFrameStructures || result?.structures}
                            gridSize={Math.min(gridSize, 50)}
                            showStrainNodes={showStrainNodes}
                            showClusters={showClusters}
                            showParticleNodes={showParticleNodes}
                            showVortices={showVortices}
                            trajectories={allTrajectories}
                            showTrajectories={showTrajectories}
                            selectedTrackedId={selectedTrackedId}
                            getStructureState={getStructureState}
                            eventFilter={eventFilter}
                            trackedStructures={result?.tracked_structures}
                            sliceAxis="xz"
                            slicePosition={Math.min(gridSize, 50) / 2}
                            sliceThickness={sliceThickness}
                            showAllZ={showAllZ}
                            onStructureClick={handleStructureClick}
                          />
                          <FieldHeatmapWithOverlays 
                            data={currentSnapshot.rho_yz} 
                            title="ρ (YZ slice)" 
                            colorScheme="heat"
                            structures={currentFrameStructures || result?.structures}
                            gridSize={Math.min(gridSize, 50)}
                            showStrainNodes={showStrainNodes}
                            showClusters={showClusters}
                            showParticleNodes={showParticleNodes}
                            showVortices={showVortices}
                            trajectories={allTrajectories}
                            showTrajectories={showTrajectories}
                            selectedTrackedId={selectedTrackedId}
                            getStructureState={getStructureState}
                            eventFilter={eventFilter}
                            trackedStructures={result?.tracked_structures}
                            sliceAxis="yz"
                            slicePosition={Math.min(gridSize, 50) / 2}
                            sliceThickness={sliceThickness}
                            showAllZ={showAllZ}
                            onStructureClick={handleStructureClick}
                          />
                          <FieldHeatmapWithOverlays 
                            data={currentSnapshot.c_eff_xy} 
                            title="c_eff (XY)" 
                            colorScheme="blue"
                            structures={currentFrameStructures || result?.structures}
                            gridSize={Math.min(gridSize, 50)}
                            showStrainNodes={showStrainNodes}
                            showClusters={showClusters}
                            showParticleNodes={showParticleNodes}
                            showVortices={showVortices}
                            trajectories={allTrajectories}
                            showTrajectories={showTrajectories}
                            selectedTrackedId={selectedTrackedId}
                            getStructureState={getStructureState}
                            eventFilter={eventFilter}
                            trackedStructures={result?.tracked_structures}
                            sliceAxis="xy"
                            slicePosition={Math.min(gridSize, 50) / 2}
                            sliceThickness={sliceThickness}
                            showAllZ={showAllZ}
                            onStructureClick={handleStructureClick}
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
                      
                      {/* Tracking Information */}
                      {selectedTracked && (
                        <div className="mt-4 pt-4 border-t border-border/50">
                          <div className="text-xs font-mono uppercase text-muted-foreground mb-2 flex items-center gap-2">
                            <Activity className="w-3 h-3" />
                            Time Tracking ({selectedTracked.id})
                          </div>
                          <div className="grid grid-cols-2 md:grid-cols-5 gap-4 text-xs font-mono">
                            <div>
                              <span className="text-muted-foreground">Status:</span>
                              <div className="font-bold">
                                <Badge variant={selectedTracked.status === 'active' ? 'default' : 'secondary'}>
                                  {selectedTracked.status}
                                </Badge>
                              </div>
                            </div>
                            <div>
                              <span className="text-muted-foreground">Birth:</span>
                              <div className="font-bold">t = {selectedTracked.birth_time?.toFixed(2)}</div>
                            </div>
                            <div>
                              <span className="text-muted-foreground">Last Seen:</span>
                              <div className="font-bold">t = {selectedTracked.last_seen_time?.toFixed(2)}</div>
                            </div>
                            <div>
                              <span className="text-muted-foreground">Age:</span>
                              <div className="font-bold text-primary">{selectedTracked.age?.toFixed(2)}</div>
                            </div>
                            <div>
                              <span className="text-muted-foreground">Confidence:</span>
                              <div className="font-bold">
                                <Badge variant={
                                  selectedTracked.match_confidence === 'high' ? 'default' : 
                                  selectedTracked.match_confidence === 'medium' ? 'secondary' : 'outline'
                                }>
                                  {selectedTracked.match_confidence}
                                </Badge>
                              </div>
                            </div>
                          </div>
                          
                          {/* Trajectory summary */}
                          {selectedTracked.trajectory?.length > 1 && (
                            <div className="mt-3">
                              <span className="text-xs text-muted-foreground">
                                Trajectory: {selectedTracked.trajectory.length} points
                              </span>
                            </div>
                          )}
                          
                          {/* Stability history mini-chart (if available) */}
                          {selectedTracked.history?.length > 1 && (
                            <div className="mt-3">
                              <span className="text-xs text-muted-foreground">Stability History:</span>
                              <div className="flex items-end gap-px h-8 mt-1">
                                {selectedTracked.history.slice(-20).map((h, i) => (
                                  <div 
                                    key={i}
                                    className="flex-1 bg-primary/60 rounded-t-sm"
                                    style={{ height: `${(h.stability || 0) * 100}%` }}
                                    title={`t=${h.t?.toFixed(2)}: ${(h.stability * 100 || 0).toFixed(0)}%`}
                                  />
                                ))}
                              </div>
                            </div>
                          )}
                          
                          {/* Lineage Section (Merge/Split) */}
                          {selectedLineageInfo && (selectedLineageInfo.parents.length > 0 || selectedLineageInfo.children.length > 0) && (
                            <div className="mt-4 pt-4 border-t border-border/30">
                              <div className="text-xs font-mono uppercase text-muted-foreground mb-3 flex items-center gap-2">
                                <Sparkles className="w-3 h-3" />
                                Lineage
                                {selectedLineageInfo.eventType !== 'none' && (
                                  <Badge 
                                    variant="outline" 
                                    className={
                                      selectedLineageInfo.eventType === 'merge' || selectedLineageInfo.eventType === 'merge-parent'
                                        ? 'text-cyan-400 border-cyan-400/50'
                                        : selectedLineageInfo.eventType === 'split' || selectedLineageInfo.eventType === 'split-child'
                                        ? 'text-orange-400 border-orange-400/50'
                                        : ''
                                    }
                                  >
                                    {selectedLineageInfo.eventType === 'merge' && 'Merged'}
                                    {selectedLineageInfo.eventType === 'merge-parent' && 'Merged Into'}
                                    {selectedLineageInfo.eventType === 'split' && 'Split'}
                                    {selectedLineageInfo.eventType === 'split-child' && 'Split From'}
                                  </Badge>
                                )}
                                {selectedLineageInfo.eventTime != null && (
                                  <span className="text-muted-foreground ml-2">
                                    @ t = {selectedLineageInfo.eventTime.toFixed(2)}
                                  </span>
                                )}
                              </div>
                              
                              <div className="space-y-3">
                                {/* Parents */}
                                {selectedLineageInfo.parents.length > 0 && (
                                  <div>
                                    <span className="text-xs text-muted-foreground block mb-1">Parents:</span>
                                    <div className="space-y-1">
                                      {selectedLineageInfo.parents.map(parent => (
                                        <button
                                          key={parent.id}
                                          onClick={() => navigateToStructure(parent.id, true)}
                                          className="flex items-center gap-2 text-xs font-mono px-2 py-1 rounded bg-cyan-500/10 hover:bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 transition-colors w-full text-left"
                                          data-testid={`lineage-parent-${parent.id}`}
                                        >
                                          <Target className="w-3 h-3" />
                                          <span className="font-bold">{parent.id}</span>
                                          <span className="text-muted-foreground">
                                            (t = {parent.birthTime?.toFixed(2) ?? '?'} → {parent.lastSeenTime?.toFixed(2) ?? '?'})
                                          </span>
                                          {parent.status && parent.status !== 'unknown' && (
                                            <Badge variant="outline" className="ml-auto text-[10px] py-0">
                                              {parent.status}
                                            </Badge>
                                          )}
                                        </button>
                                      ))}
                                    </div>
                                  </div>
                                )}
                                
                                {/* Children */}
                                {selectedLineageInfo.children.length > 0 && (
                                  <div>
                                    <span className="text-xs text-muted-foreground block mb-1">Children:</span>
                                    <div className="space-y-1">
                                      {selectedLineageInfo.children.map(child => (
                                        <button
                                          key={child.id}
                                          onClick={() => navigateToStructure(child.id, true)}
                                          className="flex items-center gap-2 text-xs font-mono px-2 py-1 rounded bg-orange-500/10 hover:bg-orange-500/20 text-orange-300 border border-orange-500/30 transition-colors w-full text-left"
                                          data-testid={`lineage-child-${child.id}`}
                                        >
                                          <CircleDot className="w-3 h-3" />
                                          <span className="font-bold">{child.id}</span>
                                          <span className="text-muted-foreground">
                                            (t = {child.birthTime?.toFixed(2) ?? '?'} → {child.lastSeenTime?.toFixed(2) ?? '?'})
                                          </span>
                                          {child.status && child.status !== 'unknown' && (
                                            <Badge variant="outline" className="ml-auto text-[10px] py-0">
                                              {child.status}
                                            </Badge>
                                          )}
                                        </button>
                                      ))}
                                    </div>
                                  </div>
                                )}
                              </div>
                            </div>
                          )}
                        </div>
                      )}
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
