import React from 'react';
import { motion } from 'framer-motion';
import { Globe, TrendingUp, AlertTriangle, Sparkles } from 'lucide-react';

const getClassificationColor = (classification) => {
  if (classification.includes('Sanctuary')) return 'text-green-500 border-green-500/50';
  if (classification.includes('Garden') || classification.includes('Earth')) return 'text-blue-500 border-blue-500/50';
  if (classification.includes('Frontier') || classification.includes('Contested')) return 'text-amber-500 border-amber-500/50';
  if (classification.includes('Harsh') || classification.includes('Death')) return 'text-red-500 border-red-500/50';
  if (classification.includes('Apocalypse')) return 'text-purple-500 border-purple-500/50';
  return 'text-muted-foreground border-border';
};

const getDifficultyColor = (difficulty) => {
  if (difficulty < 3) return 'text-green-500';
  if (difficulty < 5) return 'text-blue-500';
  if (difficulty < 7) return 'text-amber-500';
  if (difficulty < 9) return 'text-red-500';
  return 'text-purple-500';
};

export const WorldCard = ({ world, onClick }) => {
  const params = world.world_parameters;
  const classColor = getClassificationColor(world.classification);
  const diffColor = getDifficultyColor(params.survival_difficulty);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ scale: 1.02 }}
      transition={{ duration: 0.2 }}
      onClick={onClick}
      data-testid={`world-card-${world.id}`}
      className="bg-card/40 backdrop-blur-md border border-border/50 rounded-lg overflow-hidden hover:border-primary/50 transition-colors duration-300 cursor-pointer group"
    >
      {/* Header */}
      <div className="border-b border-border/50 p-4 bg-muted/20">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <h3 className="font-semibold text-lg tracking-tight mb-1">{world.name}</h3>
            <div className="flex items-center gap-2">
              <span className={`text-[10px] font-mono uppercase tracking-widest px-2 py-0.5 rounded-full border ${classColor}`}>
                {world.classification}
              </span>
            </div>
          </div>
          {world.apex_qualified && (
            <Sparkles className="w-4 h-4 text-primary" data-testid="apex-badge" />
          )}
        </div>
      </div>

      {/* Content */}
      <div className="p-4 space-y-4">
        {/* Death World Level */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono uppercase tracking-widest text-muted-foreground">Death World Level</span>
            <span className="text-2xl font-mono font-bold text-primary">{world.death_world_level}</span>
          </div>
          <div className="h-1.5 bg-muted/50 rounded-full overflow-hidden">
            <div 
              className="h-full bg-primary rounded-full glow-primary"
              style={{ width: `${(world.death_world_level / 15) * 100}%` }}
            />
          </div>
        </div>

        {/* Key Metrics Grid */}
        <div className="grid grid-cols-2 gap-3">
          <div className="space-y-1">
            <div className="flex items-center gap-1.5">
              <Globe className="w-3 h-3 text-muted-foreground" />
              <span className="text-[10px] font-mono uppercase tracking-widest text-muted-foreground">Bio Viability</span>
            </div>
            <p className="text-lg font-mono font-bold">{(params.biological_viability * 100).toFixed(0)}%</p>
          </div>
          
          <div className="space-y-1">
            <div className="flex items-center gap-1.5">
              <AlertTriangle className="w-3 h-3 text-muted-foreground" />
              <span className="text-[10px] font-mono uppercase tracking-widest text-muted-foreground">Survival</span>
            </div>
            <p className={`text-lg font-mono font-bold ${diffColor}`}>
              {params.survival_difficulty.toFixed(1)}/10
            </p>
          </div>
          
          <div className="space-y-1">
            <span className="text-[10px] font-mono uppercase tracking-widest text-muted-foreground">Gravity</span>
            <p className="text-lg font-mono font-bold">{params.gravity.toFixed(2)}G</p>
          </div>
          
          <div className="space-y-1">
            <span className="text-[10px] font-mono uppercase tracking-widest text-muted-foreground">Resources</span>
            <p className="text-lg font-mono font-bold">{(params.resource_density * 100).toFixed(0)}%</p>
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="px-4 py-3 border-t border-border/50 bg-muted/10">
        <p className="text-[10px] font-mono text-muted-foreground">
          ID: {world.id.slice(0, 8).toUpperCase()}
        </p>
      </div>
    </motion.div>
  );
};
