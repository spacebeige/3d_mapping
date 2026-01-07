"""
CSV Upload Demo - Complete Integration Example

Demonstrates:
1. Loading CSV data
2. Creating warehouse with multi-access points
3. Allocating products to racks/shelves
4. Finding optimal routes
5. Creating visualizations
6. Generating reports
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import WarehouseDigitalTwin
from utils.csv_loader import CSVLoader
from utils.cost_reporter import CostReporter
from routing.cost_optimizer import CostOptimizedRouter
from viz.movement_animation import MovementAnimator
from viz.rack_detail import RackDetailVisualizer


def main():
    """Run complete CSV upload demo"""
    
    print("=" * 80)
    print("🏭 CSV UPLOAD & COST-OPTIMIZED ROUTING DEMO")
    print("=" * 80)
    print()
    
    # 1. Load CSV data
    print("📁 Step 1: Loading CSV data...")
    csv_loader = CSVLoader()
    
    try:
        products = csv_loader.load_products("test_data_unseen_expanded.csv")
        print(f"✅ Loaded {len(products)} products")
        
        # Show statistics
        stats = csv_loader.get_statistics()
        print(f"\n📊 Statistics:")
        print(f"   Total Products: {stats['total_products']}")
        print(f"   Total Stock: {stats['total_stock']:,} units")
        print(f"   Total Daily Demand: {stats['total_demand']:.1f} units/day")
        print(f"   Zones: {dict(stats['zones'])}")
        print(f"   Categories: {len(stats['categories'])}")
    except FileNotFoundError:
        print("⚠️ CSV file not found. Using sample products...")
        from main import generate_sample_data
        import pandas as pd
        
        # Generate sample data and convert to products
        df = generate_sample_data(20)
        products = []
        for _, row in df.iterrows():
            from models.warehouse import Product, ZoneType, Position3D
            product = Product(
                item_id=row['item_id'],
                category=row['category'],
                description=row['description'],
                stock_level=row['stock_level'],
                daily_demand=row['daily_demand'],
                profit_per_unit=50.0,
                holding_cost_per_unit_day=0.15,
                turnover_ratio=2.5,
                size_score=3.0,
                predicted_zone=ZoneType.B,
                position=Position3D(x=10, y=10, z=2)
            )
            products.append(product)
        print(f"✅ Generated {len(products)} sample products")
    
    print()
    
    # 2. Create warehouse with multi-access points
    print("🏗️ Step 2: Creating warehouse with multi-access points...")
    twin = WarehouseDigitalTwin()
    warehouse = twin.create_warehouse(
        name="Multi-Access Distribution Center",
        length=200.0,
        width=150.0,
        height=12.0,
        num_aisles=50,
        aisle_width=3.0
    )
    
    # Add default access points
    warehouse.add_default_access_points()
    
    print(f"✅ Warehouse created:")
    print(f"   Dimensions: {warehouse.dimensions.width}m × {warehouse.warehouse_length}m × {warehouse.dimensions.height}m")
    print(f"   Entry Points: {len(warehouse.entry_points)}")
    print(f"   Exit Points: {len(warehouse.exit_points)}")
    
    # List access points
    print(f"\n📍 Entry Points:")
    for entry in warehouse.entry_points:
        print(f"   - {entry.name}: ${entry.base_cost:.2f}, {entry.capacity_per_hour}/hr, {entry.capabilities}")
    
    print(f"\n📍 Exit Points:")
    for exit_point in warehouse.exit_points:
        print(f"   - {exit_point.name}: ${exit_point.base_cost:.2f}, {exit_point.capacity_per_hour}/hr, {exit_point.capabilities}")
    
    print()
    
    # 3. Allocate products to racks/shelves (simplified - products already have positions)
    print("📦 Step 3: Products already allocated via CSV storage_location_id")
    print(f"   Total products: {len(products)}")
    print()
    
    # 4. Find optimal routes for sample products
    print("🚀 Step 4: Finding optimal routes...")
    router = CostOptimizedRouter(warehouse)
    
    sample_products = products[:min(10, len(products))]  # First 10 products
    routes = []
    
    print(f"\n💰 Cost-Optimized Routes:")
    print("-" * 80)
    
    for product in sample_products:
        route = router.find_optimal_route(
            product=product,
            start_position=product.position,
            operation="retrieve"
        )
        routes.append(route)
        
        exit_name = route.exit_point.name if route.exit_point else "N/A"
        print(f"{product.item_id} ({product.category}):")
        print(f"  → Exit: {exit_name}")
        print(f"  → Distance: {route.total_distance:.1f}m")
        print(f"  → Total Cost: ${route.total_cost:.2f}")
        print(f"     - Base: ${route.base_distance_cost:.2f}")
        print(f"     - Weight: ${route.weight_cost:.2f}")
        print(f"     - Fragility: ${route.fragility_cost:.2f}")
        print(f"     - Size: ${route.size_cost:.2f}")
        print(f"     - Access Point: ${route.access_point_cost:.2f}")
        print(f"     - Handling: ${route.handling_cost:.2f}")
        print(f"     - Time: ${route.time_cost:.2f}")
        print()
    
    print("✅ Routes calculated")
    print()
    
    # 5. Create visualizations
    print("🎨 Step 5: Creating visualizations...")
    
    # 5a. 3D warehouse with products and access points
    print("   📊 Generating 3D warehouse visualization...")
    from viz.warehouse_3d import Warehouse3DVisualizer
    
    visualizer = Warehouse3DVisualizer(warehouse)
    fig_3d = visualizer.create_visualization(
        products=products,
        show_products=True,
        show_access_points=True,
        show_cost_heatmap=True,
        max_products_display=100
    )
    fig_3d.write_html("warehouse_3d_multi_access.html")
    print("   ✅ Saved: warehouse_3d_multi_access.html")
    
    # 5b. Animated movement for sample product
    if routes:
        print("   🎬 Generating product movement animation...")
        animator = MovementAnimator()
        fig_anim = animator.animate_product_movement(
            product=sample_products[0],
            route=routes[0],
            warehouse_config=warehouse,
            duration_seconds=5.0
        )
        fig_anim.write_html("product_movement_animation.html")
        print("   ✅ Saved: product_movement_animation.html")
    
    # 5c. Cost analysis report
    print("   📋 Generating shipping cost report...")
    reporter = CostReporter(warehouse)
    cost_df = reporter.generate_shipping_report(sample_products, routes)
    cost_df.to_csv("shipping_cost_report.csv", index=False)
    print("   ✅ Saved: shipping_cost_report.csv")
    
    # Print summary
    print(f"\n   📊 Cost Summary:")
    summary = reporter.generate_summary_statistics(routes)
    print(f"      Total Routes: {summary.get('total_routes', 0)}")
    print(f"      Total Cost: ${summary.get('total_cost', 0):.2f}")
    print(f"      Average Cost: ${summary.get('average_cost', 0):.2f}")
    print(f"      Min Cost: ${summary.get('min_cost', 0):.2f}")
    print(f"      Max Cost: ${summary.get('max_cost', 0):.2f}")
    
    # 5d. Cost heatmap
    print("   🗺️ Generating cost heatmap...")
    fig_heatmap = reporter.create_cost_heatmap(products[:50], routes[:50] if len(routes) >= 50 else routes)
    fig_heatmap.write_html("cost_heatmap.html")
    print("   ✅ Saved: cost_heatmap.html")
    
    # 5e. Cost breakdown chart
    if len(routes) >= 3:
        print("   📊 Generating cost breakdown chart...")
        fig_breakdown = reporter.create_cost_breakdown_chart(routes)
        fig_breakdown.write_html("cost_breakdown.html")
        print("   ✅ Saved: cost_breakdown.html")
    
    # 5f. Rack detail view (if warehouse has racks)
    if warehouse.storage_systems:
        print("   🗂️ Generating rack detail view...")
        rack_viz = RackDetailVisualizer(warehouse)
        try:
            fig_rack = rack_viz.visualize_rack(
                warehouse.storage_systems[0].id,
                products
            )
            fig_rack.write_html("rack_detail.html")
            print("   ✅ Saved: rack_detail.html")
        except Exception as e:
            print(f"   ⚠️ Rack detail view skipped: {e}")
    
    print()
    print("=" * 80)
    print("✅ DEMO COMPLETE!")
    print("=" * 80)
    print("\n📁 Generated Files:")
    print("   - warehouse_3d_multi_access.html  (3D warehouse with access points)")
    print("   - product_movement_animation.html  (Animated product movement)")
    print("   - shipping_cost_report.csv         (Cost analysis CSV)")
    print("   - cost_heatmap.html                (3D cost heatmap)")
    print("   - cost_breakdown.html              (Cost breakdown chart)")
    print("   - rack_detail.html                 (Detailed rack view)")
    print()
    print("💡 Open the HTML files in your web browser to view the visualizations!")
    print()


if __name__ == "__main__":
    main()
