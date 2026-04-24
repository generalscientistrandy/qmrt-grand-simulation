"""
Paper 5 Figure Generation
=========================

Generates publication-quality figures for Paper 5:
Population Ecology of Topological Defects

Figures:
1. Regional ecology panel (density, turnover, spacing)
2. Long-time population trace with bursts
3. NESS stationarity (windowed mean/variance)
4. Carrying capacity (saturation and spillover)
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.ndimage import gaussian_filter, label
import time

# Set publication style
plt.rcParams.update({
    'font.size': 11,
    'axes.labelsize': 12,
    'axes.titlesize': 12,
    'xtick.labelsize': 10,
    'ytick.labelsize': 10,
    'legend.fontsize': 10,
    'figure.dpi': 150,
    'savefig.dpi': 300,
    'savefig.bbox': 'tight',
})


class EcologySimulator:
    """Simplified simulator for figure generation."""
    
    def __init__(self, size=48, coupling_center=0.7, coupling_edge=0.2):
        self.size = size
        self.coupling_center = coupling_center
        self.coupling_edge = coupling_edge
        
        self.psi_r = np.ones((size, size, size)) * 1.2
        self.psi_i = np.zeros((size, size, size))
        self.psi_r_dot = np.zeros((size, size, size))
        self.psi_i_dot = np.zeros((size, size, size))
        self.channel_assignment = np.zeros((size, size, size))
        
        self.coupling = self._create_coupling()
        
    def _create_coupling(self):
        x, y, z = np.meshgrid(np.arange(self.size), np.arange(self.size), 
                              np.arange(self.size), indexing='ij')
        center = self.size / 2
        r = np.sqrt((x-center)**2 + (y-center)**2 + (z-center)**2)
        interior_r = self.size * 0.25
        return np.where(r <= interior_r, self.coupling_center, self.coupling_edge)
    
    def get_region(self, x, y, z):
        center = self.size / 2
        r = np.sqrt((x-center)**2 + (y-center)**2 + (z-center)**2)
        if r <= self.size * 0.25:
            return 'interior'
        elif r <= self.size * 0.25 + 8:
            return 'transition'
        return 'periphery'
    
    def step(self, dt=0.04, gamma=0.007):
        def lap(f):
            return (np.roll(f,1,0) + np.roll(f,-1,0) + 
                    np.roll(f,1,1) + np.roll(f,-1,1) +
                    np.roll(f,1,2) + np.roll(f,-1,2) - 6*f)
        
        c_eff = 2.0
        lap_r = lap(self.psi_r)
        lap_i = lap(self.psi_i)
        
        acc_r = c_eff**2 * lap_r - gamma * self.psi_r_dot
        acc_i = c_eff**2 * lap_i - gamma * self.psi_i_dot
        
        amp = np.sqrt(self.psi_r**2 + self.psi_i**2) + 1e-10
        phase = np.arctan2(self.psi_i, self.psi_r)
        
        grad_x = np.angle(np.exp(1j * (np.roll(phase, -1, axis=0) - phase)))
        grad_y = np.angle(np.exp(1j * (np.roll(phase, -1, axis=1) - phase)))
        grad_z = np.angle(np.exp(1j * (np.roll(phase, -1, axis=2) - phase)))
        topology = np.sqrt(grad_x**2 + grad_y**2 + grad_z**2)
        topology = gaussian_filter(topology, sigma=1.5)
        topology_norm = topology / (np.max(topology) + 1e-10)
        
        self.channel_assignment += 0.01 * (topology_norm - self.channel_assignment)
        self.channel_assignment = np.clip(self.channel_assignment, 0, 1)
        
        protection = topology_norm * self.channel_assignment
        radial_r = self.psi_r / amp
        radial_i = self.psi_i / amp
        acc_radial = acc_r * radial_r + acc_i * radial_i
        
        suppression = self.coupling * protection * np.maximum(acc_radial, 0)
        acc_r -= suppression * radial_r
        acc_i -= suppression * radial_i
        
        self.psi_r_dot += acc_r * dt
        self.psi_i_dot += acc_i * dt
        self.psi_r += self.psi_r_dot * dt
        self.psi_i += self.psi_i_dot * dt
    
    def detect_defects(self, threshold=0.4):
        amp = np.sqrt(self.psi_r**2 + self.psi_i**2)
        low_amp = amp < threshold
        labeled, n = label(low_amp)
        
        defects = []
        for i in range(1, n+1):
            component = (labeled == i)
            if np.sum(component) < 5:
                continue
            coords = np.where(component)
            cx = int(np.mean(coords[0]))
            cy = int(np.mean(coords[1]))
            cz = int(np.mean(coords[2]))
            defects.append((cx, cy, cz))
        return defects
    
    def inject_vortex(self, cx, cy, charge=1):
        x, y, z = np.meshgrid(np.arange(self.size), np.arange(self.size), 
                              np.arange(self.size), indexing='ij')
        r = np.sqrt((x-cx)**2 + (y-cy)**2) + 0.1
        theta = np.arctan2(y-cy, x-cx)
        vortex = np.tanh(r/3) * np.exp(1j * charge * theta)
        current = self.psi_r + 1j * self.psi_i
        combined = current * vortex / (np.abs(current) + 0.01)
        self.psi_r = np.real(combined)
        self.psi_i = np.imag(combined)


def collect_regional_data(steps=2000):
    """Collect data for regional ecology figure."""
    print("Collecting regional ecology data...")
    
    sim = EcologySimulator(size=48)
    np.random.seed(42)
    sim.psi_r += 0.04 * np.random.randn(sim.size, sim.size, sim.size)
    sim.psi_i += 0.04 * np.random.randn(sim.size, sim.size, sim.size)
    
    interior_counts = []
    transition_counts = []
    periphery_counts = []
    
    interior_nn = []
    periphery_nn = []
    
    prev_int = set()
    prev_per = set()
    interior_births = []
    interior_deaths = []
    periphery_births = []
    periphery_deaths = []
    
    for step in range(steps):
        sim.step()
        if step % 25 == 0:
            defects = sim.detect_defects()
            
            int_def = [d for d in defects if sim.get_region(*d) == 'interior']
            trans_def = [d for d in defects if sim.get_region(*d) == 'transition']
            per_def = [d for d in defects if sim.get_region(*d) == 'periphery']
            
            interior_counts.append(len(int_def))
            transition_counts.append(len(trans_def))
            periphery_counts.append(len(per_def))
            
            # NN spacing
            if len(int_def) >= 2:
                positions = np.array(int_def)
                nn_dists = []
                for i, pos in enumerate(positions):
                    dists = np.sqrt(np.sum((positions - pos)**2, axis=1))
                    dists[i] = np.inf
                    nn_dists.append(np.min(dists))
                interior_nn.append(np.mean(nn_dists))
            
            if len(per_def) >= 2:
                positions = np.array(per_def)
                nn_dists = []
                for i, pos in enumerate(positions):
                    dists = np.sqrt(np.sum((positions - pos)**2, axis=1))
                    dists[i] = np.inf
                    nn_dists.append(np.min(dists))
                periphery_nn.append(np.mean(nn_dists))
            
            # Track events
            curr_int = set(int_def)
            curr_per = set(per_def)
            interior_births.append(len(curr_int - prev_int))
            interior_deaths.append(len(prev_int - curr_int))
            periphery_births.append(len(curr_per - prev_per))
            periphery_deaths.append(len(prev_per - curr_per))
            prev_int = curr_int
            prev_per = curr_per
            
            if step % 500 == 0:
                print(f"  Step {step}")
    
    return {
        'interior_counts': interior_counts,
        'transition_counts': transition_counts,
        'periphery_counts': periphery_counts,
        'interior_nn': interior_nn,
        'periphery_nn': periphery_nn,
        'interior_births': interior_births,
        'interior_deaths': interior_deaths,
        'periphery_births': periphery_births,
        'periphery_deaths': periphery_deaths,
    }


def collect_longtime_data(steps=4000):
    """Collect data for long-time population trace."""
    print("Collecting long-time data...")
    
    sim = EcologySimulator(size=48)
    np.random.seed(42)
    sim.psi_r += 0.04 * np.random.randn(sim.size, sim.size, sim.size)
    sim.psi_i += 0.04 * np.random.randn(sim.size, sim.size, sim.size)
    
    times = []
    counts = []
    
    for step in range(steps):
        sim.step()
        if step % 20 == 0:
            defects = sim.detect_defects()
            times.append(step)
            counts.append(len(defects))
            
            if step % 1000 == 0:
                print(f"  Step {step}")
    
    return {'times': times, 'counts': counts}


def collect_capacity_data(steps=1500):
    """Collect data for carrying capacity figure."""
    print("Collecting carrying capacity data...")
    
    results = {}
    
    # Natural
    print("  Natural condition...")
    sim1 = EcologySimulator(size=48)
    np.random.seed(42)
    sim1.psi_r += 0.04 * np.random.randn(sim1.size, sim1.size, sim1.size)
    sim1.psi_i += 0.04 * np.random.randn(sim1.size, sim1.size, sim1.size)
    
    natural_int = []
    natural_per = []
    for step in range(steps):
        sim1.step()
        if step % 25 == 0:
            defects = sim1.detect_defects()
            natural_int.append(sum(1 for d in defects if sim1.get_region(*d) == 'interior'))
            natural_per.append(sum(1 for d in defects if sim1.get_region(*d) == 'periphery'))
    results['natural'] = {'interior': natural_int, 'periphery': natural_per}
    
    # Forced interior
    print("  Forced interior...")
    sim2 = EcologySimulator(size=48)
    np.random.seed(42)
    sim2.psi_r += 0.04 * np.random.randn(sim2.size, sim2.size, sim2.size)
    sim2.psi_i += 0.04 * np.random.randn(sim2.size, sim2.size, sim2.size)
    
    center = sim2.size // 2
    for offset in [(-6,-6), (-6,6), (6,-6), (6,6), (0,0), (-4,0), (4,0), (0,-4), (0,4)]:
        sim2.inject_vortex(center + offset[0], center + offset[1])
    
    forced_int = []
    forced_per = []
    for step in range(steps):
        sim2.step()
        if step % 25 == 0:
            defects = sim2.detect_defects()
            forced_int.append(sum(1 for d in defects if sim2.get_region(*d) == 'interior'))
            forced_per.append(sum(1 for d in defects if sim2.get_region(*d) == 'periphery'))
    results['forced'] = {'interior': forced_int, 'periphery': forced_per}
    
    return results


def generate_figure_1(data, output_path):
    """Figure 1: Regional ecology panel."""
    print("Generating Figure 1...")
    
    fig, axes = plt.subplots(1, 3, figsize=(12, 4))
    
    # Panel A: Density by region
    ax = axes[0]
    
    # Calculate densities
    size = 48
    interior_vol = (4/3) * np.pi * (size * 0.25)**3
    periphery_vol = size**3 - (4/3) * np.pi * (size * 0.25 + 8)**3
    
    late = slice(-20, None)
    int_density = np.mean(data['interior_counts'][late]) / interior_vol * 1e4
    per_density = np.mean(data['periphery_counts'][late]) / periphery_vol * 1e4
    
    bars = ax.bar(['Interior\n(high κ)', 'Periphery\n(low κ)'], 
                  [int_density, per_density],
                  color=['#2E86AB', '#A23B72'], alpha=0.8, edgecolor='black')
    ax.set_ylabel('Density (×10⁻⁴ per voxel)')
    ax.set_title('A. Population Density')
    
    # Add ratio annotation
    ratio = int_density / (per_density + 1e-10)
    ax.annotate(f'{ratio:.1f}×', xy=(0.5, max(int_density, per_density) * 0.8),
                ha='center', fontsize=11, fontweight='bold')
    
    # Panel B: Turnover by region
    ax = axes[1]
    
    int_turnover = (np.mean(data['interior_births'][late]) + np.mean(data['interior_deaths'][late])) / (np.mean(data['interior_counts'][late]) + 0.01)
    per_turnover = (np.mean(data['periphery_births'][late]) + np.mean(data['periphery_deaths'][late])) / (np.mean(data['periphery_counts'][late]) + 0.01)
    
    bars = ax.bar(['Interior\n(high κ)', 'Periphery\n(low κ)'], 
                  [int_turnover, per_turnover],
                  color=['#2E86AB', '#A23B72'], alpha=0.8, edgecolor='black')
    ax.set_ylabel('Turnover (events/defect/interval)')
    ax.set_title('B. Population Turnover')
    
    ratio = per_turnover / (int_turnover + 0.01)
    ax.annotate(f'{ratio:.1f}×', xy=(0.5, max(int_turnover, per_turnover) * 0.8),
                ha='center', fontsize=11, fontweight='bold')
    
    # Panel C: NN spacing
    ax = axes[2]
    
    int_nn = np.mean(data['interior_nn']) if data['interior_nn'] else 0
    per_nn = np.mean(data['periphery_nn']) if data['periphery_nn'] else 0
    
    bars = ax.bar(['Interior\n(high κ)', 'Periphery\n(low κ)'], 
                  [int_nn, per_nn],
                  color=['#2E86AB', '#A23B72'], alpha=0.8, edgecolor='black')
    ax.set_ylabel('NN Spacing (grid units)')
    ax.set_title('C. Nearest-Neighbor Spacing')
    
    ratio = per_nn / (int_nn + 0.01)
    ax.annotate(f'{ratio:.1f}×', xy=(0.5, max(int_nn, per_nn) * 0.8),
                ha='center', fontsize=11, fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()
    print(f"  Saved: {output_path}")


def generate_figure_2(data, output_path):
    """Figure 2: Long-time population trace."""
    print("Generating Figure 2...")
    
    fig, ax = plt.subplots(figsize=(10, 4))
    
    times = np.array(data['times'])
    counts = np.array(data['counts'])
    
    # Population trace
    ax.fill_between(times, 0, counts, alpha=0.3, color='#2E86AB')
    ax.plot(times, counts, color='#2E86AB', linewidth=1, label='Population')
    
    # Late-time mean
    late_mean = np.mean(counts[-len(counts)//4:])
    ax.axhline(late_mean, color='#E63946', linestyle='--', linewidth=2, 
               label=f'Late-time mean: {late_mean:.1f}')
    
    # Mark burst regions (population > 2× mean)
    burst_mask = counts > 2 * late_mean
    if np.any(burst_mask):
        burst_times = times[burst_mask]
        burst_counts = counts[burst_mask]
        ax.scatter(burst_times, burst_counts, color='#F4A261', s=30, 
                   zorder=5, label='Episodic bursts')
    
    ax.set_xlabel('Simulation Step')
    ax.set_ylabel('Total Defect Count')
    ax.set_title('Long-Time Population Dynamics')
    ax.legend(loc='upper right')
    ax.set_xlim(0, max(times))
    ax.set_ylim(0, None)
    
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()
    print(f"  Saved: {output_path}")


def generate_figure_3(data, output_path):
    """Figure 3: NESS stationarity (windowed statistics)."""
    print("Generating Figure 3...")
    
    counts = np.array(data['counts'])
    times = np.array(data['times'])
    
    # Compute windowed mean and std
    window_size = len(counts) // 8
    windowed_means = []
    windowed_stds = []
    window_centers = []
    
    for i in range(0, len(counts) - window_size, window_size // 2):
        window = counts[i:i + window_size]
        windowed_means.append(np.mean(window))
        windowed_stds.append(np.std(window))
        window_centers.append(times[i + window_size // 2])
    
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    
    # Panel A: Windowed mean
    ax = axes[0]
    ax.plot(window_centers, windowed_means, 'o-', color='#2E86AB', 
            markersize=8, linewidth=2)
    ax.axhline(np.mean(counts), color='#E63946', linestyle='--', 
               label=f'Overall mean: {np.mean(counts):.1f}')
    ax.fill_between(window_centers, 
                    np.mean(counts) - np.std(counts),
                    np.mean(counts) + np.std(counts),
                    alpha=0.2, color='#E63946')
    ax.set_xlabel('Simulation Step')
    ax.set_ylabel('Windowed Mean')
    ax.set_title('A. Mean Population (Stationarity)')
    ax.legend()
    
    # Panel B: Windowed variance
    ax = axes[1]
    ax.plot(window_centers, np.array(windowed_stds)**2, 'o-', color='#A23B72',
            markersize=8, linewidth=2)
    ax.set_xlabel('Simulation Step')
    ax.set_ylabel('Windowed Variance')
    ax.set_title('B. Population Variance')
    
    # Add autocorrelation inset
    if len(counts) > 10:
        autocorr = []
        for lag in range(1, min(20, len(counts) // 2)):
            c = np.corrcoef(counts[:-lag], counts[lag:])[0, 1]
            autocorr.append(c)
        
        # Inset
        inset = ax.inset_axes([0.55, 0.55, 0.4, 0.4])
        inset.bar(range(1, len(autocorr) + 1), autocorr, color='#A23B72', alpha=0.7)
        inset.axhline(0, color='black', linewidth=0.5)
        inset.set_xlabel('Lag', fontsize=8)
        inset.set_ylabel('Autocorr', fontsize=8)
        inset.set_title('Autocorrelation', fontsize=9)
        inset.tick_params(labelsize=7)
    
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()
    print(f"  Saved: {output_path}")


def generate_figure_4(data, output_path):
    """Figure 4: Carrying capacity."""
    print("Generating Figure 4...")
    
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    
    # Panel A: Time evolution
    ax = axes[0]
    
    times = np.arange(len(data['natural']['interior'])) * 25
    
    ax.plot(times, data['natural']['interior'], color='#2E86AB', 
            linewidth=2, label='Natural - Interior')
    ax.plot(times, data['forced']['interior'], color='#2E86AB', 
            linewidth=2, linestyle='--', label='Forced - Interior')
    ax.plot(times, data['natural']['periphery'], color='#A23B72', 
            linewidth=2, alpha=0.7, label='Natural - Periphery')
    ax.plot(times, data['forced']['periphery'], color='#A23B72', 
            linewidth=2, linestyle='--', alpha=0.7, label='Forced - Periphery')
    
    ax.set_xlabel('Simulation Step')
    ax.set_ylabel('Defect Count')
    ax.set_title('A. Population Response to Injection')
    ax.legend(fontsize=9)
    
    # Panel B: Late-time comparison
    ax = axes[1]
    
    late = slice(-20, None)
    natural_int = np.mean(data['natural']['interior'][late])
    forced_int = np.mean(data['forced']['interior'][late])
    natural_per = np.mean(data['natural']['periphery'][late])
    forced_per = np.mean(data['forced']['periphery'][late])
    
    x = np.arange(2)
    width = 0.35
    
    bars1 = ax.bar(x - width/2, [natural_int, natural_per], width, 
                   label='Natural', color=['#2E86AB', '#A23B72'], alpha=0.6)
    bars2 = ax.bar(x + width/2, [forced_int, forced_per], width,
                   label='Forced (9 injected)', color=['#2E86AB', '#A23B72'], 
                   alpha=1.0, edgecolor='black', linewidth=2)
    
    ax.set_ylabel('Late-Time Mean Defects')
    ax.set_title('B. Carrying Capacity Evidence')
    ax.set_xticks(x)
    ax.set_xticklabels(['Interior\n(high κ)', 'Periphery\n(low κ)'])
    ax.legend()
    
    # Annotate saturation
    ax.annotate('Saturation', xy=(0, forced_int), xytext=(0.3, forced_int + 5),
                arrowprops=dict(arrowstyle='->', color='black'),
                fontsize=10, fontweight='bold')
    ax.annotate('Spillover', xy=(1, forced_per), xytext=(0.7, forced_per + 5),
                arrowprops=dict(arrowstyle='->', color='black'),
                fontsize=10, fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()
    print(f"  Saved: {output_path}")


if __name__ == "__main__":
    import os
    
    output_dir = "/app/backend/qmrt_topology/papers/paper_5_draft/figures"
    os.makedirs(output_dir, exist_ok=True)
    
    print("="*60)
    print("PAPER 5 FIGURE GENERATION")
    print("="*60)
    print()
    
    # Collect data
    regional_data = collect_regional_data(steps=2000)
    longtime_data = collect_longtime_data(steps=4000)
    capacity_data = collect_capacity_data(steps=1500)
    
    # Generate figures
    generate_figure_1(regional_data, f"{output_dir}/fig1_regional_ecology.png")
    generate_figure_2(longtime_data, f"{output_dir}/fig2_population_trace.png")
    generate_figure_3(longtime_data, f"{output_dir}/fig3_ness_stationarity.png")
    generate_figure_4(capacity_data, f"{output_dir}/fig4_carrying_capacity.png")
    
    print()
    print("="*60)
    print("FIGURE GENERATION COMPLETE")
    print("="*60)
    print(f"Figures saved to: {output_dir}/")
