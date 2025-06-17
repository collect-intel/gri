"""
Calculate within-stratum variance from Global Dialogues indicator questions.

This module estimates how much responses vary within each demographic group
using consistent poll questions across GD surveys.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple


def calculate_within_stratum_variance(
    survey_df: pd.DataFrame,
    stratum_column: str,
    indicator_columns: List[str],
    response_mapping: Dict[str, Dict[str, float]] = None
) -> Dict[str, float]:
    """
    Calculate within-stratum variance for each demographic group using indicator responses.
    
    Args:
        survey_df: DataFrame with survey responses including demographics and indicators
        stratum_column: Column defining strata (e.g., 'country', 'country_gender_age')
        indicator_columns: List of indicator question columns to analyze
        response_mapping: Optional dict mapping text responses to numeric values
                         If None, assumes responses are already numeric
    
    Returns:
        Dict mapping stratum name to average within-stratum variance
    """
    variances = {}
    
    # Default 5-point scale mapping if not provided
    if response_mapping is None:
        response_mapping = {
            # Trust questions
            "Strongly Distrust": 1, "Somewhat Distrust": 2, 
            "Neither Trust Nor Distrust": 3, "Somewhat Trust": 4, "Strongly Trust": 5,
            
            # Impact questions  
            "Profoundly Worse": 1, "Noticeably Worse": 2,
            "No Major Change": 3, "Noticeably Better": 4, "Profoundly Better": 5,
            
            # Risk/benefit questions
            "Risks far outweigh benefits": 1, "Risks slightly outweigh benefits": 2,
            "Risks and benefits are equal": 3, "Benefits slightly outweigh risks": 4,
            "Benefits far outweigh risks": 5,
            
            # Frequency questions
            "never": 1, "annually": 2, "monthly": 3, "weekly": 4, "daily": 5,
            
            # Yes/No/Unsure
            "Yes": 1, "No": 0, "Don't Know": 0.5, "Unsure": 0.5,
            "Agree": 1, "Disagree": 0,
            
            # Excitement/concern
            "More concerned than excited": 1, "Equally concerned and excited": 2,
            "More excited than concerned": 3
        }
    
    # Convert responses to numeric
    numeric_df = survey_df.copy()
    for col in indicator_columns:
        if col in numeric_df.columns:
            # Map text to numeric
            if numeric_df[col].dtype == 'object':
                numeric_df[col] = numeric_df[col].map(
                    lambda x: response_mapping.get(x, np.nan) if pd.notna(x) else np.nan
                )
    
    # Calculate variance for each stratum
    for stratum in numeric_df[stratum_column].unique():
        stratum_data = numeric_df[numeric_df[stratum_column] == stratum]
        
        if len(stratum_data) < 2:  # Need at least 2 responses
            variances[stratum] = 0.25  # Default to maximum for binary
            continue
            
        # Calculate variance for each indicator
        stratum_variances = []
        for col in indicator_columns:
            if col in stratum_data.columns:
                values = stratum_data[col].dropna()
                if len(values) >= 2:
                    # Normalize to 0-1 scale if needed
                    if values.max() > 1:
                        values = (values - values.min()) / (values.max() - values.min())
                    
                    var = values.var()
                    stratum_variances.append(var)
        
        # Average variance across all indicators
        if stratum_variances:
            variances[stratum] = np.mean(stratum_variances)
        else:
            variances[stratum] = 0.25  # Default
    
    return variances


def calculate_variance_by_question_type(
    survey_df: pd.DataFrame,
    stratum_column: str,
    indicator_codesheet: pd.DataFrame
) -> Dict[str, Dict[str, float]]:
    """
    Calculate within-stratum variance grouped by question category.
    
    This helps identify which topics have more/less consensus within demographics.
    
    Args:
        survey_df: Survey data with responses
        stratum_column: Demographic grouping column
        indicator_codesheet: DataFrame with indicator metadata
        
    Returns:
        Nested dict: {question_category: {stratum: variance}}
    """
    category_variances = {}
    
    # Group indicators by category
    for category in indicator_codesheet['question_category'].unique():
        category_questions = indicator_codesheet[
            indicator_codesheet['question_category'] == category
        ]['question_code'].tolist()
        
        # Filter to questions that exist in survey
        available_questions = [q for q in category_questions if q in survey_df.columns]
        
        if available_questions:
            variances = calculate_within_stratum_variance(
                survey_df, stratum_column, available_questions
            )
            category_variances[category] = variances
    
    return category_variances


def optimal_allocation_with_survey_variance(
    population_proportions: Dict[str, float],
    total_sample_size: int,
    survey_df: pd.DataFrame,
    stratum_column: str,
    indicator_columns: List[str] = None
) -> Tuple[Dict[str, int], Dict[str, float]]:
    """
    Calculate optimal allocation using actual within-stratum variance from survey data.
    
    Args:
        population_proportions: Population proportion for each stratum
        total_sample_size: Target total sample size
        survey_df: Historical survey data to estimate variance
        stratum_column: Column defining strata
        indicator_columns: Which indicators to use (None = use all available)
        
    Returns:
        Tuple of (optimal allocations, estimated variances used)
    """
    # Get all indicator columns if not specified
    if indicator_columns is None:
        # Common indicator patterns from GD surveys
        indicator_patterns = ['ai_', 'trust_', 'impact_', 'job_', 'automation_']
        indicator_columns = [col for col in survey_df.columns 
                           if any(col.startswith(pat) for pat in indicator_patterns)]
    
    # Calculate within-stratum variances
    variances = calculate_within_stratum_variance(
        survey_df, stratum_column, indicator_columns
    )
    
    # Now use these variances for optimal allocation
    from gri.variance_weighted import optimal_allocation
    
    allocations = optimal_allocation(
        population_proportions,
        total_sample_size,
        within_stratum_variances=variances
    )
    
    return allocations, variances


# Example usage function
def demonstrate_with_gd_data():
    """
    Example showing how to use GD indicator data for variance estimation.
    """
    print("Example: Using GD3 data to estimate within-country variance")
    print("=" * 60)
    
    # Pseudo-code for the process:
    print("""
    1. Load GD3 standardized data:
       df = pd.read_csv('GD3_aggregate_standardized.csv')
    
    2. Load indicator definitions:
       indicators = pd.read_csv('INDICATOR_CODESHEET.csv')
    
    3. Calculate within-country variance for trust questions:
       trust_cols = ['trust_govt', 'trust_ai_co', 'trust_personal_ai_chatbot']
       variances = calculate_within_stratum_variance(df, 'country', trust_cols)
    
    4. Use these variances for optimal allocation:
       optimal, vars_used = optimal_allocation_with_survey_variance(
           population_proportions={'USA': 0.04, 'China': 0.18, ...},
           total_sample_size=5000,
           survey_df=df,
           stratum_column='country'
       )
    
    Result: Allocation that accounts for actual response diversity within each country!
    """)
    
    return None


if __name__ == "__main__":
    demonstrate_with_gd_data()