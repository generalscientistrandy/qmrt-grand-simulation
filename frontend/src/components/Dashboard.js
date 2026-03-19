import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Plus, RefreshCw, Loader2, Atom } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { WorldCard } from '@/components/WorldCard';
import { CreateWorldModal } from '@/components/CreateWorldModal';
import { WorldDetailModal } from '@/components/WorldDetailModal';
import { SubstrateInfoModal } from '@/components/SubstrateInfoModal';
import { MesoscopicVisualizer } from '@/components/MesoscopicVisualizer';
import axios from 'axios';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export const Dashboard = () => {
  const [worlds, setWorlds] = useState([]);
  const [loading, setLoading] = useState(true);
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [selectedWorld, setSelectedWorld] = useState(null);
  const [infoModalOpen, setInfoModalOpen] = useState(false);
  const [visualizerOpen, setVisualizerOpen] = useState(false);

  const fetchWorlds = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/worlds`);
      setWorlds(response.data.worlds);
    } catch (error) {
      console.error('Error fetching worlds:', error);
      toast.error('Failed to load worlds');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchWorlds();
  }, []);

  const handleWorldCreated = (newWorld) => {
    setWorlds([newWorld, ...worlds]);
  };

  const handleWorldDeleted = (worldId) => {
    setWorlds(worlds.filter(w => w.id !== worldId));
    setSelectedWorld(null);
  };

  return (
    <div className="space-y-8">
      {/* Header Section */}
      <motion.div 
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="space-y-4"
      >
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <h2 className="text-4xl md:text-5xl font-bold tracking-tight uppercase" style={{ fontFamily: 'Rajdhani, sans-serif' }}>
              Universe Catalog
            </h2>
            <p className="text-sm text-muted-foreground mt-2">
              Persistent worlds generated from QMRT substrate physics
            </p>
          </div>
          
          <div className="flex items-center gap-3">
            <Button
              data-testid="visualizer-button"
              onClick={() => setVisualizerOpen(true)}
              variant="outline"
              className="bg-primary/20 text-primary hover:bg-primary/30 border border-primary/50 rounded-sm font-mono uppercase text-sm h-10 px-4"
            >
              <Atom className="w-4 h-4 mr-2" />
              Substrate Lab
            </Button>
            <Button
              data-testid="substrate-info-button"
              onClick={() => setInfoModalOpen(true)}
              variant="outline"
              className="bg-secondary/20 text-secondary-foreground hover:bg-secondary/30 border border-secondary/50 rounded-sm font-mono uppercase text-sm h-10 px-4"
            >
              Substrate Info
            </Button>
            <Button
              data-testid="refresh-button"
              onClick={fetchWorlds}
              variant="outline"
              className="bg-muted/20 hover:bg-muted/30 border-border rounded-sm font-mono uppercase text-sm h-10 px-4"
              disabled={loading}
            >
              <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
            <Button
              data-testid="create-world-button"
              onClick={() => setCreateModalOpen(true)}
              className="bg-primary text-primary-foreground hover:bg-primary/90 rounded-sm font-mono uppercase tracking-wider text-sm h-10 px-6 glow-primary"
            >
              <Plus className="w-4 h-4 mr-2" />
              New World
            </Button>
          </div>
        </div>

        {/* Stats Bar */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="p-4 rounded-sm bg-card/40 backdrop-blur-md border border-border/50">
            <p className="text-xs font-mono uppercase tracking-widest text-muted-foreground mb-1">Total Worlds</p>
            <p className="text-3xl font-mono font-bold text-primary" data-testid="total-worlds">{worlds.length}</p>
          </div>
          <div className="p-4 rounded-sm bg-card/40 backdrop-blur-md border border-border/50">
            <p className="text-xs font-mono uppercase tracking-widest text-muted-foreground mb-1">Apex Qualified</p>
            <p className="text-3xl font-mono font-bold text-secondary">
              {worlds.filter(w => w.apex_qualified).length}
            </p>
          </div>
          <div className="p-4 rounded-sm bg-card/40 backdrop-blur-md border border-border/50">
            <p className="text-xs font-mono uppercase tracking-widest text-muted-foreground mb-1">Avg Death Level</p>
            <p className="text-3xl font-mono font-bold">
              {worlds.length > 0 ? (worlds.reduce((acc, w) => acc + w.death_world_level, 0) / worlds.length).toFixed(1) : '0.0'}
            </p>
          </div>
          <div className="p-4 rounded-sm bg-card/40 backdrop-blur-md border border-border/50">
            <p className="text-xs font-mono uppercase tracking-widest text-muted-foreground mb-1">Phase Status</p>
            <p className="text-sm font-mono font-bold text-green-500">A: Active</p>
          </div>
        </div>
      </motion.div>

      {/* Worlds Grid */}
      {loading ? (
        <div className="flex items-center justify-center py-16" data-testid="loading-indicator">
          <Loader2 className="w-8 h-8 animate-spin text-primary" />
        </div>
      ) : worlds.length === 0 ? (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="text-center py-16 space-y-4"
          data-testid="empty-state"
        >
          <div className="w-16 h-16 mx-auto bg-muted/20 border border-border rounded-sm flex items-center justify-center">
            <Plus className="w-8 h-8 text-muted-foreground" />
          </div>
          <div>
            <h3 className="text-xl font-semibold mb-2">No Worlds Generated</h3>
            <p className="text-sm text-muted-foreground mb-4">
              Initialize your first world from QMRT substrate physics
            </p>
            <Button
              data-testid="empty-create-button"
              onClick={() => setCreateModalOpen(true)}
              className="bg-primary text-primary-foreground hover:bg-primary/90 rounded-sm font-mono uppercase tracking-wider text-sm h-10 px-6"
            >
              <Plus className="w-4 h-4 mr-2" />
              Create First World
            </Button>
          </div>
        </motion.div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6" data-testid="worlds-grid">
          {worlds.map((world, index) => (
            <motion.div
              key={world.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.05 }}
            >
              <WorldCard 
                world={world} 
                onClick={() => setSelectedWorld(world)}
              />
            </motion.div>
          ))}
        </div>
      )}

      {/* Modals */}
      <CreateWorldModal
        open={createModalOpen}
        onClose={() => setCreateModalOpen(false)}
        onWorldCreated={handleWorldCreated}
      />

      {selectedWorld && (
        <WorldDetailModal
          world={selectedWorld}
          open={!!selectedWorld}
          onClose={() => setSelectedWorld(null)}
          onWorldDeleted={handleWorldDeleted}
        />
      )}

      <SubstrateInfoModal
        open={infoModalOpen}
        onClose={() => setInfoModalOpen(false)}
      />

      <MesoscopicVisualizer
        open={visualizerOpen}
        onClose={() => setVisualizerOpen(false)}
      />
    </div>
  );
};
