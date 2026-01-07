"""
CSV Loader for Warehouse Inventory Management

Handles parsing and validation of inventory CSV files with 23 columns.
Maps storage locations to 3D rack/aisle/shelf positions.
"""

import pandas as pd
import numpy as np
from typing import List, Optional, Dict, Tuple
from datetime import datetime
from pathlib import Path

from models.warehouse import Product, ZoneType, Position3D


class CSVLoader:
    """
    Load and parse warehouse inventory CSV files.
    
    Supports CSV format with 23 columns:
    - item_id, category, description, stock_level, reorder_point
    - reorder_frequency_days, lead_time_days, daily_demand, demand_std_dev
    - item_popularity_score, storage_location_id, zone, picking_time_seconds
    - handling_cost_per_unit, unit_price, holding_cost_per_unit_day
    - stockout_count_last_month, order_fulfillment_rate, total_orders_last_month
    - turnover_ratio, layout_efficiency_score, last_restock_date
    - forecasted_demand_next_7d, KPI_score
    """
    
    # Fragile item categories
    FRAGILE_CATEGORIES = {
        "Electronics", "VR Headsets", "Quantum Devices", 
        "Telemedicine", "Wearables"
    }
    
    # Expected CSV columns
    REQUIRED_COLUMNS = [
        'item_id', 'category', 'description', 'stock_level', 'reorder_point',
        'reorder_frequency_days', 'lead_time_days', 'daily_demand', 'demand_std_dev',
        'item_popularity_score', 'storage_location_id', 'zone', 'picking_time_seconds',
        'handling_cost_per_unit', 'unit_price', 'holding_cost_per_unit_day',
        'stockout_count_last_month', 'order_fulfillment_rate', 'total_orders_last_month',
        'turnover_ratio', 'layout_efficiency_score', 'last_restock_date',
        'forecasted_demand_next_7d', 'KPI_score'
    ]
    
    def __init__(self, warehouse_config: Optional[Dict] = None):
        """
        Initialize CSV loader.
        
        Args:
            warehouse_config: Optional warehouse configuration for mapping
        """
        self.warehouse_config = warehouse_config or {}
        self.products: List[Product] = []
        self.location_cache: Dict[str, Position3D] = {}
        
    def load_products(self, csv_path: str) -> List[Product]:
        """
        Load products from CSV file.
        
        Args:
            csv_path: Path to CSV file
            
        Returns:
            List of Product objects
            
        Raises:
            FileNotFoundError: If CSV file doesn't exist
            ValueError: If CSV format is invalid
        """
        csv_file = Path(csv_path)
        if not csv_file.exists():
            raise FileNotFoundError(f"CSV file not found: {csv_path}")
        
        print(f"📁 Loading CSV: {csv_path}")
        
        # Load CSV
        df = pd.read_csv(csv_path)
        
        # Validate columns
        self._validate_csv(df)
        
        print(f"✅ Loaded {len(df)} rows")
        print(f"📊 Columns: {len(df.columns)}")
        
        # Parse products
        products = []
        for idx, row in df.iterrows():
            try:
                product = self._parse_product(row)
                products.append(product)
            except Exception as e:
                print(f"⚠️ Warning: Failed to parse row {idx}: {e}")
                continue
        
        print(f"✅ Successfully parsed {len(products)} products")
        
        self.products = products
        return products
    
    def _validate_csv(self, df: pd.DataFrame):
        """
        Validate CSV structure and data types.
        
        Args:
            df: DataFrame to validate
            
        Raises:
            ValueError: If validation fails
        """
        # Check for missing columns
        missing_cols = set(self.REQUIRED_COLUMNS) - set(df.columns)
        if missing_cols:
            # Check if we have at least the core columns
            core_columns = ['item_id', 'category', 'description', 'stock_level', 
                          'daily_demand', 'storage_location_id', 'zone']
            missing_core = set(core_columns) - set(df.columns)
            if missing_core:
                raise ValueError(f"Missing required columns: {missing_core}")
            else:
                print(f"⚠️ Warning: Missing optional columns: {missing_cols}")
        
        # Validate data types
        if 'stock_level' in df.columns:
            if not pd.api.types.is_numeric_dtype(df['stock_level']):
                raise ValueError("stock_level must be numeric")
        
        if 'daily_demand' in df.columns:
            if not pd.api.types.is_numeric_dtype(df['daily_demand']):
                raise ValueError("daily_demand must be numeric")
    
    def _parse_product(self, row: pd.Series) -> Product:
        """
        Parse a single product row.
        
        Args:
            row: DataFrame row
            
        Returns:
            Product object
        """
        # Extract core fields
        item_id = str(row['item_id'])
        category = str(row['category'])
        description = str(row.get('description', category))
        stock_level = int(row.get('stock_level', 0))
        daily_demand = float(row.get('daily_demand', 0))
        
        # Get or estimate additional fields
        profit_per_unit = float(row.get('unit_price', 0)) * 0.3  # 30% profit margin
        holding_cost_per_unit_day = float(row.get('holding_cost_per_unit_day', 0.01))
        turnover_ratio = float(row.get('turnover_ratio', daily_demand / max(stock_level, 1)))
        
        # Calculate size score
        size_score = self._calculate_size_score(row, category, stock_level)
        
        # Parse zone
        zone_str = str(row.get('zone', 'B')).upper()
        try:
            zone = ZoneType(zone_str) if zone_str in ['A', 'B', 'C', 'D'] else ZoneType.B
        except:
            zone = ZoneType.B
        
        # Parse storage location
        storage_location_id = str(row.get('storage_location_id', ''))
        position = self._parse_storage_location(storage_location_id)
        
        # Create Product object
        product = Product(
            item_id=item_id,
            category=category,
            description=description,
            stock_level=stock_level,
            daily_demand=int(daily_demand),
            profit_per_unit=profit_per_unit,
            holding_cost_per_unit_day=holding_cost_per_unit_day,
            turnover_ratio=turnover_ratio,
            size_score=size_score,
            predicted_zone=zone,
            final_zone=zone,
            position=position,
            shelf=storage_location_id,
            rack_id=self._extract_rack_from_location(storage_location_id)
        )
        
        return product
    
    def _calculate_size_score(self, row: pd.Series, category: str, stock_level: int) -> float:
        """
        Calculate size score based on category and stock level.
        
        Args:
            row: DataFrame row
            category: Product category
            stock_level: Stock level
            
        Returns:
            Size score (1.0 - 10.0)
        """
        # Category-based size mapping
        category_sizes = {
            'Electronics': 3.0,
            'VR Headsets': 4.0,
            'Quantum Devices': 5.0,
            'Telemedicine': 2.5,
            'Wearables': 1.5,
            'Pharma': 1.0,
            'Groceries': 2.0,
            'Automotive': 8.0,
            'Apparel': 2.0
        }
        
        base_size = category_sizes.get(category, 3.0)
        
        # Adjust for stock level
        stock_multiplier = 1.0 + (stock_level / 1000.0)
        
        return min(10.0, base_size * stock_multiplier)
    
    def _parse_storage_location(self, storage_location_id: str) -> Position3D:
        """
        Parse storage_location_id to 3D position.
        
        Format: "L195", "L7", etc.
        Maps to Aisle/Rack/Shelf coordinates.
        
        Args:
            storage_location_id: Storage location ID
            
        Returns:
            Position3D object
        """
        if not storage_location_id or storage_location_id == 'nan':
            return Position3D(x=0, y=0, z=0)
        
        # Check cache
        if storage_location_id in self.location_cache:
            return self.location_cache[storage_location_id]
        
        # Extract numeric part (e.g., "L195" -> 195)
        try:
            location_num = int(''.join(filter(str.isdigit, storage_location_id)))
        except ValueError:
            location_num = 0
        
        # Map to 3D coordinates
        # Assume warehouse layout: 50 aisles, 10 racks per aisle, 20 shelves per rack
        aisle_num = (location_num // 200) + 1  # 200 shelves per aisle
        rack_num = ((location_num % 200) // 20) + 1  # 20 shelves per rack
        shelf_num = (location_num % 20) + 1
        
        # Calculate position (assuming 3m aisle width, 2m rack depth, 2m shelf height)
        x = aisle_num * 3.0  # Aisle spacing
        y = rack_num * 2.0   # Rack depth
        z = shelf_num * 2.0  # Shelf height
        
        position = Position3D(x=x, y=y, z=z)
        
        # Cache result
        self.location_cache[storage_location_id] = position
        
        return position
    
    def _extract_rack_from_location(self, storage_location_id: str) -> str:
        """
        Extract rack ID from storage location.
        
        Args:
            storage_location_id: Storage location ID
            
        Returns:
            Rack ID string
        """
        if not storage_location_id or storage_location_id == 'nan':
            return "R0"
        
        try:
            location_num = int(''.join(filter(str.isdigit, storage_location_id)))
            rack_num = ((location_num % 200) // 20) + 1
            return f"R{rack_num}"
        except:
            return "R0"
    
    def is_fragile(self, category: str) -> bool:
        """
        Check if item category is fragile.
        
        Args:
            category: Product category
            
        Returns:
            True if fragile, False otherwise
        """
        return category in self.FRAGILE_CATEGORIES
    
    def estimate_weight(self, row: pd.Series, category: str, stock_level: int) -> float:
        """
        Estimate weight in kg based on category and stock level.
        
        Args:
            row: DataFrame row
            category: Product category
            stock_level: Stock level
            
        Returns:
            Estimated weight in kg
        """
        # Category-based weight per unit (kg)
        category_weights = {
            'Electronics': 2.0,
            'VR Headsets': 1.5,
            'Quantum Devices': 3.0,
            'Telemedicine': 1.0,
            'Wearables': 0.5,
            'Pharma': 0.2,
            'Groceries': 1.0,
            'Automotive': 20.0,
            'Apparel': 0.5
        }
        
        unit_weight = category_weights.get(category, 1.0)
        return unit_weight * stock_level
    
    def get_statistics(self) -> Dict:
        """
        Get statistics about loaded products.
        
        Returns:
            Dictionary with statistics
        """
        if not self.products:
            return {}
        
        zones = {}
        categories = {}
        total_stock = 0
        total_demand = 0
        
        for product in self.products:
            # Count by zone
            zone = str(product.final_zone or product.predicted_zone or 'Unknown')
            zones[zone] = zones.get(zone, 0) + 1
            
            # Count by category
            categories[product.category] = categories.get(product.category, 0) + 1
            
            # Sum totals
            total_stock += product.stock_level
            total_demand += product.daily_demand
        
        return {
            'total_products': len(self.products),
            'zones': zones,
            'categories': categories,
            'total_stock': total_stock,
            'total_demand': total_demand
        }
