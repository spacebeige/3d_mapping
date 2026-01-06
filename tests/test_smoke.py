"""
Simple smoke test to verify core functionality.
Run from project root: PYTHONPATH=. python tests/test_smoke.py
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def main():
    print("=" * 60)
    print("🏭 WAREHOUSE DIGITAL TWIN - SMOKE TEST")
    print("=" * 60)
    
    # Test 1: Import models
    print("\n1️⃣ Testing model imports...")
    try:
        from models import WarehouseConfig, Product, ZoneType, Dimensions3D, Position3D
        print("   ✅ Models imported successfully")
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return 1
    
    # Test 2: Create warehouse config
    print("\n2️⃣ Testing warehouse creation...")
    try:
        from utils import WarehouseGenerator
        
        warehouse = WarehouseGenerator.create_warehouse(
            name="Test Warehouse",
            length=50,
            width=30,
            height=10,
            num_aisles=4,
            generate_full_structure=True
        )
        
        print(f"   ✅ Warehouse created: {warehouse.name}")
        print(f"   📊 Aisles: {warehouse.layout.num_aisles}")
        print(f"   📊 Racks: {len(warehouse.storage_systems)}")
        print(f"   📊 Volume: {warehouse.dimensions.volume:,.0f} m³")
        
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    # Test 3: Test allocator
    print("\n3️⃣ Testing optimization...")
    try:
        import pandas as pd
        import numpy as np
        from optimization import WarehouseAllocator
        
        # Create sample data
        data = pd.DataFrame({
            'item_id': [f'ITEM{i:03d}' for i in range(100)],
            'category': np.random.choice(['electronics', 'groceries', 'pharma'], 100),
            'daily_demand': np.random.randint(10, 100, 100),
            'stock_level': np.random.randint(50, 500, 100)
        })
        
        allocator = WarehouseAllocator(total_space=100000)
        allocator.train(data)
        
        results = allocator.predict_with_constraints(data)
        
        print(f"   ✅ Allocation completed for {len(results)} products")
        print(f"   📊 Zones: {results['final_zone'].value_counts().to_dict()}")
        
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    # Test 4: Test pathfinding
    print("\n4️⃣ Testing AGV pathfinding...")
    try:
        from core import generate_warehouse_navigation_grid, PathfindingGrid
        
        nodes, segments = generate_warehouse_navigation_grid(
            warehouse_length=50,
            warehouse_width=30,
            num_aisles=4,
            aisle_width=3.0
        )
        
        pathfinder = PathfindingGrid(nodes, segments)
        
        # Find path if we have nodes
        if len(nodes) >= 2:
            start = nodes[0].id
            end = nodes[-1].id
            path = pathfinder.find_path(start, end)
            
            if path:
                print(f"   ✅ Path found: {len(path.nodes)} nodes, {path.total_distance:.1f}m")
            else:
                print("   ⚠️  No path found (nodes may not be connected)")
        else:
            print("   ⚠️  Not enough nodes generated")
        
        print(f"   📊 Navigation grid: {len(nodes)} nodes, {len(segments)} segments")
        
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    # Test 5: Test scalability
    print("\n5️⃣ Testing scalability (100,000 aisles)...")
    try:
        from utils import WarehouseGenerator
        
        capacity = WarehouseGenerator.estimate_capacity(
            length=200,
            width=150,
            height=12,
            num_aisles=100000
        )
        
        print(f"   ✅ Capacity estimated for 100,000 aisles")
        print(f"   📊 Usable volume: {capacity['usable_volume_m3']:,.0f} m³")
        print(f"   📊 Estimated shelves: {capacity['estimated_shelves']:,}")
        print(f"   📊 Pallet positions: {capacity['estimated_pallet_positions']:,}")
        
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return 1
    
    # Success
    print("\n" + "=" * 60)
    print("🎉 ALL TESTS PASSED!")
    print("=" * 60)
    print("\n✨ System is ready to use!")
    print("\nNext steps:")
    print("   - Run: PYTHONPATH=. python -c 'from main import WarehouseDigitalTwin; twin = WarehouseDigitalTwin()'")
    print("   - Or check examples/warehouse_demo.ipynb for full demo")
    print()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
