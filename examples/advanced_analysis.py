#!/usr/bin/env python3
"""
Advanced GRI Analysis Examples

This script demonstrates the GRIAnalysis class for comprehensive analysis workflows.
"""

from pathlib import Path
import matplotlib.pyplot as plt

# Add parent directory to path if running from examples folder
import sys
sys.path.append(str(Path(__file__).parent.parent))

from gri import GRIAnalysis


def example_1_full_analysis_workflow():
    """Complete analysis workflow with GRIAnalysis class."""
    print("=" * 60)
    print("Example 1: Full Analysis Workflow")
    print("=" * 60)
    
    # Create analysis object from survey file
    analysis = GRIAnalysis.from_survey_file(
        'data/raw/survey_data/global-dialogues/Data/GD3/GD3_participants.csv',
        survey_type='gd',
        survey_name='Global Dialogues 3'
    )
    
    # Print quick summary
    analysis.print_summary()
    
    # Calculate comprehensive scorecard with max possible scores
    print("\nCalculating scorecard with maximum possible scores...")
    scorecard = analysis.calculate_scorecard(
        include_max_possible=True,
        n_simulations=100  # Use fewer simulations for example
    )
    
    # Show results
    print("\nScorecard Results:")
    print(scorecard[['dimension', 'gri_score', 'max_possible_score', 'efficiency_ratio']])
    
    # Generate and save visualizations
    print("\nGenerating visualizations...")
    
    # Create output directory
    output_dir = Path('examples/output')
    output_dir.mkdir(exist_ok=True)
    
    # Scorecard plot
    analysis.plot_scorecard(save_to=output_dir / 'gd3_scorecard.png')
    print(f"  ✓ Saved scorecard plot")
    
    # Top deviations plot
    analysis.plot_top_deviations(
        'Country × Gender × Age',
        n=20,
        save_to=output_dir / 'gd3_top_deviations.png'
    )
    print(f"  ✓ Saved deviations plot")
    
    # Generate text report
    report = analysis.generate_report(
        output_file=output_dir / 'gd3_report.txt',
        include_analysis=True
    )
    print(f"  ✓ Generated text report")
    
    # Export results to Excel
    analysis.export_results(
        format='excel',
        filepath=output_dir / 'gd3_results.xlsx'
    )
    print(f"  ✓ Exported results to Excel")
    print()


def example_2_segment_analysis():
    """Detailed segment deviation analysis."""
    print("=" * 60)
    print("Example 2: Segment Deviation Analysis")
    print("=" * 60)
    
    # Load survey
    analysis = GRIAnalysis.from_survey_file(
        'data/raw/survey_data/global-dialogues/Data/GD3/GD3_participants.csv',
        survey_type='gd'
    )
    
    # Analyze Country × Gender × Age dimension
    dimension = 'Country × Gender × Age'
    
    # Get top over-represented segments
    print(f"\nTop 10 OVER-represented segments in {dimension}:")
    over_rep = analysis.get_top_segments(dimension, n=10, segment_type='over')
    
    for idx, row in over_rep.iterrows():
        print(f"  {row.get('segment_name', 'Unknown')}: "
              f"+{row['deviation']:.3f} "
              f"({row['sample_proportion']*100:.1f}% vs {row['benchmark_proportion']*100:.1f}%)")
    
    # Get top under-represented segments
    print(f"\nTop 10 UNDER-represented segments in {dimension}:")
    under_rep = analysis.get_top_segments(dimension, n=10, segment_type='under')
    
    for idx, row in under_rep.iterrows():
        print(f"  {row.get('segment_name', 'Unknown')}: "
              f"{row['deviation']:.3f} "
              f"({row['sample_proportion']*100:.1f}% vs {row['benchmark_proportion']*100:.1f}%)")
    
    # Calculate impact of fixing these segments
    from gri import calculate_dimension_impact
    
    impact = calculate_dimension_impact(
        analysis.survey_data,
        analysis.benchmarks[analysis._get_benchmark_key(dimension)],
        ['country', 'gender', 'age_group'],
        n_targets=10
    )
    
    print(f"\nImpact Analysis:")
    print(f"  Current GRI: {impact['current_gri']:.4f}")
    print(f"  Potential GRI (fixing top 10): {impact['potential_gri']:.4f}")
    print(f"  Improvement: +{impact['improvement']:.4f} ({impact['improvement_pct']:.1f}%)")
    print()


def example_3_survey_comparison():
    """Compare multiple surveys."""
    print("=" * 60)
    print("Example 3: Multi-Survey Comparison")
    print("=" * 60)
    
    from gri import create_comparison_plot, generate_comparison_report
    
    # Analyze multiple GD surveys
    surveys = {}
    survey_files = {
        'GD1': 'data/raw/survey_data/global-dialogues/Data/GD1/GD1_participants.csv',
        'GD2': 'data/raw/survey_data/global-dialogues/Data/GD2/GD2_participants.csv',
        'GD3': 'data/raw/survey_data/global-dialogues/Data/GD3/GD3_participants.csv'
    }
    
    print("Loading and analyzing surveys...")
    for name, filepath in survey_files.items():
        try:
            analysis = GRIAnalysis.from_survey_file(filepath, survey_name=name)
            surveys[name] = analysis.calculate_scorecard()
            print(f"  ✓ Analyzed {name}")
        except Exception as e:
            print(f"  ✗ Failed to analyze {name}: {e}")
    
    if len(surveys) >= 2:
        # Create comparison visualization
        output_dir = Path('examples/output')
        output_dir.mkdir(exist_ok=True)
        
        # Compare a specific dimension
        dimension = 'Country × Gender × Age'
        fig = create_comparison_plot(
            surveys,
            dimension,
            save_path=output_dir / 'survey_comparison.png'
        )
        print(f"\n✓ Created comparison plot for {dimension}")
        
        # Generate comparison report
        report = generate_comparison_report(
            surveys,
            output_file=output_dir / 'comparison_report.txt',
            include_trends=True
        )
        print("✓ Generated comparison report")
        
        # Show average GRI trends
        print("\nAverage GRI Score Trends:")
        for name, scorecard in surveys.items():
            avg_gri = scorecard['gri_score'].mean()
            print(f"  {name}: {avg_gri:.4f}")
    print()


