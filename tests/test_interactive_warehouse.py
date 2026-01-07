"""
Tests for interactive warehouse builder functionality.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from interactive_warehouse import assign_position, determine_zone
from models import ZoneType, Position3D


def test_assign_position_uniqueness():
    """Test that assign_position generates unique positions for different products"""
    print("🧪 Testing position uniqueness...")
    
    warehouse_config = {
        'length': 100,
        'width': 80,
        'height': 10,
        'aisles': 10
    }
    
    positions = []
    for i in range(50):
        pos = assign_position(
            i,
            warehouse_config['aisles'],
            warehouse_config['length'],
            warehouse_config['width'],
            warehouse_config['height']
        )
        positions.append((pos.x, pos.y, pos.z))
    
    # Check uniqueness
    unique_positions = set(positions)
    if len(unique_positions) == len(positions):
        print(f"   ✅ All {len(positions)} positions are unique")
        return True
    else:
        print(f"   ❌ Found duplicates: {len(positions)} positions, {len(unique_positions)} unique")
        return False


def test_assign_position_within_bounds():
    """Test that positions stay within warehouse boundaries"""
    print("🧪 Testing position boundaries...")
    
    warehouse_length = 100
    warehouse_width = 80
    warehouse_height = 10
    num_aisles = 10
    
    # Test first 20 products
    for i in range(20):
        pos = assign_position(i, num_aisles, warehouse_length, warehouse_width, warehouse_height)
        
        # Check bounds
        if not (0 <= pos.x <= warehouse_width):
            print(f"   ❌ X position {pos.x} out of bounds [0, {warehouse_width}]")
            return False
        if not (0 <= pos.y <= warehouse_length):
            print(f"   ❌ Y position {pos.y} out of bounds [0, {warehouse_length}]")
            return False
        if not (0 <= pos.z <= warehouse_height):
            print(f"   ❌ Z position {pos.z} out of bounds [0, {warehouse_height}]")
            return False
    
    print(f"   ✅ All positions within warehouse bounds")
    return True


def test_assign_position_distribution():
    """Test that products are distributed across aisles, racks, and shelves"""
    print("🧪 Testing position distribution...")
    
    warehouse_config = {
        'length': 100,
        'width': 80,
        'height': 10,
        'aisles': 5
    }
    
    # Calculate capacity per aisle to ensure we test multiple aisles
    racks_per_aisle = max(10, int(warehouse_config['length'] / 5))
    usable_height = warehouse_config['height'] * 0.8
    shelves_per_rack = max(3, int(usable_height / 1.6))
    products_per_aisle = racks_per_aisle * shelves_per_rack
    
    # Test enough products to spread across multiple aisles
    num_products = products_per_aisle * 2 + 10
    positions = []
    for i in range(num_products):
        pos = assign_position(
            i,
            warehouse_config['aisles'],
            warehouse_config['length'],
            warehouse_config['width'],
            warehouse_config['height']
        )
        positions.append(pos)
    
    # Check that we have different X values (different aisles)
    x_values = set(pos.x for pos in positions)
    if len(x_values) < 2:
        print(f"   ❌ Products not distributed across aisles: only {len(x_values)} unique X values")
        return False
    
    # Check that we have different Y values (different racks)
    y_values = set(pos.y for pos in positions)
    if len(y_values) < 2:
        print(f"   ❌ Products not distributed across racks: only {len(y_values)} unique Y values")
        return False
    
    # Check that we have different Z values (different shelves)
    z_values = set(pos.z for pos in positions)
    if len(z_values) < 2:
        print(f"   ❌ Products not distributed across shelves: only {len(z_values)} unique Z values")
        return False
    
    print(f"   ✅ Products distributed across {len(x_values)} aisles, {len(y_values)} racks, {len(z_values)} shelves")
    return True


def test_assign_position_edge_cases():
    """Test edge cases like 0 products or very large product counts"""
    print("🧪 Testing edge cases...")
    
    # Test with single product
    pos = assign_position(0, 10, 100, 80, 10)
    if not isinstance(pos, Position3D):
        print("   ❌ Failed for single product")
        return False
    
    # Test with large product count
    try:
        pos = assign_position(10000, 10, 200, 150, 12)
        if not isinstance(pos, Position3D):
            print("   ❌ Failed for large product count")
            return False
    except Exception as e:
        print(f"   ❌ Exception for large product count: {e}")
        return False
    
    print("   ✅ Edge cases handled correctly")
    return True


def test_determine_zone_boundaries():
    """Test zone assignment for boundary values"""
    print("🧪 Testing zone boundary values...")
    
    test_cases = [
        # (demand, expected_zone)
        (5, ZoneType.D),      # Low demand
        (10, ZoneType.D),     # Exactly at boundary (10)
        (10.1, ZoneType.C),   # Just above boundary
        (20, ZoneType.C),     # Exactly at boundary (20)
        (20.1, ZoneType.B),   # Just above boundary
        (50, ZoneType.B),     # Exactly at boundary (50)
        (50.1, ZoneType.A),   # Just above boundary
        (100, ZoneType.A),    # High demand
    ]
    
    all_passed = True
    for demand, expected_zone in test_cases:
        result = determine_zone(demand)
        if result == expected_zone:
            print(f"   ✅ Demand {demand} → Zone {result.value} (correct)")
        else:
            print(f"   ❌ Demand {demand} → Zone {result.value} (expected {expected_zone.value})")
            all_passed = False
    
    return all_passed


def test_determine_zone_typical_values():
    """Test zone assignment for typical values in each range"""
    print("🧪 Testing typical zone values...")
    
    test_cases = [
        # (demand, expected_zone)
        (1, ZoneType.D),
        (15, ZoneType.C),
        (35, ZoneType.B),
        (75, ZoneType.A),
    ]
    
    all_passed = True
    for demand, expected_zone in test_cases:
        result = determine_zone(demand)
        if result == expected_zone:
            print(f"   ✅ Demand {demand} → Zone {result.value} (correct)")
        else:
            print(f"   ❌ Demand {demand} → Zone {result.value} (expected {expected_zone.value})")
            all_passed = False
    
    return all_passed


def run_all_tests():
    """Run all tests"""
    print("=" * 60)
    print("🧪 INTERACTIVE WAREHOUSE TESTS")
    print("=" * 60)
    print()
    
    results = []
    
    # Position assignment tests
    results.append(("Position Uniqueness", test_assign_position_uniqueness()))
    results.append(("Position Boundaries", test_assign_position_within_bounds()))
    results.append(("Position Distribution", test_assign_position_distribution()))
    results.append(("Position Edge Cases", test_assign_position_edge_cases()))
    
    # Zone determination tests
    results.append(("Zone Boundary Values", test_determine_zone_boundaries()))
    results.append(("Zone Typical Values", test_determine_zone_typical_values()))
    
    print()
    print("=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print()
    print(f"Results: {passed}/{total} tests passed")
    print("=" * 60)
    
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
