#!/usr/bin/env python3
"""Run comprehensive validation and save results to file"""
import json
import time
from qmrt_comprehensive_validation import run_comprehensive_validation

print("Starting QMRT Comprehensive Validation...")
print("This may take several minutes...")
start = time.time()

try:
    results = run_comprehensive_validation(quick_mode=True, seed=42)
    
    # Save results to file
    with open('/app/backend/validation_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    elapsed = time.time() - start
    print(f"\n✅ Validation completed in {elapsed:.1f}s")
    print(f"Results saved to /app/backend/validation_results.json")
    print("\nSUMMARY:")
    print(json.dumps(results['summary'], indent=2))
    
except Exception as e:
    print(f"\n❌ Validation failed: {e}")
    import traceback
    traceback.print_exc()
    
    # Save error info
    with open('/app/backend/validation_results.json', 'w') as f:
        json.dump({'error': str(e)}, f)