def example_4_custom_analysis():
    """Custom analysis with specific requirements."""
    print("=" * 60)
    print("Example 4: Custom Analysis Workflow")
    print("=" * 60)
    
    # Load survey with custom configuration
    from gri import GRIConfig
    
    # Use custom config if needed
    config = GRIConfig(config_dir='config')
    
    # Create analysis with pre-filtered data
    import pandas as pd
    from gri import load_gd_survey
    
    # Load and filter survey data
    survey_data = load_gd_survey('data/raw/survey_data/global-dialogues/Data/GD3/GD3_participants.csv')
    
    # Example: Focus on specific regions
    regions_of_interest = ['Eastern Asia', 'Northern America', 'Western Europe']
    filtered_survey = survey_data[survey_data['region'].isin(regions_of_interest)]
    
    print(f"Filtered to {len(filtered_survey)} participants from {regions_of_interest}")
    
    # Create analysis with filtered data
    analysis = GRIAnalysis(
        filtered_survey,
        survey_name="GD3 - Select Regions",
        config=config
    )
    
    # Calculate scores for specific dimensions only
    scorecard = analysis.calculate_scorecard(
        dimensions=['Country', 'Gender', 'Age Group'],
        include_max_possible=False  # Faster without max scores
    )
    
    print("\nFiltered Analysis Results:")
    for _, row in scorecard.iterrows():
        print(f"  {row['dimension']}: {row['gri_score']:.4f}")
    
    # Check alignment for filtered data
    alignment = analysis.check_alignment()
    print("\nAlignment Check for Filtered Data:")
    for dim, report in alignment.items():
        if report['status'] == 'complete':
            print(f"  {dim}: {report['overall_alignment']*100:.1f}% aligned")
    print()


def example_5_max_possible_analysis():
    """Analyze maximum possible scores for different sample sizes."""
    print("=" * 60)
    print("Example 5: Maximum Possible Score Analysis")
    print("=" * 60)
    
    from gri import generate_sample_size_curve, load_data
    import matplotlib.pyplot as plt
    
    # Load benchmark data
    benchmark = load_data('data/processed/benchmark_country_gender_age.csv')
    
    # Test different sample sizes
    sample_sizes = [100, 250, 500, 1000, 2000, 5000]
    
    print("Calculating maximum possible scores for different sample sizes...")
    curve_data = generate_sample_size_curve(
        benchmark,
        sample_sizes,
        dimension_columns=['country', 'gender', 'age_group'],
        n_simulations=100  # Fewer simulations for speed
    )
    
    # Display results
    print("\nSample Size vs Maximum Possible GRI:")
    for _, row in curve_data.iterrows():
        print(f"  N={row['sample_size']:,}: "
              f"Max GRI = {row['max_gri_mean']:.4f} ± {row['max_gri_std']:.4f}")
    
    # Plot the curve
    plt.figure(figsize=(10, 6))
    plt.errorbar(
        curve_data['sample_size'],
        curve_data['max_gri_mean'],
        yerr=curve_data['max_gri_std'],
        marker='o',
        capsize=5
    )
    plt.xlabel('Sample Size')
    plt.ylabel('Maximum Possible GRI Score')
    plt.title('Maximum Achievable GRI by Sample Size\n(Country × Gender × Age)')
    plt.grid(True, alpha=0.3)
    plt.xscale('log')
    
    output_dir = Path('examples/output')
    output_dir.mkdir(exist_ok=True)
    plt.savefig(output_dir / 'max_gri_curve.png', dpi=150, bbox_inches='tight')
    plt.close()
    
    print("\n✓ Saved maximum GRI curve plot")
    print()


if __name__ == "__main__":
    # Note: Some examples may take time due to calculations
    print("Running advanced GRI analysis examples...")
    print("Note: These examples assume data files are in standard locations.")
    print("Adjust paths as needed for your setup.\n")
    
    # Run examples
    examples = [
        ("Full Analysis Workflow", example_1_full_analysis_workflow),
        ("Segment Analysis", example_2_segment_analysis),
        ("Survey Comparison", example_3_survey_comparison),
        ("Custom Analysis", example_4_custom_analysis),
        ("Max Possible Analysis", example_5_max_possible_analysis)
    ]
    
    for name, func in examples:
        try:
            func()
        except Exception as e:
            print(f"\n{name} failed: {e}")
            print("This might be due to missing data files or dependencies.\n")
    
    print("\nAll examples completed!")
    print("Check the 'examples/output/' directory for generated files.")