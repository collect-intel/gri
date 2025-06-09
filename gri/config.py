"""
Configuration management for GRI calculations.

This module provides functionality to load and manage configuration files
for dimensions, segments, and regional mappings.
"""

import os
import yaml
from typing import Dict, List, Any, Optional
from pathlib import Path


class GRIConfig:
    """Configuration manager for GRI calculations."""
    
    def __init__(self, config_dir: str = None):
        """
        Initialize configuration manager.
        
        Args:
            config_dir: Path to configuration directory. Defaults to 'config' in project root.
        """
        if config_dir is None:
            # Default to config directory relative to this file
            project_root = Path(__file__).parent.parent
            config_dir = project_root / "config"
        
        self.config_dir = Path(config_dir)
        self._dimensions = None
        self._segments = None
        self._regions = None
    
    def _load_yaml(self, filename: str) -> Dict[str, Any]:
        """Load a YAML configuration file."""
        file_path = self.config_dir / filename
        if not file_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    @property
    def dimensions(self) -> Dict[str, Any]:
        """Get dimensions configuration."""
        if self._dimensions is None:
            self._dimensions = self._load_yaml("dimensions.yaml")
        return self._dimensions
    
    @property
    def segments(self) -> Dict[str, Any]:
        """Get segments configuration."""
        if self._segments is None:
            self._segments = self._load_yaml("segments.yaml")
        return self._segments
    
    @property
    def regions(self) -> Dict[str, Any]:
        """Get regions configuration."""
        if self._regions is None:
            self._regions = self._load_yaml("regions.yaml")
        return self._regions
    
    def get_standard_scorecard(self) -> List[Dict[str, Any]]:
        """Get the standard GRI scorecard dimensions."""
        return self.dimensions["standard_scorecard"]
    
    def get_extended_dimensions(self) -> List[Dict[str, Any]]:
        """Get all available extended dimensions."""
        extended = self.dimensions.get("extended_dimensions", [])
        # Handle case where extended_dimensions is None or empty
        if extended is None:
            return []
        return extended
    
    def get_all_dimensions(self) -> List[Dict[str, Any]]:
        """Get all dimensions (standard + extended)."""
        return self.get_standard_scorecard() + self.get_extended_dimensions()
    
    def get_dimension_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a specific dimension by name."""
        for dim in self.get_all_dimensions():
            if dim["name"] == name:
                return dim
        return None
    
    def get_segment_mapping(self, source: str, segment_type: str) -> Dict[str, List[str]]:
        """
        Get segment mapping for a specific source and segment type.
        
        Args:
            source: Data source (e.g., 'benchmark_mappings', 'global_dialogues')
            segment_type: Type of segment (e.g., 'age_group', 'country')
            
        Returns:
            Mapping dictionary from standard names to source values
        """
        if source == "benchmark_mappings":
            return self.segments["benchmark_mappings"].get(segment_type, {})
        elif source in self.segments["survey_mappings"]:
            mapping = self.segments["survey_mappings"][source].get(segment_type, {})
            
            # Handle inheritance
            if isinstance(mapping, dict) and "inherit_from" in mapping:
                inherit_path = mapping["inherit_from"].split(".")
                base_mapping = self.segments
                for key in inherit_path:
                    base_mapping = base_mapping[key]
                return base_mapping
            
            return mapping
        else:
            return {}
    
    def get_country_to_region_mapping(self) -> Dict[str, str]:
        """Get mapping from country to region."""
        country_to_region = {}
        for region, countries in self.regions["country_to_region"].items():
            for country in countries:
                country_to_region[country] = region
        return country_to_region
    
    def get_region_to_continent_mapping(self) -> Dict[str, str]:
        """Get mapping from region to continent."""
        region_to_continent = {}
        for continent, regions in self.regions["region_to_continent"].items():
            for region in regions:
                region_to_continent[region] = continent
        return region_to_continent
    
    def get_country_to_continent_mapping(self) -> Dict[str, str]:
        """Get mapping from country to continent."""
        country_to_region = self.get_country_to_region_mapping()
        region_to_continent = self.get_region_to_continent_mapping()
        
        country_to_continent = {}
        for country, region in country_to_region.items():
            continent = region_to_continent.get(region)
            if continent:
                country_to_continent[country] = continent
        
        return country_to_continent
    
    def validate_dimension_requirements(self, dimension: Dict[str, Any]) -> bool:
        """
        Check if a dimension's requirements are satisfied.
        
        Args:
            dimension: Dimension configuration dictionary
            
        Returns:
            True if requirements are satisfied, False otherwise
        """
        requirements = dimension.get("requires_mapping", [])
        
        for requirement in requirements:
            if requirement == "country_to_region":
                # Check if region mapping exists
                if not self.regions.get("country_to_region"):
                    return False
            elif requirement == "country_to_continent":
                # Check if continent mapping can be constructed
                if not (self.regions.get("country_to_region") and 
                       self.regions.get("region_to_continent")):
                    return False
        
        return True


# Global configuration instance
_config = None


def get_config(config_dir: str = None) -> GRIConfig:
    """Get the global configuration instance."""
    global _config
    if _config is None or config_dir is not None:
        _config = GRIConfig(config_dir)
    return _config