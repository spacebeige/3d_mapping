#!/usr/bin/env python3
"""
Demo script to showcase zone-based warehouse allocation with 3D visualization.
Shows how high-profit items are allocated to Zone A (near entry) and 
low-turnover items to Zone D (far back).
"""

from main import WarehouseDigitalTwin, generate_sample_data
import pandas as pd
import numpy as np
import os
import tempfile

def demo_zone_allocation():
    """Demonstrate zone-based allocation with clear examples."""
    
    print("=" * 70)
    print("🏭 WAREHOUSE ZONE ALLOCATION DEMO")
    print("=" * 70)
    
    # Create twin with larger warehouse to accommodate more items
    twin = WarehouseDigitalTwin()
    warehouse = twin.create_warehouse(
        name="Demo Distribution Center",
        length=100.0,  # Larger warehouse
        width=80.0,
        height=12.0,
        num_aisles=8,
        aisle_width=3.0
    )
    
    # Generate strategic sample data with clear distinctions
    print("\n📦 Generating strategic product mix...")
    
    # Create products with different characteristics
    products = []
    
    # Zone A candidates: High-profit, high-demand items
    for i in range(20):
        products.append({
            'item_id': f'A-ITEM-{i:03d}',
            'category': 'electronics',
            'daily_demand': np.random.randint(50, 100),
            'stock_level': np.random.randint(100, 300),
            'description': f'High-value electronic item {i}'
        })
    
    # Zone B candidates: Medium-profit items
    for i in range(25):
        products.append({
            'item_id': f'B-ITEM-{i:03d}',
            'category': 'apparel',
            'daily_demand': np.random.randint(20, 50),
            'stock_level': np.random.randint(80, 200),
            'description': f'Medium-value apparel item {i}'
        })
    
    # Zone C candidates: Bulky items
    for i in range(15):
        products.append({
            'item_id': f'C-ITEM-{i:03d}',
            'category': 'automotive',
            'daily_demand': np.random.randint(5, 20),
            'stock_level': np.random.randint(50, 150),
            'description': f'Bulky automotive item {i}'
        })
    
    # Zone D candidates: Low-turnover items
    for i in range(20):
        products.append({
            'item_id': f'D-ITEM-{i:03d}',
            'category': 'pharma',
            'daily_demand': np.random.randint(1, 10),
            'stock_level': np.random.randint(200, 500),
            'description': f'Long-term storage item {i}'
        })
    
    products_df = pd.DataFrame(products)
    
    # Train and optimize
    print("\n🎓 Training allocation optimizer...")
    twin.train_optimizer(products_df)
    
    print("\n⚙️ Optimizing warehouse allocation...")
    results = twin.optimize_allocation(products_df)
    
    # Analyze results
    print("\n" + "=" * 70)
    print("📊 ALLOCATION RESULTS")
    print("=" * 70)
    
    # Zone distribution
    print("\n🏷️  Zone Distribution:")
    zone_counts = results['final_zone'].value_counts().sort_index()
    for zone, count in zone_counts.items():
        print(f"   Zone {zone}: {count} items")
    
    # Analyze each zone
    print("\n💡 Zone Analysis:")
    for zone in ['A', 'B', 'C', 'D']:
        zone_data = results[results['final_zone'] == zone]
        if len(zone_data) > 0:
            avg_profit = zone_data['profit_per_unit'].mean()
            avg_demand = zone_data['daily_demand'].mean()
            avg_size = zone_data['size_score'].mean()
            
            print(f"\n   Zone {zone} ({len(zone_data)} items):")
            print(f"      Avg Profit: ₹{avg_profit:.2f}")
            print(f"      Avg Daily Demand: {avg_demand:.1f}")
            print(f"      Avg Size Score: {avg_size:.1f}")
            
            # Show zone purpose
            zone_purpose = {
                'A': '🎯 High-Value, High-Turnover (Near Entry)',
                'B': '📦 Medium-Value (Middle Area)',
                'C': '📦 Bulky Items (Back-Middle)',
                'D': '🗄️  Long-Term Storage (Far Back)'
            }
            print(f"      Purpose: {zone_purpose.get(zone, 'N/A')}")
    
    # Show sample allocations
    print("\n" + "=" * 70)
    print("📋 SAMPLE ALLOCATIONS")
    print("=" * 70)
    
    for zone in ['A', 'B', 'C', 'D']:
        zone_items = results[results['final_zone'] == zone].head(3)
        if len(zone_items) > 0:
            print(f"\n🔹 Zone {zone} Sample:")
            for _, item in zone_items.iterrows():
                print(f"   • {item['item_id']}: {item['description']}")
                print(f"     Profit: ₹{item['profit_per_unit']:.2f} | Demand: {item['daily_demand']}/day")
    
    # Create 3D visualization
    print("\n" + "=" * 70)
    print("🎨 Generating 3D Warehouse Visualization...")
    print("=" * 70)
    
    fig = twin.visualize_warehouse_3d(show_products=True, max_products=500)
    
    print("\n✅ Visualization created successfully!")
    print("\n📊 Visualization Features:")
    print("   • Zone A (Green): High-value items near entry (0-30% length)")
    print("   • Zone B (Blue): Medium-value items in middle (30-60% length)")
    print("   • Zone C (Orange): Bulky items in back-middle (60-80% length)")
    print("   • Zone D (Red): Long-term storage in far back (80-100% length)")
    print("   • Entry path (Green diamond): Main warehouse entrance")
    print("   • Exit path (Red diamond): Main warehouse exit")
    
    print("\n💾 Saving visualization...")
    
    # Use tempfile for cross-platform compatibility
    output_dir = tempfile.gettempdir()
    output_path = os.path.join(output_dir, "warehouse_zone_allocation_demo.html")
    
    fig.write_html(output_path)
    print(f"   Saved to: {output_path}")
    
    print("\n" + "=" * 70)
    print("✅ DEMO COMPLETE!")
    print("=" * 70)
    
    return twin, results, fig

if __name__ == "__main__":
    twin, results, fig = demo_zone_allocation()
