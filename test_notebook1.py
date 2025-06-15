#!/usr/bin/env python3
"""Test script to debug notebook 1 issues."""

import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Add the gri module to the path
sys.path.append('.')

try:
    # Import the new GRI module functions
    from gri.data_loader import load_benchmark_suite, load_gd_survey
    from gri.validation import validate_benchmark_data, validate_survey_data
    from gri.config import GRIConfig
    
    print("✅ Imports successful")
    
    # Initialize configuration
    config = GRIConfig()
    print(f"✅ Config initialized with {len(config.get_all_dimensions())} dimensions")
    
    # Try loading benchmark suite
    print("\nTesting benchmark loading...")
    benchmarks = load_benchmark_suite(data_dir='data/processed')
    print(f"✅ Loaded {len(benchmarks)} benchmarks")
    
except Exception as e:
    print(f"❌ Error: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()