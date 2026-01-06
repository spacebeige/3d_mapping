"""
Warehouse Digital Twin System

A comprehensive Digital Twin platform for warehouse optimization with:
- 3D Visualization
- Geospatial Mapping  
- AGV Pathfinding
- ML-powered Optimization
"""

__version__ = "0.1.0"
__author__ = "SpaceBeige Team"

# Expose main classes at package level
from .main import WarehouseDigitalTwin, generate_sample_data

__all__ = [
    "WarehouseDigitalTwin",
    "generate_sample_data",
]
