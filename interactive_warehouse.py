#!/usr/bin/env python3
"""
Interactive Warehouse Builder with GUI

This script provides an interactive GUI interface using ipywidgets for:
1. Defining warehouse dimensions via input widgets
2. Uploading CSV files or generating sample data
3. Generating 3D visualizations
4. Saving all data to files

Works in Jupyter notebooks, Google Colab, and VS Code notebooks!
"""

import sys
import traceback
import os
from pathlib import Path
import io
import tempfile

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from main import WarehouseDigitalTwin
from models import Product, ZoneType, Position3D
import pandas as pd
import warnings

warnings.filterwarnings('ignore')

# Try to import GUI components
try:
    import ipywidgets as widgets
    from IPython.display import display, HTML, clear_output
    GUI_AVAILABLE = True
except ImportError:
    GUI_AVAILABLE = False
    print("⚠️ ipywidgets not available. GUI will not work.")
    print("   Install with: pip install ipywidgets ipython")
    print("   For Jupyter Lab: jupyter labextension install @jupyter-widgets/jupyterlab-manager")

# Import CSV loader at module level
try:
    from utils.csv_loader import CSVLoader
    CSV_LOADER_AVAILABLE = True
except ImportError:
    CSV_LOADER_AVAILABLE = False


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


def create_gui():
    """
    Create interactive GUI for warehouse builder using ipywidgets.
    Works in Jupyter notebooks, Google Colab, and VS Code notebooks.
    """
    if not GUI_AVAILABLE:
        print("❌ GUI not available. Please install ipywidgets:")
        print("   pip install ipywidgets ipython")
        return
    
    # Output area for messages
    output = widgets.Output()
    
    # Warehouse dimension inputs
    warehouse_name_input = widgets.Text(
        value='My Distribution Center',
        description='Name:',
        style={'description_width': '150px'},
        layout=widgets.Layout(width='400px')
    )
    
    length_input = widgets.FloatText(
        value=100.0,
        description='Length (m):',
        style={'description_width': '150px'},
        layout=widgets.Layout(width='300px'),
        min=1.0
    )
    
    width_input = widgets.FloatText(
        value=80.0,
        description='Width (m):',
        style={'description_width': '150px'},
        layout=widgets.Layout(width='300px'),
        min=1.0
    )
    
    height_input = widgets.FloatText(
        value=10.0,
        description='Height (m):',
        style={'description_width': '150px'},
        layout=widgets.Layout(width='300px'),
        min=1.0
    )
    
    aisles_input = widgets.IntText(
        value=10,
        description='Number of Aisles:',
        style={'description_width': '150px'},
        layout=widgets.Layout(width='300px'),
        min=1
    )
    
    # CSV upload widget
    csv_upload = widgets.FileUpload(
        accept='.csv',
        multiple=False,
        description='Upload CSV:',
        style={'description_width': '150px'},
        layout=widgets.Layout(width='400px')
    )
    
    # Generate button
    generate_button = widgets.Button(
        description='Generate Digital Twin',
        button_style='primary',
        tooltip='Generate warehouse visualization',
        icon='check',
        layout=widgets.Layout(width='300px', height='50px')
    )
    
    def on_generate_clicked(b):
        """Handle generate button click"""
        with output:
            clear_output(wait=True)
            
            try:
                # Get warehouse dimensions
                warehouse_name = warehouse_name_input.value.strip() or "My Distribution Center"
                length = length_input.value
                width = width_input.value
                height = height_input.value
                num_aisles = aisles_input.value
                
                # Validate inputs
                if length <= 0 or width <= 0 or height <= 0 or num_aisles <= 0:
                    print("❌ Error: All dimensions and number of aisles must be positive!")
                    return
                
                print("=" * 60)
                print("🏭 GENERATING WAREHOUSE DIGITAL TWIN")
                print("=" * 60)
                print(f"\n📊 Configuration:")
                print(f"   Name: {warehouse_name}")
                print(f"   Dimensions: {length}m × {width}m × {height}m")
                print(f"   Aisles: {num_aisles}")
                print()
                
                # Create warehouse
                print("🏗️ Creating warehouse...")
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
                print()
                
                # Handle CSV upload or generate sample data
                products = []
                
                if csv_upload.value:
                    print("📁 Processing uploaded CSV file...")
                    try:
                        # Get the uploaded file
                        uploaded_file = list(csv_upload.value.values())[0]
                        content = uploaded_file['content']
                        
                        # Read CSV from bytes
                        csv_data = pd.read_csv(io.BytesIO(content))
                        print(f"✅ CSV loaded: {len(csv_data)} rows")
                        
                        # Convert CSV to products
                        if not CSV_LOADER_AVAILABLE:
                            print("⚠️ CSV loader not available, generating sample products instead")
                            products = []
                        else:
                            csv_loader = CSVLoader()
                            
                            # Save temporarily and load (cross-platform)
                            with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as tmp_file:
                                tmp_path = tmp_file.name
                                csv_data.to_csv(tmp_path, index=False)
                            
                            try:
                                products = csv_loader.load_products(tmp_path)
                            finally:
                                # Clean up temp file
                                try:
                                    os.unlink(tmp_path)
                                except:
                                    pass
                        
                        print(f"✅ Loaded {len(products)} products from CSV")
                        
                    except Exception as e:
                        print(f"⚠️ Error reading CSV: {e}")
                        print("   Generating sample products instead...")
                        products = []
                else:
                    print("📦 No CSV uploaded. Generating sample products...")
                
                # Generate sample products if none loaded from CSV
                if not products:
                    print("📦 Generating sample products...")
                    for i in range(10):
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
                    print(f"✅ Generated {len(products)} sample products")
                
                print()
                
                # Create visualization
                print("🎨 Generating 3D warehouse visualization...")
                fig = generate_visualization(warehouse, products)
                print()
                
                # Create product dataframe
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
                products_df = pd.DataFrame(product_data)
                
                # Save files
                print("💾 Saving files...")
                fig.write_html("warehouse_3d.html")
                print("✅ Saved: warehouse_3d.html")
                
                products_df.to_csv("products.csv", index=False)
                print("✅ Saved: products.csv")
                
                # Try to create dashboard
                twin_df = pd.DataFrame([{
                    'item_id': p.item_id,
                    'category': p.category,
                    'description': p.description,
                    'stock_level': p.stock_level,
                    'daily_demand': p.daily_demand
                } for p in products])
                twin.load_products(twin_df)
                
                if len(products) > 0:
                    try:
                        dashboard = twin.create_dashboard()
                        dashboard.write_html("dashboard.html")
                        print("✅ Saved: dashboard.html")
                    except (AttributeError, ValueError, KeyError) as e:
                        print(f"⚠️ Dashboard creation skipped: {e}")
                    except Exception as e:
                        print(f"⚠️ Dashboard creation failed: {type(e).__name__}")
                
                print()
                print("=" * 60)
                print("🎉 WAREHOUSE DIGITAL TWIN CREATED SUCCESSFULLY!")
                print("=" * 60)
                print("\n✅ What you've created:")
                print(f"   • Warehouse: {warehouse_name}")
                print(f"   • Dimensions: {length}m × {width}m × {height}m")
                print(f"   • Aisles: {num_aisles}")
                print(f"   • Products: {len(products)}")
                print(f"   • Files: warehouse_3d.html, products.csv")
                print("\n💡 Next steps:")
                print("   1. Open warehouse_3d.html in your browser")
                print("   2. Explore the 3D visualization (rotate, zoom, click)")
                print("   3. Check products.csv for all product data")
                
                # Display preview of products
                print("\n📋 Product Preview:")
                display(products_df.head(10))
                
            except Exception as e:
                print(f"\n❌ Error: {e}")
                traceback.print_exc()
    
    generate_button.on_click(on_generate_clicked)
    
    # Layout
    title = widgets.HTML(
        value="<h2>🏭 Interactive Warehouse Digital Twin Builder</h2>"
        "<p>Configure your warehouse dimensions and upload a CSV file (optional), then click Generate!</p>"
    )
    
    dimensions_box = widgets.VBox([
        widgets.HTML("<h3>📐 Warehouse Dimensions</h3>"),
        warehouse_name_input,
        length_input,
        width_input,
        height_input,
        aisles_input
    ])
    
    csv_box = widgets.VBox([
        widgets.HTML("<h3>📁 CSV Upload (Optional)</h3>"
                    "<p>Upload a CSV file with product data, or leave empty to generate sample products.</p>"),
        csv_upload
    ])
    
    button_box = widgets.HBox([generate_button], layout=widgets.Layout(justify_content='center'))
    
    main_ui = widgets.VBox([
        title,
        dimensions_box,
        csv_box,
        button_box,
        output
    ], layout=widgets.Layout(padding='20px'))
    
    display(main_ui)
    
    print("\n💡 Tip: You can modify the dimensions and click Generate again to create a new warehouse!")


def main():
    """Main execution flow - supports both GUI and CLI modes"""
    # Check if running in a notebook environment
    # Use multiple detection methods for robustness
    in_notebook = False
    
    # Method 1: Check for IPython
    try:
        from IPython import get_ipython
        if get_ipython() is not None:
            in_notebook = True
    except (ImportError, NameError):
        pass
    
    # Method 2: Check sys.modules as fallback
    if not in_notebook and 'ipykernel' in sys.modules:
        in_notebook = True
    
    # If in notebook and GUI is available, use GUI
    if in_notebook and GUI_AVAILABLE:
        print("🎨 Launching GUI interface...")
        print("=" * 60)
        create_gui()
        return
    
    # Otherwise, use CLI
    print("=" * 60)
    print("🏭 INTERACTIVE WAREHOUSE DIGITAL TWIN BUILDER")
    print("=" * 60)
    print()
    
    if not GUI_AVAILABLE:
        print("ℹ️ Running in command-line mode")
        print("   For GUI mode, install ipywidgets and run in a Jupyter notebook")
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
