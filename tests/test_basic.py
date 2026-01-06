"""
Quick test script to verify installation and basic functionality.
"""

import sys


def test_imports():
    """Test that all modules can be imported"""
    print("🧪 Testing imports...")
    
    try:
        from models import (
            WarehouseConfig, Product, ZoneType,
            WarehouseLocation, Route, AGV
        )
        print("   ✅ Models imported")
    except Exception as e:
        print(f"   ❌ Models import failed: {e}")
        return False
    
    try:
        from optimization import WarehouseAllocator, ProductClusterer
        print("   ✅ Optimization imported")
    except Exception as e:
        print(f"   ❌ Optimization import failed: {e}")
        return False
    
    try:
        from viz import Warehouse3DVisualizer, WarehouseCharts
        print("   ✅ Visualization imported")
    except Exception as e:
        print(f"   ❌ Visualization import failed: {e}")
        return False
    
    try:
        from geo import Map3DGenerator
        print("   ✅ Geospatial imported")
    except Exception as e:
        print(f"   ❌ Geospatial import failed: {e}")
        return False
    
    try:
        from core import PathfindingGrid
        print("   ✅ Core imported")
    except Exception as e:
        print(f"   ❌ Core import failed: {e}")
        return False
    
    try:
        from utils import WarehouseGenerator
        print("   ✅ Utils imported")
    except Exception as e:
        print(f"   ❌ Utils import failed: {e}")
        return False
    
    return True


def test_basic_functionality():
    """Test basic functionality"""
    print("\n🧪 Testing basic functionality...")
    
    try:
        from main import WarehouseDigitalTwin, generate_sample_data
        
        # Create twin
        twin = WarehouseDigitalTwin()
        print("   ✅ Digital Twin created")
        
        # Create small warehouse
        warehouse = twin.create_warehouse(
            name="Test Warehouse",
            length=50,
            width=30,
            height=10,
            num_aisles=4
        )
        print("   ✅ Warehouse created")
        
        # Generate sample data
        data = generate_sample_data(100)
        print("   ✅ Sample data generated")
        
        # Train
        twin.train_optimizer(data)
        print("   ✅ Optimizer trained")
        
        # Optimize
        results = twin.optimize_allocation(data)
        print("   ✅ Allocation optimized")
        
        # Check results
        assert len(results) == 100
        assert "final_zone" in results.columns
        print("   ✅ Results validated")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Basic functionality test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_scalability():
    """Test scalability with large warehouse"""
    print("\n🧪 Testing scalability...")
    
    try:
        from utils import WarehouseGenerator
        
        # Test large warehouse creation
        capacity = WarehouseGenerator.estimate_capacity(
            length=200,
            width=150,
            height=12,
            num_aisles=10000
        )
        
        print(f"   📊 Estimated capacity for 10,000 aisles:")
        print(f"      Usable volume: {capacity['usable_volume_m3']:,.0f} m³")
        print(f"      Shelves: {capacity['estimated_shelves']:,}")
        print("   ✅ Scalability test passed")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Scalability test failed: {e}")
        return False


def test_models_validation():
    """Test Pydantic model validation"""
    print("\n🧪 Testing model validation...")
    
    try:
        from models import Dimensions3D, Position3D, Shelf
        
        # Test valid data
        dim = Dimensions3D(width=10, depth=2, height=8)
        pos = Position3D(x=5, y=10, z=0)
        shelf = Shelf(
            id="A1-R1-L1-S1",
            aisle_id="aisle_1",
            rack_id="rack_1",
            level_number=1,
            position_in_rack=1,
            capacity=1.5,
            max_load_kg=1000
        )
        
        print("   ✅ Valid models created")
        
        # Test validation
        try:
            invalid_dim = Dimensions3D(width=-10, depth=2, height=8)
            print("   ❌ Validation should have failed")
            return False
        except:
            print("   ✅ Validation working correctly")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Model validation test failed: {e}")
        return False


def main():
    """Run all tests"""
    print("=" * 60)
    print("🏭 WAREHOUSE DIGITAL TWIN - TEST SUITE")
    print("=" * 60)
    
    tests = [
        ("Import Test", test_imports),
        ("Basic Functionality", test_basic_functionality),
        ("Scalability Test", test_scalability),
        ("Model Validation", test_models_validation),
    ]
    
    results = []
    
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ {name} crashed: {e}")
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
