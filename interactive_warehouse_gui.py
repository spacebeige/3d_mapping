#!/usr/bin/env python3
"""
Interactive Warehouse Builder with ipywidgets GUI

This script provides a GUI interface using ipywidgets for:
1. Defining warehouse dimensions
2. Uploading CSV files with product data or using defaults
3. Generating 3D visualizations
4. Saving all data to files

Perfect for Jupyter notebooks, Google Colab, and VS Code!
"""

import sys
from pathlib import Path
from typing import Optional
import io

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    import ipywidgets as widgets
    from IPython.display import display, HTML, clear_output
    WIDGETS_AVAILABLE = True
except ImportError:
    print("❌ ipywidgets or IPython not available. Please install with:")
    print("   pip install ipywidgets ipython")
    sys.exit(1)

from main import WarehouseDigitalTwin
from models import Product, ZoneType, Position3D
import pandas as pd
import warnings

warnings.filterwarnings('ignore')


class InteractiveWarehouseApp:
    """
    Interactive Warehouse Builder GUI using ipywidgets.
    
    Provides a user-friendly interface for warehouse creation and visualization.
    """
    
    # Position calculation constants
    RACK_DEPTH_METERS = 5.0  # Meters of warehouse length per rack
    SHELF_HEIGHT_METERS = 1.6  # Height per shelf level
    MAX_REASONABLE_AISLES = 1000  # Maximum aisles for typical warehouse
    
    def __init__(self):
        """Initialize the application"""
        self.twin = None
        self.warehouse = None
        self.products = []
        self.output = widgets.Output()
        
        # Create widgets
        self._create_widgets()
        self._setup_layout()
    
    def _create_widgets(self):
        """Create all UI widgets"""
        # Header
        self.header = widgets.HTML(
            value="""
            <h1>🏭 Interactive Warehouse Digital Twin Builder</h1>
            <p>Build custom warehouses with guided inputs and generate 3D visualizations!</p>
            """
        )
        
        # Warehouse configuration widgets
        self.warehouse_name = widgets.Text(
            value='My Distribution Center',
            description='Name:',
            placeholder='Enter warehouse name',
            style={'description_width': '150px'}
        )
        
        self.warehouse_length = widgets.FloatText(
            value=100.0,
            description='Length (m):',
            min=10.0,
            max=1000.0,
            step=10.0,
            style={'description_width': '150px'}
        )
        
        self.warehouse_width = widgets.FloatText(
            value=80.0,
            description='Width (m):',
            min=10.0,
            max=1000.0,
            step=10.0,
            style={'description_width': '150px'}
        )
        
        self.warehouse_height = widgets.FloatText(
            value=10.0,
            description='Height (m):',
            min=4.0,
            max=30.0,
            step=1.0,
            style={'description_width': '150px'}
        )
        
        self.num_aisles = widgets.IntText(
            value=10,
            description='Aisles:',
            min=1,
            max=self.MAX_REASONABLE_AISLES,
            step=1,
            style={'description_width': '150px'}
        )
        
        # CSV upload widget
        self.csv_uploader = widgets.FileUpload(
            accept='.csv',
            multiple=False,
            description='Upload CSV:',
            style={'description_width': '150px'}
        )
        
        self.csv_info = widgets.HTML(
            value='<i>Optional: Upload CSV with product data. Leave empty for sample data.</i>'
        )
        
        # Number of sample products
        self.num_sample_products = widgets.IntText(
            value=5,
            description='Sample Products:',
            min=1,
            max=100,
            step=1,
            style={'description_width': '150px'},
            layout=widgets.Layout(width='300px')
        )
        
        self.sample_info = widgets.HTML(
            value='<i>Number of sample products to generate if no CSV is uploaded.</i>'
        )
        
        # Generate button
        self.generate_button = widgets.Button(
            description='🚀 Generate Warehouse',
            button_style='success',
            tooltip='Click to create warehouse and visualizations',
            icon='rocket',
            layout=widgets.Layout(width='300px', height='50px')
        )
        self.generate_button.on_click(self._on_generate_clicked)
        
        # Progress indicator
        self.progress = widgets.HTML(value='')
    
    def _setup_layout(self):
        """Setup the widget layout"""
        # Group warehouse parameters
        warehouse_box = widgets.VBox([
            widgets.HTML('<h3>📏 Warehouse Configuration</h3>'),
            self.warehouse_name,
            self.warehouse_length,
            self.warehouse_width,
            self.warehouse_height,
            self.num_aisles
        ])
        
        # Group product data options
        products_box = widgets.VBox([
            widgets.HTML('<h3>📦 Product Data</h3>'),
            self.csv_uploader,
            self.csv_info,
            widgets.HTML('<br>'),
            self.num_sample_products,
            self.sample_info
        ])
        
        # Main layout
        self.app_layout = widgets.VBox([
            self.header,
            widgets.HTML('<hr>'),
            warehouse_box,
            widgets.HTML('<hr>'),
            products_box,
            widgets.HTML('<hr>'),
            self.generate_button,
            self.progress,
            self.output
        ], layout=widgets.Layout(padding='20px'))
    
    def _on_generate_clicked(self, button):
        """Handle generate button click"""
        with self.output:
            clear_output(wait=True)
            
            try:
                # Show progress
                self.progress.value = '<p>⏳ Generating warehouse...</p>'
                self.generate_button.disabled = True
                
                # Get warehouse parameters
                name = self.warehouse_name.value
                length = self.warehouse_length.value
                width = self.warehouse_width.value
                height = self.warehouse_height.value
                num_aisles = self.num_aisles.value
                
                # Create warehouse
                print("=" * 80)
                print("🏗️ CREATING WAREHOUSE")
                print("=" * 80)
                print(f"Name: {name}")
                print(f"Dimensions: {length}m × {width}m × {height}m")
                print(f"Aisles: {num_aisles}")
                print()
                
                self.twin = WarehouseDigitalTwin()
                self.warehouse = self.twin.create_warehouse(
                    name=name,
                    length=length,
                    width=width,
                    height=height,
                    num_aisles=num_aisles,
                    aisle_width=3.0,
                    rack_height=height * 0.8
                )
                print("✅ Warehouse created successfully!")
                print()
                
                # Load or generate products
                self.progress.value = '<p>⏳ Loading products...</p>'
                self.products = self._load_products(num_aisles, length, width, height)
                
                print(f"✅ Loaded {len(self.products)} products")
                print()
                
                # Display summary
                self._display_summary()
                
                # Generate visualization
                self.progress.value = '<p>⏳ Generating 3D visualization...</p>'
                self._generate_visualization()
                
                # Save files
                self.progress.value = '<p>⏳ Saving files...</p>'
                self._save_files()
                
                # Success message
                self.progress.value = '<p style="color: green;">✅ Warehouse created successfully!</p>'
                
                print()
                print("=" * 80)
                print("🎉 COMPLETE!")
                print("=" * 80)
                print("\n📁 Generated files:")
                print("   - warehouse_3d.html (Open in browser)")
                print("   - products.csv (Product data)")
                print("\n💡 Open warehouse_3d.html in your browser to explore the 3D visualization!")
                
            except Exception as e:
                self.progress.value = f'<p style="color: red;">❌ Error: {str(e)}</p>'
                print(f"❌ Error: {e}")
                import traceback
                traceback.print_exc()
            finally:
                self.generate_button.disabled = False
    
    def _load_products(self, num_aisles: int, length: float, width: float, height: float) -> list:
        """Load products from CSV or generate sample data"""
        products = []
        
        # Check if CSV was uploaded
        if self.csv_uploader.value:
            print("📁 Loading products from CSV...")
            try:
                # Get uploaded file
                uploaded_file = list(self.csv_uploader.value.values())[0]
                content = uploaded_file['content']
                
                # Parse CSV
                df = pd.read_csv(io.BytesIO(content))
                print(f"   Parsed {len(df)} rows from CSV")
                
                # Convert to products
                products = self._csv_to_products(df, num_aisles, length, width, height)
                print(f"   Converted to {len(products)} products")
                
            except pd.errors.EmptyDataError:
                print(f"⚠️ CSV file is empty")
                print("   Falling back to sample data...")
                products = self._generate_sample_products(
                    self.num_sample_products.value, num_aisles, length, width, height
                )
            except pd.errors.ParserError as e:
                print(f"⚠️ Error parsing CSV: {e}")
                print("   Expected format: CSV with columns like 'item_id', 'category', 'description', 'stock_level', 'daily_demand'")
                print("   Falling back to sample data...")
                products = self._generate_sample_products(
                    self.num_sample_products.value, num_aisles, length, width, height
                )
            except KeyError as e:
                print(f"⚠️ Missing required column in CSV: {e}")
                print("   Expected columns: item_id (optional), category, description, stock_level, daily_demand")
                print("   Falling back to sample data...")
                products = self._generate_sample_products(
                    self.num_sample_products.value, num_aisles, length, width, height
                )
            except Exception as e:
                print(f"⚠️ Error loading CSV: {e}")
                print("   Falling back to sample data...")
                products = self._generate_sample_products(
                    self.num_sample_products.value, num_aisles, length, width, height
                )
        else:
            # Generate sample products
            print("📦 Generating sample products...")
            products = self._generate_sample_products(
                self.num_sample_products.value, num_aisles, length, width, height
            )
        
        return products
    
    def _csv_to_products(self, df: pd.DataFrame, num_aisles: int, length: float, width: float, height: float) -> list:
        """Convert CSV data to Product objects"""
        products = []
        
        for idx, row in df.iterrows():
            # Extract fields (with defaults)
            item_id = row.get('item_id', f'PROD{idx+1:04d}')
            category = row.get('category', 'general')
            description = row.get('description', f'Product {idx+1}')
            stock_level = int(row.get('stock_level', 100))
            daily_demand = float(row.get('daily_demand', 10.0))
            
            # Assign position
            position = self._assign_position(idx, num_aisles, length, width, height)
            
            # Determine zone
            zone = self._determine_zone(daily_demand)
            
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
        
        return products
    
    def _generate_sample_products(self, count: int, num_aisles: int, length: float, width: float, height: float) -> list:
        """Generate sample products"""
        products = []
        categories = ['electronics', 'groceries', 'pharma', 'apparel', 'automotive']
        
        for i in range(count):
            position = self._assign_position(i, num_aisles, length, width, height)
            daily_demand = 10.0 + (i % 50)
            zone = self._determine_zone(daily_demand)
            
            product = Product(
                item_id=f"PROD{i+1:04d}",
                category=categories[i % len(categories)],
                description=f"Sample Product {i+1}",
                stock_level=100,
                daily_demand=daily_demand,
                profit_per_unit=50.0,
                holding_cost_per_unit_day=0.15,
                turnover_ratio=daily_demand / 100.0,
                size_score=3.0,
                predicted_zone=zone,
                position=position
            )
            products.append(product)
        
        return products
    
    def _assign_position(self, product_index: int, total_aisles: int, 
                        warehouse_length: float, warehouse_width: float, 
                        warehouse_height: float) -> Position3D:
        """Assign a unique position to each product"""
        # Calculate configuration based on warehouse dimensions
        racks_per_aisle = max(10, int(warehouse_length / self.RACK_DEPTH_METERS))
        usable_height = warehouse_height * 0.8
        shelves_per_rack = max(3, int(usable_height / self.SHELF_HEIGHT_METERS))
        
        products_per_aisle = racks_per_aisle * shelves_per_rack
        
        aisle_num = (product_index // products_per_aisle) % total_aisles
        rack_num = (product_index % products_per_aisle) // shelves_per_rack
        shelf_num = product_index % shelves_per_rack
        
        aisle_spacing = warehouse_width / (total_aisles + 1)
        x = aisle_spacing * (aisle_num + 1)
        
        rack_spacing = warehouse_length / racks_per_aisle
        y = rack_spacing * (rack_num + 0.5)
        
        shelf_height = usable_height / shelves_per_rack
        z = shelf_height * (shelf_num + 0.5)
        
        return Position3D(x=x, y=y, z=z)
    
    def _determine_zone(self, daily_demand: float) -> ZoneType:
        """Determine warehouse zone based on daily demand"""
        if daily_demand > 50:
            return ZoneType.A
        elif daily_demand > 20:
            return ZoneType.B
        elif daily_demand > 10:
            return ZoneType.C
        else:
            return ZoneType.D
    
    def _display_summary(self):
        """Display product summary"""
        product_data = []
        for p in self.products:
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
        print(f"Total Products: {len(self.products)}")
        print(f"Total Stock: {sum(p.stock_level for p in self.products):,} units")
        print(f"Total Daily Demand: {sum(p.daily_demand for p in self.products):.1f} units/day")
        print(f"\nZone Distribution:")
        zone_counts = {}
        for p in self.products:
            zone = p.predicted_zone.value
            zone_counts[zone] = zone_counts.get(zone, 0) + 1
        for zone, count in sorted(zone_counts.items()):
            print(f"  Zone {zone}: {count} products")
    
    def _generate_visualization(self):
        """Generate and save 3D visualization"""
        from viz.warehouse_3d import Warehouse3DVisualizer
        
        print("\n🎨 Generating 3D warehouse visualization...")
        
        visualizer = Warehouse3DVisualizer(self.warehouse)
        self.fig = visualizer.create_visualization(
            products=self.products,
            show_products=True,
            max_products_display=len(self.products)
        )
        
        print("✅ Visualization created")
    
    def _save_files(self):
        """Save all generated files"""
        print("\n💾 Saving files...")
        
        # Save warehouse visualization
        self.fig.write_html("warehouse_3d.html")
        print("✅ Saved: warehouse_3d.html")
        
        # Save product data as CSV
        product_data = []
        for p in self.products:
            product_data.append({
                'item_id': p.item_id,
                'category': p.category,
                'description': p.description,
                'stock_level': p.stock_level,
                'daily_demand': p.daily_demand,
                'zone': p.predicted_zone.value,
                'position_x': p.position.x,
                'position_y': p.position.y,
                'position_z': p.position.z
            })
        
        df = pd.DataFrame(product_data)
        df.to_csv("products.csv", index=False)
        print("✅ Saved: products.csv")
    
    def display(self):
        """Display the application"""
        display(self.app_layout)


def main():
    """Main entry point for the GUI application"""
    print("Starting Interactive Warehouse Builder GUI...")
    print("Note: This requires a Jupyter environment with ipywidgets support.")
    print()
    
    app = InteractiveWarehouseApp()
    app.display()


if __name__ == "__main__":
    # Check if running in a Jupyter environment
    try:
        get_ipython()
        main()
    except NameError:
        print("=" * 80)
        print("⚠️ This script is designed to run in a Jupyter environment")
        print("=" * 80)
        print("\nPlease run this in:")
        print("  1. Jupyter Notebook")
        print("  2. JupyterLab")
        print("  3. Google Colab")
        print("  4. VS Code with Jupyter extension")
        print("\nTo use from Python:")
        print("  >>> from interactive_warehouse_gui import InteractiveWarehouseApp")
        print("  >>> app = InteractiveWarehouseApp()")
        print("  >>> app.display()")
