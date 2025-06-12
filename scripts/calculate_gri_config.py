#!/usr/bin/env python3
"""
Configuration-driven GRI calculation demo script for make calculate-gri command.
"""

import sys
import os
import argparse
from pathlib import Path
import pandas as pd
import numpy as np

# Add the gri module to the path
sys.path.append(str(Path(__file__).parent.parent))

from gri.config import GRIConfig
from gri import calculate_gri, calculate_diversity_score, load_data

def load_gd_data(gd_number=None):
    """Load real Global Dialogues data for GRI calculation."""
    gd_data_dir = Path("data/raw/survey_data/global-dialogues/Data")
    
    # Try to find available GD datasets
    gd_datasets = []
    for gd_dir in gd_data_dir.glob("GD*"):
        if gd_dir.is_dir():
            participants_file = gd_dir / f"{gd_dir.name}_participants.csv"
            if participants_file.exists():
                gd_datasets.append((gd_dir.name, participants_file))
    
    if not gd_datasets:
        print("No Global Dialogues datasets found. Using sample data instead.")
        return generate_sample_data()
    
    # Sort datasets by number
    gd_datasets.sort(reverse=True)
    
    # Use specific GD number if provided, otherwise use the most recent
    if gd_number:
        target_gd = f"GD{gd_number}"
        selected_dataset = next(((name, path) for name, path in gd_datasets if name == target_gd), None)
        if not selected_dataset:
            print(f"GD{gd_number} not found. Available datasets: {[name for name, _ in gd_datasets]}")
            print("Using most recent dataset instead.")
            gd_name, participants_file = gd_datasets[0]
        else:
            gd_name, participants_file = selected_dataset
    else:
        # Use the highest numbered (most recent) GD dataset
        gd_name, participants_file = gd_datasets[0]
    
    print(f"Loading {gd_name} participant data...")
    
    try:
        # Load the CSV with proper handling of quotes and commas
        df = pd.read_csv(participants_file, encoding='utf-8')
        
        # Handle cases where the first row might be empty (like GD4)
        if len(df.columns) == 1 and ('Unnamed:' in df.columns[0] or df.columns[0] in ['', '""']):
            print(f"Detected empty/malformed first line in {gd_name}, attempting to reload with skiprows=1...")
            df = pd.read_csv(participants_file, encoding='utf-8', skiprows=1)
        
        # Map column names to our standard format
        column_mapping = {
            'How old are you?': 'age_group',
            'What is your gender?': 'gender', 
            'What country or region do you most identify with?': 'country',
            'What religious group or faith do you most identify with?': 'religion',
            'What best describes where you live?': 'environment'
        }
        
        # Extract and rename relevant columns
        relevant_data = {}
        for original_col, standard_col in column_mapping.items():
            if original_col in df.columns:
                relevant_data[standard_col] = df[original_col]
            else:
                print(f"Warning: Column '{original_col}' not found in {gd_name}")
        
        if not relevant_data:
            print("No demographic columns found. Using sample data instead.")
            return generate_sample_data()
        
        gd_survey = pd.DataFrame(relevant_data)
        
        # Clean and standardize the data
        gd_survey = gd_survey.dropna()
        
        # Map environment values to standard format if available
        if 'environment' in gd_survey.columns:
            env_mapping = {
                'Urban': 'Urban',
                'Suburban': 'Urban',  # Consider suburban as urban
                'Rural': 'Rural'
            }
            gd_survey['environment'] = gd_survey['environment'].map(env_mapping)
        
        # Apply geographic hierarchies from configuration
        from gri.config import GRIConfig
        config = GRIConfig()
        
        # Add region column if country data exists
        if 'country' in gd_survey.columns:
            country_to_region = config.get_country_to_region_mapping()
            gd_survey['region'] = gd_survey['country'].map(country_to_region)
            
            # Add continent column if region data exists
            region_to_continent = config.get_region_to_continent_mapping()
            gd_survey['continent'] = gd_survey['region'].map(region_to_continent)
            
            # Report coverage
            regions_found = gd_survey['region'].notna().sum()
            continents_found = gd_survey['continent'].notna().sum()
            total_participants = len(gd_survey)
            
            print(f"Geographic mapping coverage:")
            print(f"  Regions: {regions_found}/{total_participants} ({regions_found/total_participants*100:.1f}%)")
            print(f"  Continents: {continents_found}/{total_participants} ({continents_found/total_participants*100:.1f}%)")
        
        print(f"Loaded {gd_name}: {len(gd_survey)} participants from {gd_survey['country'].nunique() if 'country' in gd_survey.columns else 'N/A'} countries")
        print(f"Available dimensions: {list(gd_survey.columns)}")
        
        return gd_survey
        
    except Exception as e:
        print(f"Error loading {gd_name}: {e}")
        print("Using sample data instead.")
        return generate_sample_data()

def generate_sample_data():
    """Generate sample survey data as fallback."""
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

def calculate_gri_demo(gd_number=None):
    """Run GRI calculation demo using configuration."""
    config = GRIConfig()
    dimensions = config.get_standard_scorecard()
    processed_dir = Path("data/processed")
    
    print("Running GRI calculation demo...")
    print("=" * 50)
    
    # Load Global Dialogues data
    survey_data = load_gd_data(gd_number)
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
            gri_score = calculate_gri(survey_data, benchmark_data, dimension['columns'])
            diversity_score = calculate_diversity_score(survey_data, benchmark_data, dimension['columns'])
            
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
    parser = argparse.ArgumentParser(description='Calculate GRI scores using Global Dialogues data')
    parser.add_argument('--gd', type=int, help='Global Dialogue number to use (e.g., 3 for GD3)')
    args = parser.parse_args()
    
    calculate_gri_demo(args.gd)