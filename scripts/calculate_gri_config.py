#!/usr/bin/env python3
"""
Configuration-driven GRI calculation demo script for make calculate-gri command.
"""

import sys
import os
from pathlib import Path
import pandas as pd
import numpy as np

# Add the gri module to the path
sys.path.append(str(Path(__file__).parent.parent))

from gri.config import GRIConfig
from gri import calculate_gri, calculate_diversity_score, load_data

def generate_sample_data():
    """Generate sample survey data for demo."""
    np.random.seed(42)
    
    # Sample countries (reasonable mix of large/small populations)
    sample_countries = ['United States', 'India', 'Brazil', 'Germany', 'Nigeria', 'Japan']
    
    # Generate sample data
    sample_data = pd.DataFrame({
        'country': np.random.choice(sample_countries, 500),
        'age_group': np.random.choice(['18-25', '26-35', '36-45', '46-55', '56-65', '65+'], 500),
        'gender': np.random.choice(['Male', 'Female'], 500),
        'religion': np.random.choice([
            'Christianity', 'Islam', 'Hinduism', 'Buddhism', 'Judaism', 
            'I do not identify with any religious group or faith', 'Other religious group'
        ], 500),
        'environment': np.random.choice(['Urban', 'Rural'], 500)
    })
    
    print(f"Sample survey: {len(sample_data)} participants from {sample_data['country'].nunique()} countries")
    return sample_data

def calculate_gri_demo():
    """Run GRI calculation demo using configuration."""
    config = GRIConfig()
    dimensions = config.get_standard_scorecard()
    processed_dir = Path("data/processed")
    
    print("Running GRI calculation demo...")
    print("=" * 50)
    
    # Generate sample data
    sample_data = generate_sample_data()
    print()
    
    gri_scores = []
    diversity_scores = []
    results = []
    
    for dimension in dimensions:
        # Convert dimension name to filename
        filename = f"benchmark_{dimension['name'].lower().replace(' × ', '_').replace(' ', '_')}.csv"
        filepath = processed_dir / filename
        
        if not filepath.exists():
            print(f"⚠️  Skipping {dimension['name']}: benchmark file not found")
            continue
        
        try:
            # Load benchmark data
            benchmark_data = load_data(str(filepath))
            
            # Calculate GRI and diversity for this dimension
            gri_score = calculate_gri(sample_data, benchmark_data, dimension['columns'])
            diversity_score = calculate_diversity_score(sample_data, benchmark_data, dimension['columns'])
            
            gri_scores.append(gri_score)
            diversity_scores.append(diversity_score)
            results.append({
                'dimension': dimension['name'],
                'gri': gri_score,
                'diversity': diversity_score
            })
            
        except Exception as e:
            print(f"⚠️  Error calculating {dimension['name']}: {e}")
            continue
    
    if not results:
        print("No GRI calculations could be performed. Check that benchmark files exist.")
        return
    
    # Display results
    print("GRI Scorecard Results:")
    print("-" * 50)
    
    for result in results:
        print(f"  {result['dimension']:<25} GRI={result['gri']:.4f}, Diversity={result['diversity']:.4f}")
    
    if len(gri_scores) > 0:
        avg_gri = np.mean(gri_scores)
        avg_diversity = np.mean(diversity_scores)
        
        print()
        print(f"Average GRI: {avg_gri:.4f}")
        print(f"Average Diversity: {avg_diversity:.4f}")
        
        # Provide interpretation
        if avg_gri >= 0.8:
            assessment = "Excellent"
        elif avg_gri >= 0.6:
            assessment = "Good"
        elif avg_gri >= 0.4:
            assessment = "Moderate"
        else:
            assessment = "Poor"
        
        print(f"Assessment: {assessment} representativeness")

if __name__ == "__main__":
    calculate_gri_demo()