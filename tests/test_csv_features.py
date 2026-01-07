"""
Tests for CSV upload and cost-optimized routing features
"""

import pytest
import pandas as pd
from pathlib import Path

from utils.csv_loader import CSVLoader
from routing.cost_optimizer import CostOptimizedRouter
from utils.cost_reporter import CostReporter
from models.warehouse import WarehouseConfig, Product, ZoneType, Position3D, Dimensions3D, WarehouseLayout, AccessPoint
from utils import WarehouseGenerator


class TestCSVLoader:
    """Test CSV loading functionality"""
    
    def test_csv_loader_init(self):
        """Test CSV loader initialization"""
        loader = CSVLoader()
        assert loader is not None
        assert loader.products == []
        assert loader.location_cache == {}
    
    def test_is_fragile(self):
        """Test fragile item detection"""
        loader = CSVLoader()
        
        assert loader.is_fragile("Electronics") == True
        assert loader.is_fragile("VR Headsets") == True
        assert loader.is_fragile("Quantum Devices") == True
        assert loader.is_fragile("Telemedicine") == True
        assert loader.is_fragile("Wearables") == True
        assert loader.is_fragile("Groceries") == False
        assert loader.is_fragile("Pharma") == False
    
    def test_parse_storage_location(self):
        """Test storage location parsing"""
        loader = CSVLoader()
        
        # Test valid location
        pos = loader._parse_storage_location("L195")
        assert isinstance(pos, Position3D)
        assert pos.x > 0
        assert pos.y > 0
        assert pos.z > 0
        
        # Test empty location
        pos = loader._parse_storage_location("")
        assert pos.x == 0 and pos.y == 0 and pos.z == 0
        
        # Test caching
        pos1 = loader._parse_storage_location("L100")
        pos2 = loader._parse_storage_location("L100")
        assert pos1.x == pos2.x
        assert pos1.y == pos2.y
        assert pos1.z == pos2.z
    
    def test_extract_rack_from_location(self):
        """Test rack ID extraction"""
        loader = CSVLoader()
        
        rack_id = loader._extract_rack_from_location("L195")
        assert rack_id.startswith("R")
        
        rack_id = loader._extract_rack_from_location("")
        assert rack_id == "R0"


class TestAccessPoint:
    """Test AccessPoint model"""
    
    def test_access_point_creation(self):
        """Test creating access point"""
        ap = AccessPoint(
            id="test_entry",
            name="Test Entry",
            type="entry",
            position=Position3D(x=5.0, y=5.0, z=0.0),
            capabilities=["standard", "fragile"],
            base_cost=2.0,
            capacity_per_hour=200
        )
        
        assert ap.id == "test_entry"
        assert ap.name == "Test Entry"
        assert ap.type == "entry"
        assert ap.base_cost == 2.0
        assert ap.capacity_per_hour == 200
        assert ap.active == True
        assert "standard" in ap.capabilities
        assert "fragile" in ap.capabilities


class TestWarehouseConfigAccessPoints:
    """Test WarehouseConfig with access points"""
    
    def test_warehouse_with_access_points(self):
        """Test creating warehouse with access points"""
        warehouse = WarehouseGenerator.create_warehouse(
            name="Test Warehouse",
            length=100.0,
            width=80.0,
            height=10.0,
            num_aisles=10
        )
        
        assert warehouse is not None
        assert warehouse.entry_points == []
        assert warehouse.exit_points == []
        
        # Add default access points
        warehouse.add_default_access_points()
        
        assert len(warehouse.entry_points) == 4
        assert len(warehouse.exit_points) == 4
        
        # Check entry points
        assert any(ap.name == "Main Entry" for ap in warehouse.entry_points)
        assert any(ap.name == "Receiving Dock" for ap in warehouse.entry_points)
        
        # Check exit points
        assert any(ap.name == "Shipping Dock A" for ap in warehouse.exit_points)
        assert any(ap.name == "Express Dock" for ap in warehouse.exit_points)


