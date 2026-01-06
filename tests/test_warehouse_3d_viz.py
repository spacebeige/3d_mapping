"""
Test for warehouse 3D visualization to ensure no ValueError with marker symbols.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_warehouse_3d_visualization_with_products():
    """
    Test that warehouse 3D visualization works without ValueError.
    This specifically tests the fix for the 'cube' symbol issue.
    """
    print("\n🧪 Testing warehouse 3D visualization with products...")
    
    try:
        from main import WarehouseDigitalTwin, generate_sample_data
        
        # Create twin
        twin = WarehouseDigitalTwin()
        
        # Create warehouse
        warehouse = twin.create_warehouse(
            name="Distribution Center",
            length=50.0,  # Using smaller size for faster test
            width=40.0,
            height=12.0,
            num_aisles=5,
            aisle_width=3.0
        )
        
        # Generate sample data
        products_df = generate_sample_data(100)  # Using fewer products for faster test
        
        # Train optimizer
        twin.train_optimizer(products_df)
        
        # Optimize allocation
        results = twin.optimize_allocation(products_df)
        
        # This is the critical test - it should not raise ValueError
        fig = twin.visualize_warehouse_3d()
        
        # Verify the figure was created
        assert fig is not None
        assert hasattr(fig, 'data')
        assert len(fig.data) > 0
        
        # Verify that products were added (there should be traces with products)
        product_traces = [trace for trace in fig.data if 'Products Zone' in trace.name]
        
        # Check that product traces have the correct marker symbol
        for trace in product_traces:
            if hasattr(trace, 'marker') and hasattr(trace.marker, 'symbol'):
                # The symbol should be 'square', not 'cube'
                assert trace.marker.symbol == 'square', f"Expected 'square' but got '{trace.marker.symbol}'"
        
        print("   ✅ Warehouse 3D visualization works correctly")
        print(f"   📊 Figure has {len(fig.data)} traces")
        print(f"   📊 Product traces: {len(product_traces)}")
        
        return True
        
    except ValueError as e:
        if "'cube'" in str(e) or "symbol" in str(e):
            print(f"   ❌ ValueError with marker symbol: {e}")
            print("   This indicates the 'cube' -> 'square' fix was not applied correctly")
            return False
        else:
            # Re-raise if it's a different ValueError
            raise
            
    except Exception as e:
        print(f"   ❌ Test failed with unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_warehouse_3d_without_products():
    """
    Test warehouse 3D visualization without products (should still work).
    """
    print("\n🧪 Testing warehouse 3D visualization without products...")
    
    try:
        from main import WarehouseDigitalTwin
        
        # Create twin
        twin = WarehouseDigitalTwin()
        
        # Create warehouse
        warehouse = twin.create_warehouse(
            name="Empty Warehouse",
            length=30.0,
            width=20.0,
            height=10.0,
            num_aisles=3,
            aisle_width=3.0
        )
        
        # Create visualization without products
        fig = twin.visualize_warehouse_3d(show_products=False)
        
        # Verify the figure was created
        assert fig is not None
        assert hasattr(fig, 'data')
        
        print("   ✅ Warehouse 3D visualization without products works correctly")
        print(f"   📊 Figure has {len(fig.data)} traces")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run the 3D visualization tests"""
    print("=" * 60)
    print("🏭 WAREHOUSE 3D VISUALIZATION TEST")
    print("=" * 60)
    
    tests = [
        ("3D Viz with Products", test_warehouse_3d_visualization_with_products),
        ("3D Viz without Products", test_warehouse_3d_without_products),
    ]
    
    results = []
    
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ {name} crashed: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
    
    print("\n" + "=" * 60)
    print(f"Result: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed!")
        return 0
    else:
        print("⚠️  Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
