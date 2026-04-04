"""
QMRT FIGURE: Interferometer Diagram with Torsion Defect
=========================================================

Creates publication-quality diagram showing:
  - Closed loop electron path
  - Torsion defect at center
  - Phase shift indication
  - Comparison with defect-free case

"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyArrowPatch, Arc
from matplotlib.lines import Line2D
import matplotlib.patheffects as pe

def create_interferometer_diagram():
    """Create the main QMRT interferometer diagram."""
    
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    
    # =========================================================================
    # LEFT PANEL: Standard AB (no torsion defect)
    # =========================================================================
    ax1 = axes[0]
    ax1.set_xlim(-2, 2)
    ax1.set_ylim(-2, 2)
    ax1.set_aspect('equal')
    ax1.axis('off')
    ax1.set_title('Standard Aharonov-Bohm\n(No Torsion Defect)', fontsize=14, fontweight='bold')
    
    # Electron source
    ax1.plot(-1.5, 0, 'ko', markersize=15)
    ax1.text(-1.5, -0.3, 'Source', ha='center', fontsize=10)
    
    # Detector
    ax1.plot(1.5, 0, 's', color='green', markersize=15)
    ax1.text(1.5, -0.3, 'Detector', ha='center', fontsize=10)
    
    # Upper path
    theta_upper = np.linspace(0, np.pi, 50)
    x_upper = 1.0 * np.cos(theta_upper)
    y_upper = 0.8 * np.sin(theta_upper)
    ax1.plot(x_upper - 0.25, y_upper, 'b-', linewidth=2, label='Path 1')
    ax1.annotate('', xy=(0.5, 0.75), xytext=(0.0, 0.8),
                arrowprops=dict(arrowstyle='->', color='blue', lw=2))
    
    # Lower path
    theta_lower = np.linspace(0, -np.pi, 50)
    x_lower = 1.0 * np.cos(theta_lower)
    y_lower = 0.8 * np.sin(theta_lower)
    ax1.plot(x_lower - 0.25, y_lower, 'r-', linewidth=2, label='Path 2')
    ax1.annotate('', xy=(0.5, -0.75), xytext=(0.0, -0.8),
                arrowprops=dict(arrowstyle='->', color='red', lw=2))
    
    # Magnetic flux (solenoid) in center
    solenoid = Circle((0, 0), 0.25, fill=True, color='gray', alpha=0.5)
    ax1.add_patch(solenoid)
    ax1.text(0, 0, 'Φ', ha='center', va='center', fontsize=14, fontweight='bold')
    
    # Phase equation
    ax1.text(0, -1.5, r'$\phi_{total} = \frac{e\Phi}{\hbar}$', 
             ha='center', fontsize=14, 
             bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
    
    # =========================================================================
    # RIGHT PANEL: QMRT (with torsion defect)
    # =========================================================================
    ax2 = axes[1]
    ax2.set_xlim(-2, 2)
    ax2.set_ylim(-2, 2)
    ax2.set_aspect('equal')
    ax2.axis('off')
    ax2.set_title('QMRT: With Torsion Defect\n(τ = +1, W = 1)', fontsize=14, fontweight='bold')
    
    # Electron source
    ax2.plot(-1.5, 0, 'ko', markersize=15)
    ax2.text(-1.5, -0.3, 'Source', ha='center', fontsize=10)
    
    # Detector
    ax2.plot(1.5, 0, 's', color='green', markersize=15)
    ax2.text(1.5, -0.3, 'Detector', ha='center', fontsize=10)
    
    # Upper path
    ax2.plot(x_upper - 0.25, y_upper, 'b-', linewidth=2)
    ax2.annotate('', xy=(0.5, 0.75), xytext=(0.0, 0.8),
                arrowprops=dict(arrowstyle='->', color='blue', lw=2))
    
    # Lower path
    ax2.plot(x_lower - 0.25, y_lower, 'r-', linewidth=2)
    ax2.annotate('', xy=(0.5, -0.75), xytext=(0.0, -0.8),
                arrowprops=dict(arrowstyle='->', color='red', lw=2))
    
    # Torsion defect (screw dislocation) - shown as spiral
    defect = Circle((0, 0), 0.25, fill=True, color='purple', alpha=0.7)
    ax2.add_patch(defect)
    ax2.text(0, 0, 'τ', ha='center', va='center', fontsize=14, 
             fontweight='bold', color='white')
    
    # Spiral indicator for chirality
    theta_spiral = np.linspace(0, 4*np.pi, 100)
    r_spiral = 0.15 + 0.02 * theta_spiral
    x_spiral = r_spiral * np.cos(theta_spiral) * 0.3
    y_spiral = r_spiral * np.sin(theta_spiral) * 0.3
    ax2.plot(x_spiral + 0.5, y_spiral + 0.5, 'purple', linewidth=1.5, alpha=0.7)
    ax2.text(0.5, 0.85, 'RH defect', ha='center', fontsize=9, color='purple')
    
    # Winding number indicator
    winding_arc = Arc((0, 0), 1.4, 1.4, angle=0, theta1=30, theta2=330, 
                      color='orange', linewidth=2, linestyle='--')
    ax2.add_patch(winding_arc)
    ax2.annotate('', xy=(0.6, 0.55), xytext=(0.7, 0.35),
                arrowprops=dict(arrowstyle='->', color='orange', lw=2))
    ax2.text(1.0, 0.9, 'W = 1', ha='center', fontsize=11, color='orange', fontweight='bold')
    
    # Phase equation with QMRT correction
    ax2.text(0, -1.5, r'$\phi_{total} = \frac{e\Phi}{\hbar} - \pi\tau W = \frac{e\Phi}{\hbar} - \pi$', 
             ha='center', fontsize=14,
             bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.8))
    
    # Highlight the extra phase
    ax2.text(0, -1.9, r'$\Delta\phi = -\pi$ (half-period shift)', 
             ha='center', fontsize=12, color='red', fontweight='bold')
    
    plt.tight_layout()
    plt.savefig('/app/backend/qmrt_topology/qmrt_interferometer_diagram.png', 
                dpi=200, bbox_inches='tight', facecolor='white')
    print("  Diagram saved to: qmrt_interferometer_diagram.png")
    plt.close()


def create_fringe_comparison():
    """Create interference fringe comparison."""
    
    fig, axes = plt.subplots(1, 2, figsize=(12, 4))
    
    # Phase values
    phi = np.linspace(0, 4*np.pi, 500)
    
    # Standard interference
    I_standard = 0.5 * (1 + np.cos(phi))
    
    # QMRT interference (shifted by π)
    I_qmrt = 0.5 * (1 + np.cos(phi - np.pi))
    
    # Left: Standard
    ax1 = axes[0]
    ax1.plot(phi / np.pi, I_standard, 'b-', linewidth=2)
    ax1.set_xlabel('Phase φ/π', fontsize=12)
    ax1.set_ylabel('Intensity I', fontsize=12)
    ax1.set_title('Standard AB Interference', fontsize=14, fontweight='bold')
    ax1.set_xlim(0, 4)
    ax1.set_ylim(0, 1.1)
    ax1.grid(True, alpha=0.3)
    ax1.axvline(x=1, color='gray', linestyle='--', alpha=0.5)
    ax1.axvline(x=2, color='gray', linestyle='--', alpha=0.5)
    ax1.axvline(x=3, color='gray', linestyle='--', alpha=0.5)
    
    # Right: QMRT
    ax2 = axes[1]
    ax2.plot(phi / np.pi, I_standard, 'b--', linewidth=1.5, alpha=0.5, label='Standard')
    ax2.plot(phi / np.pi, I_qmrt, 'r-', linewidth=2, label='With defect (τ=1)')
    ax2.set_xlabel('Phase φ/π', fontsize=12)
    ax2.set_ylabel('Intensity I', fontsize=12)
    ax2.set_title('QMRT: Half-Period Shift', fontsize=14, fontweight='bold')
    ax2.set_xlim(0, 4)
    ax2.set_ylim(0, 1.1)
    ax2.grid(True, alpha=0.3)
    ax2.legend(loc='upper right')
    
    # Indicate shift
    ax2.annotate('', xy=(1.5, 0.5), xytext=(1.0, 0.5),
                arrowprops=dict(arrowstyle='<->', color='green', lw=2))
    ax2.text(1.25, 0.6, 'Δφ = π', ha='center', fontsize=11, color='green', fontweight='bold')
    
    plt.tight_layout()
    plt.savefig('/app/backend/qmrt_topology/qmrt_fringe_shift.png', 
                dpi=200, bbox_inches='tight', facecolor='white')
    print("  Fringe comparison saved to: qmrt_fringe_shift.png")
    plt.close()


def main():
    print("=" * 70)
    print("  QMRT PUBLICATION FIGURES")
    print("=" * 70)
    print()
    
    print("  Creating interferometer diagram...")
    create_interferometer_diagram()
    
    print("  Creating fringe comparison...")
    create_fringe_comparison()
    
    print()
    print("  FIGURES COMPLETE")
    print("  Ready for publication/arXiv upload")
    print()


if __name__ == "__main__":
    main()
