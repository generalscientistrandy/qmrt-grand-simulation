import React, { useState } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Slider } from '@/components/ui/slider';
import { motion } from 'framer-motion';
import { Loader2, Sparkles } from 'lucide-react';
import { toast } from 'sonner';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const getLevelDescription = (level) => {
  if (level <= 3) return 'Sanctuary World - Low difficulty, stable environment';
  if (level <= 6) return 'Garden/Frontier World - Moderate challenges';
  if (level <= 9) return 'Contested/Harsh World - Significant dangers';
  if (level === 10) return 'Earth-Class World - Balanced reference standard';
  if (level <= 12) return 'Death World - Extreme survival conditions';
  if (level <= 14) return 'Extreme Death World - Apocalyptic environment';
  return 'Apocalypse World - Maximum chaos and danger';
};

export const CreateWorldModal = ({ open, onClose, onWorldCreated }) => {
  const [name, setName] = useState('');
  const [deathWorldLevel, setDeathWorldLevel] = useState(10);
  const [seed, setSeed] = useState('');
  const [creating, setCreating] = useState(false);

  const handleCreate = async () => {
    if (!name.trim()) {
      toast.error('Please enter a world name');
      return;
    }

    setCreating(true);
    try {
      const response = await axios.post(`${API}/worlds`, {
        name: name.trim(),
        death_world_level: deathWorldLevel,
        seed: seed ? parseInt(seed) : null,
        evolution_steps: 200
      });

      toast.success(`World "${name}" generated successfully!`);
      onWorldCreated(response.data);
      
      // Reset form
      setName('');
      setDeathWorldLevel(10);
      setSeed('');
      onClose();
    } catch (error) {
      console.error('Error creating world:', error);
      toast.error(error.response?.data?.detail || 'Failed to generate world');
    } finally {
      setCreating(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[600px] bg-card/95 backdrop-blur-xl border-border/50" data-testid="create-world-modal">
        <DialogHeader>
          <DialogTitle className="text-2xl font-bold tracking-tight uppercase" style={{ fontFamily: 'Rajdhani, sans-serif' }}>
            Initialize New World
          </DialogTitle>
          <DialogDescription className="font-mono text-xs text-muted-foreground">
            Configure substrate parameters to generate a persistent world. Set death-world level (1-15) and optional seed for reproducibility.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6 py-4">
          {/* Name Input */}
          <div className="space-y-2">
            <Label htmlFor="world-name" className="text-xs font-mono uppercase tracking-widest text-muted-foreground">
              World Designation
            </Label>
            <Input
              id="world-name"
              data-testid="world-name-input"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Enter world name..."
              className="bg-background/50 border-border focus:border-primary focus:ring-1 focus:ring-primary/50 rounded-sm font-mono h-10"
            />
          </div>

          {/* Death World Level Slider */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <Label className="text-xs font-mono uppercase tracking-widest text-muted-foreground">
                Death World Level
              </Label>
              <span className="text-3xl font-mono font-bold text-primary" data-testid="death-level-display">
                {deathWorldLevel}
              </span>
            </div>
            
            <Slider
              data-testid="death-level-slider"
              value={[deathWorldLevel]}
              onValueChange={(value) => setDeathWorldLevel(value[0])}
              min={1}
              max={15}
              step={1}
              className="py-4"
            />

            <div className="flex justify-between text-[10px] font-mono text-muted-foreground">
              <span>1 - Sanctuary</span>
              <span className="text-primary">10 - Earth</span>
              <span>15 - Apocalypse</span>
            </div>

            <motion.div
              key={deathWorldLevel}
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              className="p-4 rounded-sm bg-muted/20 border border-border/50"
            >
              <p className="text-sm text-muted-foreground">{getLevelDescription(deathWorldLevel)}</p>
              {deathWorldLevel >= 10 && (
                <div className="flex items-center gap-2 mt-2 text-xs text-primary">
                  <Sparkles className="w-3 h-3" />
                  <span className="font-mono">Apex qualification enabled</span>
                </div>
              )}
            </motion.div>
          </div>

          {/* Optional Seed */}
          <div className="space-y-2">
            <Label htmlFor="seed" className="text-xs font-mono uppercase tracking-widest text-muted-foreground">
              Seed (Optional)
            </Label>
            <Input
              id="seed"
              data-testid="seed-input"
              type="number"
              value={seed}
              onChange={(e) => setSeed(e.target.value)}
              placeholder="Random seed for reproducibility..."
              className="bg-background/50 border-border focus:border-primary focus:ring-1 focus:ring-primary/50 rounded-sm font-mono h-10"
            />
          </div>
        </div>

        <div className="flex gap-3">
          <Button
            data-testid="cancel-button"
            onClick={onClose}
            variant="outline"
            className="flex-1 bg-secondary/20 text-secondary-foreground hover:bg-secondary/30 border border-secondary/50 rounded-sm font-mono uppercase text-sm h-10"
            disabled={creating}
          >
            Cancel
          </Button>
          <Button
            data-testid="generate-button"
            onClick={handleCreate}
            disabled={creating}
            className="flex-1 bg-primary text-primary-foreground hover:bg-primary/90 rounded-sm font-mono uppercase tracking-wider text-sm h-10 glow-primary"
          >
            {creating ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Generating...
              </>
            ) : (
              'Generate World'
            )}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
};