class TestCostOptimizedRouter:
    """Test cost-optimized routing"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.warehouse = WarehouseGenerator.create_warehouse(
            name="Test Warehouse",
            length=100.0,
            width=80.0,
            height=10.0,
            num_aisles=10
        )
        self.warehouse.add_default_access_points()
        self.router = CostOptimizedRouter(self.warehouse)
    
    def test_router_initialization(self):
        """Test router initialization"""
        assert self.router is not None
        assert self.router.warehouse == self.warehouse
    
    def test_is_item_fragile(self):
        """Test fragile item detection"""
        product = Product(
            item_id="TEST001",
            category="Electronics",
            description="Test Product",
            stock_level=100,
            daily_demand=10,
            profit_per_unit=50.0,
            holding_cost_per_unit_day=0.15,
            turnover_ratio=2.5,
            size_score=3.0,
            is_fragile=True
        )
        
        assert self.router._is_item_fragile(product) == True
        
        product.is_fragile = False
        assert self.router._is_item_fragile(product) == False
    
    def test_is_item_heavy(self):
        """Test heavy item detection"""
        product = Product(
            item_id="TEST002",
            category="Automotive",
            description="Test Product",
            stock_level=100,
            daily_demand=10,
            profit_per_unit=50.0,
            holding_cost_per_unit_day=0.15,
            turnover_ratio=2.5,
            size_score=3.0,
            weight_kg=25.0
        )
        
        assert self.router._is_item_heavy(product) == True
        
        product.weight_kg = 15.0
        assert self.router._is_item_heavy(product) == False
    
    def test_is_item_large(self):
        """Test large item detection"""
        product = Product(
            item_id="TEST003",
            category="Test",
            description="Test Product",
            stock_level=100,
            daily_demand=10,
            profit_per_unit=50.0,
            holding_cost_per_unit_day=0.15,
            turnover_ratio=2.5,
            size_score=5.0
        )
        
        assert self.router._is_item_large(product) == True
        
        product.size_score = 2.0
        assert self.router._is_item_large(product) == False
    
    def test_find_optimal_route(self):
        """Test finding optimal route"""
        product = Product(
            item_id="TEST004",
            category="Electronics",
            description="Test Product",
            stock_level=100,
            daily_demand=10,
            profit_per_unit=50.0,
            holding_cost_per_unit_day=0.15,
            turnover_ratio=2.5,
            size_score=3.0,
            position=Position3D(x=20.0, y=30.0, z=2.0)
        )
        
        route = self.router.find_optimal_route(
            product=product,
            start_position=product.position,
            operation="retrieve"
        )
        
        assert route is not None
        assert route.product == product
        assert route.total_cost > 0
        assert route.total_distance > 0
        assert route.exit_point is not None
        assert len(route.waypoints) > 0


class TestCostReporter:
    """Test cost reporting"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.warehouse = WarehouseGenerator.create_warehouse(
            name="Test Warehouse",
            length=100.0,
            width=80.0,
            height=10.0,
            num_aisles=10
        )
        self.warehouse.add_default_access_points()
        self.reporter = CostReporter(self.warehouse)
    
    def test_reporter_initialization(self):
        """Test reporter initialization"""
        assert self.reporter is not None
        assert self.reporter.warehouse == self.warehouse
    
    def test_generate_shipping_report(self):
        """Test generating shipping report"""
        # Create test products
        products = [
            Product(
                item_id=f"TEST{i:03d}",
                category="Electronics",
                description=f"Test Product {i}",
                stock_level=100,
                daily_demand=10,
                profit_per_unit=50.0,
                holding_cost_per_unit_day=0.15,
                turnover_ratio=2.5,
                size_score=3.0,
                position=Position3D(x=20.0 + i*5, y=30.0, z=2.0)
            )
            for i in range(3)
        ]
        
        # Create routes
        router = CostOptimizedRouter(self.warehouse)
        routes = [
            router.find_optimal_route(product, product.position, operation="retrieve")
            for product in products
        ]
        
        # Generate report
        df = self.reporter.generate_shipping_report(products, routes)
        
        assert df is not None
        assert len(df) == 3
        assert 'item_id' in df.columns
        assert 'total_cost' in df.columns
        assert 'distance_meters' in df.columns
        
        # Check that costs are positive
        assert all(df['total_cost'] > 0)
        assert all(df['distance_meters'] > 0)
    
    def test_generate_summary_statistics(self):
        """Test generating summary statistics"""
        products = [
            Product(
                item_id=f"TEST{i:03d}",
                category="Electronics",
                description=f"Test Product {i}",
                stock_level=100,
                daily_demand=10,
                profit_per_unit=50.0,
                holding_cost_per_unit_day=0.15,
                turnover_ratio=2.5,
                size_score=3.0,
                position=Position3D(x=20.0 + i*5, y=30.0, z=2.0)
            )
            for i in range(3)
        ]
        
        router = CostOptimizedRouter(self.warehouse)
        routes = [
            router.find_optimal_route(product, product.position, operation="retrieve")
            for product in products
        ]
        
        stats = self.reporter.generate_summary_statistics(routes)
        
        assert stats is not None
        assert 'total_routes' in stats
        assert 'total_cost' in stats
        assert 'average_cost' in stats
        assert stats['total_routes'] == 3
        assert stats['total_cost'] > 0
        assert stats['average_cost'] > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
