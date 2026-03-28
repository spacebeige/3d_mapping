#!/usr/bin/env python3
"""
Interactive Warehouse Builder

This script provides an interactive command-line interface for:
1. Defining warehouse dimensions
2. Adding products with automatic position assignment
3. Generating 3D visualizations
4. Saving all data to files

Each product gets a unique ID and position automatically!
"""

import sys
import traceback
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from main import WarehouseDigitalTwin
from models import Product, ZoneType, Position3D
import pandas as pd
import warnings

warnings.filterwarnings('ignore')


def assign_position(product_index, total_aisles, warehouse_length, warehouse_width, warehouse_height):
    """
    Assign a unique position to each product based on its index.
    Distributes products evenly across aisles, racks, and shelves.
    
    Args:
        product_index: Index of the product (0-based)
        total_aisles: Total number of aisles in warehouse
        warehouse_length: Length of warehouse in meters
        warehouse_width: Width of warehouse in meters
        warehouse_height: Height of warehouse in meters
        
    Returns:
        Position3D object with unique coordinates
    """
    # Calculate configuration based on warehouse dimensions
    # More racks for longer warehouses (1 rack per 5m of length)
    racks_per_aisle = max(10, int(warehouse_length / 5))
    
    # More shelves for taller warehouses (1 shelf per 1.6m of usable height)
    usable_height = warehouse_height * 0.8  # 80% of height is usable
    shelves_per_rack = max(3, int(usable_height / 1.6))
    
    # Products capacity per aisle
    products_per_aisle = racks_per_aisle * shelves_per_rack
    
    # Calculate which aisle, rack, and shelf
    aisle_num = (product_index // products_per_aisle) % total_aisles
    rack_num = (product_index % products_per_aisle) // shelves_per_rack
    shelf_num = product_index % shelves_per_rack
    
    # Calculate 3D position
    aisle_spacing = warehouse_width / (total_aisles + 1)
    x = aisle_spacing * (aisle_num + 1)
    
    rack_spacing = warehouse_length / racks_per_aisle
    y = rack_spacing * (rack_num + 0.5)
    
    shelf_height = usable_height / shelves_per_rack
    z = shelf_height * (shelf_num + 0.5)
    
    return Position3D(x=x, y=y, z=z)


def determine_zone(daily_demand):
    """
    Determine warehouse zone based on daily demand.
    High demand products go to Zone A (closest to exits).
    
    Args:
        daily_demand: Daily demand for the product
        
    Returns:
        ZoneType enum
    """
    if daily_demand > 50:
        return ZoneType.A
    elif daily_demand > 20:
        return ZoneType.B
    elif daily_demand > 10:
        return ZoneType.C
    else:
        return ZoneType.D


def get_warehouse_dimensions():
    """Get warehouse dimensions from user"""
    print("🏗️ WAREHOUSE CONFIGURATION")
    print("=" * 50)
    
    warehouse_name = input("Enter warehouse name (default: My Distribution Center): ").strip() or "My Distribution Center"

    def _prompt_float(prompt: str) -> float:
        """Prompt user for a positive float without falling back to defaults"""
        while True:
            raw_value = input(prompt).strip()
            if not raw_value:
                print("❌ A value is required. Please enter a number.")
                continue
            try:
                value = float(raw_value)
                if value <= 0:
                    print("❌ Please enter a positive number.")
                    continue
                return value
            except ValueError:
                print("❌ Invalid number. Please try again.")

    def _prompt_int(prompt: str) -> int:
        """Prompt user for a positive integer without falling back to defaults"""
        while True:
            raw_value = input(prompt).strip()
            if not raw_value:
                print("❌ A value is required. Please enter a whole number.")
                continue
            try:
                value = int(raw_value)
                if value <= 0:
                    print("❌ Please enter a positive integer.")
                    continue
                return value
            except ValueError:
                print("❌ Invalid number. Please try again.")

    length = _prompt_float("Enter warehouse length in meters: ")
    width = _prompt_float("Enter warehouse width in meters: ")
    height = _prompt_float("Enter warehouse height in meters: ")
    num_aisles = _prompt_int("Enter number of aisles: ")
    
    print("\n📊 Warehouse Configuration:")
    print(f"   Name: {warehouse_name}")
    print(f"   Dimensions: {length}m × {width}m × {height}m")
    print(f"   Aisles: {num_aisles}")
    print(f"   Volume: {length * width * height:,.0f} m³")
    
    return warehouse_name, length, width, height, num_aisles


def add_products(num_aisles, length, width, height):
    """
    Interactive product addition.
    
    Returns:
        List of Product objects
    """
    products = []
    product_counter = 1
    
    print("\n📦 PRODUCT INPUT")
    print("=" * 50)
    print("Enter product details. Type 'done' when finished.\n")
    
    while True:
        print(f"\n--- Product #{product_counter} ---")
        
        item_id = input(f"Product ID (default: PROD{product_counter:04d}, or 'done' to finish): ").strip()
        
        # Check if user wants to finish
        if item_id.lower() == 'done':
            break
        
        if not item_id:
            item_id = f"PROD{product_counter:04d}"
        
        category = input("Category (electronics/groceries/pharma/apparel/automotive): ").strip() or "electronics"
        description = input("Description: ").strip() or f"Product {product_counter}"
        
        try:
            stock_level = int(input("Stock level (default: 100): ") or "100")
            if stock_level < 0:
                print(f"⚠️ Stock level cannot be negative, using 0")
                stock_level = 0
            
            daily_demand = float(input("Daily demand (default: 10): ") or "10")
            if daily_demand < 0:
                print(f"⚠️ Daily demand cannot be negative, using 0")
                daily_demand = 0
        except ValueError as e:
            print(f"⚠️ Invalid number, using defaults: {e}")
            stock_level = 100
            daily_demand = 10
        
        # Assign unique position
        position = assign_position(
            product_counter - 1,
            num_aisles,
            length,
            width,
            height
        )
        
        # Determine zone based on demand
        zone = determine_zone(daily_demand)
        
        # Create product
        product = Product(
            item_id=item_id,
            category=category,
            description=description,
            stock_level=stock_level,
            daily_demand=daily_demand,
            profit_per_unit=50.0,
            holding_cost_per_unit_day=0.15,
            turnover_ratio=daily_demand / stock_level if stock_level > 0 else 0,
            size_score=3.0,
            predicted_zone=zone,
            position=position
        )
        
        products.append(product)
        
        print(f"\n✅ Product added!")
        print(f"   ID: {item_id}")
        print(f"   Position: ({position.x:.2f}, {position.y:.2f}, {position.z:.2f})")
        print(f"   Zone: {zone.value}")
        
        product_counter += 1
        
        # Ask if user wants to add more
        more = input("\nAdd another product? (y/n, default: y): ").strip().lower()
        if more == 'n':
            break
    
    print(f"\n✅ Total products added: {len(products)}")
    
    # Add sample products if none were added
    if len(products) == 0:
        print("\n⚠️ No products added. Adding sample products...")
        for i in range(5):
            position = assign_position(i, num_aisles, length, width, height)
            product = Product(
                item_id=f"PROD{i+1:04d}",
                category="electronics",
                description=f"Sample Product {i+1}",
                stock_level=100,
                daily_demand=15.0,
                profit_per_unit=50.0,
                holding_cost_per_unit_day=0.15,
                turnover_ratio=0.15,
                size_score=3.0,
                predicted_zone=ZoneType.B,
                position=position
            )
            products.append(product)
        print(f"✅ Added {len(products)} sample products")
    
    return products


def display_summary(products):
    """Display product summary"""
    product_data = []
    for p in products:
        product_data.append({
            'Product ID': p.item_id,
            'Category': p.category,
            'Description': p.description,
            'Stock': p.stock_level,
            'Daily Demand': p.daily_demand,
            'Zone': p.predicted_zone.value,
            'Position X': f"{p.position.x:.2f}",
            'Position Y': f"{p.position.y:.2f}",
            'Position Z': f"{p.position.z:.2f}"
        })
    
    df = pd.DataFrame(product_data)
    print("\n📋 PRODUCT SUMMARY")
    print("=" * 80)
    print(df.to_string(index=False))
    
    # Statistics
    print(f"\n📊 STATISTICS")
    print("=" * 50)
    print(f"Total Products: {len(products)}")
    print(f"Total Stock: {sum(p.stock_level for p in products):,} units")
    print(f"Total Daily Demand: {sum(p.daily_demand for p in products):.1f} units/day")
    print(f"\nZone Distribution:")
    zone_counts = {}
    for p in products:
        zone = p.predicted_zone.value
        zone_counts[zone] = zone_counts.get(zone, 0) + 1
    for zone, count in sorted(zone_counts.items()):
        print(f"  Zone {zone}: {count} products")
    
    return df


def generate_visualization(warehouse, products):
    """Generate and save 3D visualization"""
    from viz.warehouse_3d import Warehouse3DVisualizer
    
    print("\n🎨 Generating 3D warehouse visualization...")
    
    # Create visualizer
    visualizer = Warehouse3DVisualizer(warehouse)
    
    # Generate visualization
    fig = visualizer.create_visualization(
        products=products,
        show_products=True,
        max_products_display=len(products)  # Show all products
    )
    
    return fig


def save_files(fig, products_df, twin, products):
    """Save all generated files"""
    print("\n💾 Saving files...")
    
    # Save warehouse visualization
    fig.write_html("warehouse_3d.html")
    print("✅ Saved: warehouse_3d.html")
    
    # Save product data as CSV
    products_df.to_csv("products.csv", index=False)
    print("✅ Saved: products.csv")
    
    # Try to create dashboard
    if len(products) > 0:
        try:
            dashboard = twin.create_dashboard()
            dashboard.write_html("dashboard.html")
            print("✅ Saved: dashboard.html")
        except (AttributeError, ValueError, KeyError) as e:
            print(f"⚠️ Dashboard creation skipped: {e}")
        except Exception as e:
            print(f"⚠️ Dashboard creation failed with unexpected error: {type(e).__name__}")
            traceback.print_exc()
    
    print("\n📁 Files saved successfully!")
    print("   Open warehouse_3d.html in your web browser to view the 3D visualization")


def main():
    """Main execution flow"""
    print("=" * 60)
    print("🏭 INTERACTIVE WAREHOUSE DIGITAL TWIN BUILDER")
    print("=" * 60)
    print()
    
    # Step 1: Get warehouse dimensions
    warehouse_name, length, width, height, num_aisles = get_warehouse_dimensions()
    
    # Create warehouse
    print("\n🏗️ Creating warehouse...")
    twin = WarehouseDigitalTwin()
    warehouse = twin.create_warehouse(
        name=warehouse_name,
        length=length,
        width=width,
        height=height,
        num_aisles=num_aisles,
        aisle_width=3.0,
        rack_height=height * 0.8
    )
    print("✅ Warehouse created successfully!")
    
    # Step 2: Add products
    products = add_products(num_aisles, length, width, height)
    
    # Step 3: Display summary
    products_df = display_summary(products)
    
    # Load products into twin system
    twin_df = pd.DataFrame([{
        'item_id': p.item_id,
        'category': p.category,
        'description': p.description,
        'stock_level': p.stock_level,
        'daily_demand': p.daily_demand
    } for p in products])
    twin.load_products(twin_df)
    
    # Step 4: Generate visualization
    fig = generate_visualization(warehouse, products)
    
    # Step 5: Save files
    save_files(fig, products_df, twin, products)
    
    # Summary
    print("\n" + "=" * 60)
    print("🎉 WAREHOUSE DIGITAL TWIN CREATED SUCCESSFULLY!")
    print("=" * 60)
    print("\n✅ What you've created:")
    print(f"   • Warehouse: {warehouse_name}")
    print(f"   • Dimensions: {length}m × {width}m × {height}m")
    print(f"   • Aisles: {num_aisles}")
    print(f"   • Products: {len(products)}")
    print(f"   • Files: warehouse_3d.html, products.csv, dashboard.html")
    print("\n💡 Next steps:")
    print("   1. Open warehouse_3d.html in your browser")
    print("   2. Explore the 3D visualization (rotate, zoom, click)")
    print("   3. Check products.csv for all product data")
    print("   4. View dashboard.html for analytics")
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ Operation cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
