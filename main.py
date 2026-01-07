"""
# 🏭 Warehouse Digital Twin - Colab Integration
Main entry point for Google Colab usage with interactive UI.

This module provides a complete warehouse optimization and 3D visualization system
compatible with Google Colab notebooks.
"""

import warnings
warnings.filterwarnings('ignore')

# Core imports
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from pathlib import Path

# Visualization
import plotly.graph_objects as go
from IPython.display import display, HTML, clear_output

try:
    import ipywidgets as widgets
    WIDGETS_AVAILABLE = True
except ImportError:
    WIDGETS_AVAILABLE = False
    print("⚠️ ipywidgets not available - UI will be disabled")

# Package imports
from models import (
    WarehouseConfig, Product, ZoneType,
    WarehouseLocation, Route, SupplyChainNetwork, GeoCoordinate, FacilityType
)
from optimization import WarehouseAllocator, ProductClusterer
from viz import Warehouse3DVisualizer, WarehouseCharts
from geo import Map3DGenerator, generate_sample_network
from utils import WarehouseGenerator
from core import PathfindingGrid, generate_warehouse_navigation_grid

# New imports for CSV upload and routing
from utils.csv_loader import CSVLoader
from utils.cost_reporter import CostReporter
from routing.cost_optimizer import CostOptimizedRouter
from viz.movement_animation import MovementAnimator
from viz.rack_detail import RackDetailVisualizer


class WarehouseDigitalTwin:
    """
    Complete Digital Twin system for warehouse optimization and visualization.
    Designed for Google Colab with interactive UI.
    """
    
    def __init__(self):
        """Initialize the Digital Twin system"""
        self.warehouse_config: Optional[WarehouseConfig] = None
        self.allocator: Optional[WarehouseAllocator] = None
        self.products_df: Optional[pd.DataFrame] = None
        self.clusterer: Optional[ProductClusterer] = None
        self.network: Optional[SupplyChainNetwork] = None
        
        print("✅ Warehouse Digital Twin System initialized")
        print("📦 Version: 0.1.0")
        print("🎯 Features: 3D Warehouse | Geospatial Maps | AGV Pathfinding | ML Optimization")
    
    def create_warehouse(
        self,
        name: str = "Distribution Center",
        length: float = 50.0,
        width: float = 30.0,
        height: float = 10.0,
        num_aisles: int = 4,
        aisle_width: float = 3.0,
        rack_height: float = 8.0
    ) -> WarehouseConfig:
        """
        Create warehouse configuration.
        
        Args:
            name: Warehouse name
            length: Length in meters
            width: Width in meters
            height: Height in meters
            num_aisles: Number of aisles (no limit!)
            aisle_width: Aisle width in meters
            rack_height: Rack height in meters
            
        Returns:
            WarehouseConfig instance
        """
        print(f"🏗️ Creating warehouse: {name}")
        print(f"   Dimensions: {length}m × {width}m × {height}m")
        print(f"   Aisles: {num_aisles} (width: {aisle_width}m)")
        
        # Determine if we need lightweight mode
        lightweight = num_aisles > 100
        
        self.warehouse_config = WarehouseGenerator.create_warehouse(
            name=name,
            length=length,
            width=width,
            height=height,
            aisle_width=aisle_width,
            num_aisles=num_aisles,
            rack_height=rack_height,
            generate_full_structure=not lightweight
        )
        
        if lightweight:
            print(f"   ⚡ Lightweight mode activated (sampling for visualization)")
            print(f"   📊 Estimated shelves: {self.warehouse_config.estimated_total_shelves:,}")
        else:
            print(f"   ✅ Full structure generated")
            print(f"   📊 Total shelves: {self.warehouse_config.total_shelves:,}")
        
        print(f"   📦 Storage systems: {len(self.warehouse_config.storage_systems)}")
        print(f"   🎯 Capacity: {self.warehouse_config.dimensions.volume:,.0f} m³")
        
        # Initialize allocator with warehouse capacity
        total_capacity = self.warehouse_config.dimensions.volume * 0.7  # 70% usable
        self.allocator = WarehouseAllocator(total_space=total_capacity)
        
        return self.warehouse_config
    
    def load_products(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Load product data.
        
        Args:
            df: Products dataframe
            
        Returns:
            Processed dataframe
        """
        print(f"📦 Loading {len(df)} products...")
        self.products_df = df.copy()
        return self.products_df
    
    def train_optimizer(self, training_df: pd.DataFrame):
        """
        Train ML optimization model.
        
        Args:
            training_df: Training data
        """
        if self.allocator is None:
            self.allocator = WarehouseAllocator()
        
        print("🎓 Training optimization model...")
        self.allocator.train(training_df)
    
    def optimize_allocation(self, products_df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        """
        Optimize product allocation.
        
        Args:
            products_df: Products to allocate (uses loaded data if None)
            
        Returns:
            Allocation results dataframe
        """
        if products_df is None:
            products_df = self.products_df
        
        if products_df is None:
            raise ValueError("No products loaded. Call load_products() first.")
        
        if self.allocator is None:
            raise ValueError("Allocator not initialized. Call create_warehouse() first.")
        
        print(f"⚙️ Optimizing allocation for {len(products_df)} products...")
        
        results = self.allocator.predict_with_constraints(products_df)
        self.products_df = self.allocator.internal_df
        
        print("✅ Optimization complete!")
        print(f"   📊 Utilization: {self.get_utilization_summary()}")
        
        return results
    
    def visualize_warehouse_3d(
        self,
        show_products: bool = True,
        max_products: int = 1000
    ) -> go.Figure:
        """
        Create 3D warehouse visualization.
        
        Args:
            show_products: Whether to show products
            max_products: Maximum products to display
            
        Returns:
            Plotly Figure
        """
        if self.warehouse_config is None:
            raise ValueError("No warehouse configured. Call create_warehouse() first.")
        
        print("🎨 Generating 3D warehouse visualization...")
        
        visualizer = Warehouse3DVisualizer(self.warehouse_config)
        
        products = None
        if show_products and self.allocator and self.allocator.internal_df is not None:
            products = self.allocator.convert_to_products(self.allocator.internal_df)
        
        fig = visualizer.create_visualization(
            products=products,
            show_products=show_products,
            max_products_display=max_products
        )
        
        print("✅ 3D visualization ready!")
        return fig
    
    def visualize_utilization(self) -> go.Figure:
        """
        Create utilization charts.
        
        Returns:
            Plotly Figure
        """
        if self.allocator is None or not self.allocator.utilization:
            raise ValueError("No utilization data. Run optimize_allocation() first.")
        
        print("📊 Creating utilization charts...")
        
        fig = WarehouseCharts.create_utilization_chart(self.allocator.utilization)
        
        return fig
    
    def run_clustering(self, n_clusters: int = 5) -> pd.DataFrame:
        """
        Run product clustering analysis.
        
        Args:
            n_clusters: Number of clusters
            
        Returns:
            Clustered dataframe
        """
        if self.products_df is None:
            raise ValueError("No products loaded.")
        
        print(f"🔍 Running clustering analysis ({n_clusters} clusters)...")
        
        self.clusterer = ProductClusterer(n_clusters=n_clusters)
        clustered_df = self.clusterer.fit_predict(self.products_df)
        
        self.products_df = clustered_df
        
        print("✅ Clustering complete!")
        return clustered_df
    
    def visualize_clusters(self) -> go.Figure:
        """
        Visualize product clusters.
        
        Returns:
            Plotly Figure
        """
        if self.products_df is None or "cluster" not in self.products_df.columns:
            raise ValueError("No clustering data. Run run_clustering() first.")
        
        print("🎨 Creating cluster visualization...")
        
        fig = WarehouseCharts.create_cluster_scatter(self.products_df)
        
        return fig
    
    def create_geospatial_map(
        self,
        network: Optional[SupplyChainNetwork] = None,
        style: str = "3d"
    ):
        """
        Create 3D geospatial map.
        
        Args:
            network: Supply chain network (generates sample if None)
            style: "3d" or "2d"
            
        Returns:
            PyDeck Deck object
        """
        if network is None:
            print("🌍 Generating sample supply chain network...")
            network = generate_sample_network(
                num_warehouses=10,
                num_routes=15,
                num_demand_points=100
            )
            self.network = network
        
        print(f"🗺️ Creating {style.upper()} geospatial map...")
        
        map_gen = Map3DGenerator()
        deck = map_gen.create_supply_chain_map(network, style=style)
        
        print("✅ Geospatial map ready!")
        
        return deck
    
    def get_utilization_summary(self) -> str:
        """Get utilization summary string"""
        if self.allocator is None or not self.allocator.utilization:
            return "N/A"
        
        utilizations = [u["percent"] for u in self.allocator.utilization.values()]
        avg_util = sum(utilizations) / len(utilizations) if utilizations else 0
        
        return f"{avg_util:.1f}%"
    
    def create_dashboard(self) -> go.Figure:
        """
        Create comprehensive performance dashboard.
        
        Returns:
            Plotly Figure
        """
        if self.allocator is None or self.products_df is None:
            raise ValueError("No data available. Run optimization first.")
        
        print("📊 Creating performance dashboard...")
        
        fig = WarehouseCharts.create_performance_dashboard(
            self.allocator.utilization,
            self.products_df
        )
        
        return fig
    
    def load_products_from_csv(self, csv_path: str) -> List[Product]:
        """
        Load products from CSV file.
        
        Args:
            csv_path: Path to CSV file with 23 columns
            
        Returns:
            List of Product objects
        """
        print(f"📁 Loading products from CSV: {csv_path}")
        
        csv_loader = CSVLoader(
            warehouse_config={'dimensions': self.warehouse_config.dimensions} 
            if self.warehouse_config else None
        )
        
        products = csv_loader.load_products(csv_path)
        
        # Convert to DataFrame for internal use
        data = []
        for product in products:
            data.append({
                'item_id': product.item_id,
                'category': product.category,
                'description': product.description,
                'stock_level': product.stock_level,
                'daily_demand': product.daily_demand,
                'profit_per_unit': product.profit_per_unit,
                'holding_cost_per_unit_day': product.holding_cost_per_unit_day,
                'turnover_ratio': product.turnover_ratio,
                'size_score': product.size_score
            })
        
        self.products_df = pd.DataFrame(data)
        
        # Show statistics
        stats = csv_loader.get_statistics()
        print(f"\n📊 CSV Import Statistics:")
        print(f"   Products: {stats.get('total_products', 0)}")
        print(f"   Total Stock: {stats.get('total_stock', 0):,} units")
        print(f"   Daily Demand: {stats.get('total_demand', 0):.1f} units/day")
        print(f"   Zones: {stats.get('zones', {})}")
        
        return products
    
    def create_cost_optimized_routes(
        self,
        products: List[Product],
        operation: str = "retrieve"
    ) -> List:
        """
        Create cost-optimized routes for products.
        
        Args:
            products: List of products to route
            operation: Operation type ("retrieve", "store", "relocate")
            
        Returns:
            List of OptimalRoute objects
        """
        if not self.warehouse_config:
            raise ValueError("Warehouse not configured. Call create_warehouse() first.")
        
        print(f"🚀 Calculating cost-optimized routes for {len(products)} products...")
        
        router = CostOptimizedRouter(self.warehouse_config)
        routes = []
        
        for product in products:
            route = router.find_optimal_route(
                product=product,
                start_position=product.position,
                operation=operation
            )
            routes.append(route)
        
        print(f"✅ Routes calculated")
        print(f"   Total Cost: ${sum(r.total_cost for r in routes):.2f}")
        print(f"   Average Cost: ${sum(r.total_cost for r in routes) / len(routes):.2f}")
        
        return routes
    
    def generate_cost_report(
        self,
        products: List[Product],
        routes: List,
        output_path: str = "cost_report.csv"
    ) -> pd.DataFrame:
        """
        Generate cost analysis report.
        
        Args:
            products: List of products
            routes: List of routes
            output_path: Output CSV path
            
        Returns:
            Cost report DataFrame
        """
        print(f"📋 Generating cost report...")
        
        reporter = CostReporter(self.warehouse_config)
        df = reporter.generate_shipping_report(products, routes)
        
        df.to_csv(output_path, index=False)
        print(f"✅ Report saved: {output_path}")
        
        return df
    
    def visualize_product_movement(
        self,
        product: Product,
        route,
        duration_seconds: float = 5.0,
        output_path: str = "movement_animation.html"
    ) -> go.Figure:
        """
        Create animated visualization of product movement.
        
        Args:
            product: Product to animate
            route: Optimal route
            duration_seconds: Animation duration
            output_path: Output HTML path
            
        Returns:
            Plotly Figure
        """
        if not self.warehouse_config:
            raise ValueError("Warehouse not configured.")
        
        print(f"🎬 Creating movement animation...")
        
        animator = MovementAnimator()
        fig = animator.animate_product_movement(
            product=product,
            route=route,
            warehouse_config=self.warehouse_config,
            duration_seconds=duration_seconds
        )
        
        fig.write_html(output_path)
        print(f"✅ Animation saved: {output_path}")
        
        return fig
    
    def visualize_cost_heatmap(
        self,
        products: Optional[List[Product]] = None,
        routes: Optional[List] = None,
        output_path: str = "cost_heatmap.html"
    ) -> go.Figure:
        """
        Create 3D cost heatmap.
        
        Args:
            products: Optional products list
            routes: Optional routes list
            output_path: Output HTML path
            
        Returns:
            Plotly Figure
        """
        if not self.warehouse_config:
            raise ValueError("Warehouse not configured.")
        
        print(f"🗺️ Creating cost heatmap...")
        
        reporter = CostReporter(self.warehouse_config)
        fig = reporter.create_cost_heatmap(products, routes)
        
        fig.write_html(output_path)
        print(f"✅ Heatmap saved: {output_path}")
        
        return fig
    
    def visualize_rack_detail(
        self,
        rack_id: str,
        products: Optional[List[Product]] = None,
        output_path: str = "rack_detail.html"
    ) -> go.Figure:
        """
        Create detailed rack visualization.
        
        Args:
            rack_id: Rack identifier
            products: Optional products list
            output_path: Output HTML path
            
        Returns:
            Plotly Figure
        """
        if not self.warehouse_config:
            raise ValueError("Warehouse not configured.")
        
        print(f"🗂️ Creating rack detail view...")
        
        visualizer = RackDetailVisualizer(self.warehouse_config)
        fig = visualizer.visualize_rack(rack_id, products)
        
        fig.write_html(output_path)
        print(f"✅ Rack view saved: {output_path}")
        
        return fig
    
    def create_allocator(self) -> WarehouseAllocator:
        """
        Create and return warehouse allocator.
        
        Returns:
            WarehouseAllocator instance
        """
        if self.allocator is None:
            total_capacity = self.warehouse_config.dimensions.volume * 0.7 if self.warehouse_config else 1000000
            self.allocator = WarehouseAllocator(total_space=total_capacity)
        
        return self.allocator


def generate_sample_data(num_products: int = 100) -> pd.DataFrame:
    """
    Generate sample product data for testing.
    
    Args:
        num_products: Number of products to generate
        
    Returns:
        Sample products dataframe
    """
    categories = ['electronics', 'groceries', 'pharma', 'apparel', 'automotive']
    
    data = {
        'item_id': [f"ITEM{i:04d}" for i in range(1, num_products + 1)],
        'category': np.random.choice(categories, num_products),
        'daily_demand': np.random.randint(10, 100, num_products),
        'stock_level': np.random.randint(50, 500, num_products),
        'description': [f"Product {i}" for i in range(1, num_products + 1)]
    }
    
    return pd.DataFrame(data)


# Initialize system on import
print("=" * 60)
print("🏭 WAREHOUSE DIGITAL TWIN SYSTEM")
print("=" * 60)
print("\n📦 To get started:")
print("   1. twin = WarehouseDigitalTwin()")
print("   2. twin.create_warehouse(num_aisles=10)")
print("   3. data = generate_sample_data(200)")
print("   4. twin.train_optimizer(data)")
print("   5. results = twin.optimize_allocation(data)")
print("   6. fig = twin.visualize_warehouse_3d()")
print("   7. fig.show()")
print("\n🗺️ For geospatial maps:")
print("   deck = twin.create_geospatial_map()")
print("   deck.show()")
print("\n" + "=" * 60)
