# 🏭 3D Warehouse Digital Twin & Geospatial Mapping

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A comprehensive **Digital Twin** system for warehouse optimization with advanced 3D visualization, geospatial mapping, and AGV pathfinding simulation. Designed for both Google Colab and future FastAPI deployment.

## ✨ Features

### 🏢 Warehouse Management
- **Scalable Architecture**: Support for **100,000+ aisles and shelves** without hardcoded limits
- **Detailed 3D Models**: Realistic rack structures with beams, levels, and pallet positions
- **Geometry Validation**: Pydantic models with comprehensive validation
- **Zone Optimization**: ML-powered allocation across warehouse zones (A, B, C, D)

### 🤖 ML & Optimization
- **Hybrid ML System**: Random Forest + business rules for intelligent allocation
- **Dynamic Thresholds**: Adaptive zone assignments based on utilization
- **Product Clustering**: K-means clustering for storage pattern analysis
- **Capacity Planning**: Real-time utilization tracking and forecasting

### 🗺️ 3D Geospatial Visualization
- **PyDeck Integration**: Beautiful 3D maps with warehouse locations
- **Supply Chain Routes**: Animated arcs showing shipment flows
- **Demand Heat Maps**: Hexagon-based demand visualization
- **Multi-layer Maps**: Columns, scatters, paths, and heatmaps

### 🚗 AGV Pathfinding
- **A\* Algorithm**: Efficient pathfinding for large warehouses
- **Collision Detection**: Real-time collision avoidance
- **Fleet Management**: Multi-AGV coordination
- **Navigation Grid**: Dynamic grid generation for any warehouse layout

### 📊 Analytics & Visualization
- **Interactive Dashboards**: Plotly-based performance metrics
- **Utilization Charts**: Real-time zone usage tracking
- **Cluster Analysis**: Visual product segmentation
- **3D Warehouse Views**: Rotate, zoom, and explore warehouse models

## 🚀 Quick Start

### 🆕 Interactive Warehouse Builder with GUI (Perfect for Beginners!)

Build your custom warehouse with an easy-to-use graphical interface:

```bash
# Clone repository
git clone https://github.com/spacebeige/3d_mapping.git
cd 3d_mapping

# Install dependencies
pip install -r requirements.txt

# Option 1: GUI Mode in Jupyter Notebook (Recommended)
jupyter notebook interactive_warehouse.py
# Or open examples/interactive_warehouse.ipynb

# Option 2: Command-line mode (for terminal use)
python interactive_warehouse.py
```

**✨ New GUI Features:**
1. 📐 **Interactive Input Widgets** - Easy-to-use sliders and text boxes for warehouse dimensions
2. 📁 **CSV Upload Support** - Upload your own product data via file picker widget
3. 🎯 **One-Click Generation** - Generate your warehouse with a single button click
4. 🎨 **Automatic Visualization** - Instantly see your 3D warehouse after generation
5. ⚡ **Real-time Preview** - View product data tables directly in the notebook
6. 🔄 **Error Handling** - Graceful error messages and fallback to sample data
7. 💻 **Works Everywhere** - Compatible with Google Colab, Jupyter, and VS Code notebooks

**What the GUI includes:**
- Warehouse name input
- Dimension inputs (Length, Width, Height in meters)
- Number of aisles selector
- CSV file upload button (optional - will generate sample products if not provided)
- "Generate Digital Twin" button to create your warehouse

**CSV Upload Format:**
Upload a CSV file with product data including columns like `item_id`, `category`, `description`, `stock_level`, `daily_demand`, etc. If no CSV is uploaded, the system automatically generates sample products.

👉 **See [INTERACTIVE_GUIDE.md](INTERACTIVE_GUIDE.md) for complete step-by-step guide**

### 📓 Full Demo with Advanced Features

Run the complete demo with interactive widgets:

```bash
# Clone and run the automated launcher
git clone https://github.com/spacebeige/3d_mapping.git
cd 3d_mapping

# Option 1: Cross-platform Python script (Recommended)
python3 run_warehouse_demo.py

# Option 2: Linux/macOS shell script
./run_warehouse_demo.sh

# Option 3: Windows batch script
run_warehouse_demo.bat

# Option 4: Manual launch
pip install -r requirements.txt
jupyter notebook examples/warehouse_demo.ipynb
```

**Features of the interactive notebook:**
- ✨ **Interactive widgets** for warehouse creation (no code editing!)
- 📁 **Flexible data loading**: Load CSV or generate sample data
- 🎛️ **Adjustable parameters**: Change warehouse size, dimensions, etc.
- 🔍 **Error handling**: Clear messages if files are missing
- 📊 **Full visualization suite**: 3D models, maps, analytics

👉 **See [examples/README.md](examples/README.md) for detailed usage instructions**

### 🌐 Google Colab (Cloud-based, Recommended for GUI!)

Run the interactive GUI warehouse builder directly in Google Colab:

```python
# 1. Install in Colab
!git clone https://github.com/spacebeige/3d_mapping.git
%cd 3d_mapping
!pip install -r requirements.txt

# 2. Launch GUI interface
from interactive_warehouse import create_gui
create_gui()

# The GUI will appear with:
# - Input fields for warehouse dimensions
# - CSV upload button (optional)
# - Generate button to create your warehouse
# - Live output and product preview
```

**For advanced programmatic usage:**

```python
# Import and initialize
from main import WarehouseDigitalTwin, generate_sample_data

# Create Digital Twin instance
twin = WarehouseDigitalTwin()

# Create warehouse with 10,000 aisles (scalable to 100,000+!)
warehouse = twin.create_warehouse(
    name="Mega Distribution Center",
    length=200.0,      # 200m length
    width=150.0,       # 150m width
    height=12.0,       # 12m height
    num_aisles=10000,  # No limits!
    aisle_width=3.0
)

# Generate sample data
products_df = generate_sample_data(5000)

# Train optimizer
twin.train_optimizer(products_df)

# Optimize allocation
results = twin.optimize_allocation(products_df)

# Visualize in 3D
fig = twin.visualize_warehouse_3d()
fig.show()

# Create geospatial map
deck = twin.create_geospatial_map()
deck.show()

# Performance dashboard
dashboard = twin.create_dashboard()
dashboard.show()
```

### 💻 VS Code (Local Development)

The GUI works seamlessly in VS Code with the Jupyter extension:

```bash
# 1. Clone and setup
git clone https://github.com/spacebeige/3d_mapping.git
cd 3d_mapping
pip install -r requirements.txt

# 2. Open in VS Code
code .

# 3. Open interactive_warehouse.py as a Jupyter notebook
# - Right-click the file → "Open With" → "Jupyter Notebook"
# - Or use the "Select Notebook Kernel" command

# 4. Run the cells to launch the GUI
```

**VS Code Requirements:**
- Install the [Jupyter extension](https://marketplace.visualstudio.com/items?itemName=ms-toolsai.jupyter)
- Install the [Python extension](https://marketplace.visualstudio.com/items?itemName=ms-python.python)
- Install ipywidgets: `pip install ipywidgets ipython`

The interactive GUI will render directly in VS Code's notebook interface!

### Local Installation (Command-line)

```bash
# Clone repository
git clone https://github.com/spacebeige/3d_mapping.git
cd 3d_mapping

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run example
python -c "from main import WarehouseDigitalTwin; twin = WarehouseDigitalTwin()"
```

## 📁 Project Structure

```
3d_mapping/
├── models/              # Pydantic data models
│   ├── warehouse.py     # Warehouse entities (racks, shelves, products)
│   ├── geospatial.py    # Geographic models (locations, routes)
│   └── agv.py           # AGV and pathfinding models
├── optimization/        # ML & optimization algorithms
│   ├── allocator.py     # Warehouse allocation system
│   └── clustering.py    # K-means clustering
├── viz/                 # Visualization modules
│   ├── warehouse_3d.py  # 3D warehouse visualizer
│   └── charts.py        # Analytics charts
├── geo/                 # Geospatial visualization
│   └── map_generator.py # PyDeck 3D map generator
├── core/                # Core algorithms
│   └── pathfinding.py   # A* pathfinding & collision detection
├── utils/               # Utility functions
│   └── warehouse_generator.py  # Warehouse creation utilities
├── main.py              # Main entry point (Colab integration)
├── requirements.txt     # Python dependencies
└── pyproject.toml       # Project configuration
```

## 🎯 Architecture Highlights

### Modular Design
- **Models Layer**: Type-safe Pydantic models with validation
- **Optimization Layer**: Pluggable ML algorithms
- **Visualization Layer**: Separate rendering logic
- **Core Layer**: Reusable algorithms (pathfinding, collision)

### Scalability
- **Lightweight Mode**: Automatic sampling for 100,000+ aisle warehouses
- **Efficient Rendering**: Smart product sampling for visualization
- **Optimized Pathfinding**: A* with early termination for large grids

### FastAPI Ready
```python
# Future API structure (ready for implementation)
from fastapi import FastAPI
from models import WarehouseConfig, Product

app = FastAPI()

@app.post("/warehouse/create")
async def create_warehouse(config: WarehouseConfig):
    ...

@app.post("/optimize/allocate")
async def allocate_products(products: List[Product]):
    ...
```

## 📊 Example Use Cases

### 1. Warehouse Capacity Planning
```python
from utils import WarehouseGenerator

# Estimate capacity before building
capacity = WarehouseGenerator.estimate_capacity(
    length=100,
    width=80,
    height=10,
    num_aisles=50000  # 50,000 aisles!
)

print(f"Usable volume: {capacity['usable_volume_m3']:,.0f} m³")
print(f"Estimated shelves: {capacity['estimated_shelves']:,}")
```

### 2. Supply Chain Optimization
```python
from geo import generate_sample_network, Map3DGenerator

# Create supply chain network
network = generate_sample_network(
    num_warehouses=20,
    num_routes=50,
    center_lat=40.7128,
    center_lon=-74.0060
)

# Visualize routes
map_gen = Map3DGenerator()
deck = map_gen.create_supply_chain_map(network, style="3d")
deck.show()
```

### 3. AGV Fleet Simulation
```python
from core import PathfindingGrid, generate_warehouse_navigation_grid
from models import AGV, Position3D, AGVStatus

# Generate navigation grid
nodes, segments = generate_warehouse_navigation_grid(
    warehouse_length=100,
    warehouse_width=80,
    num_aisles=20,
    aisle_width=3.0
)

# Create pathfinding system
pathfinder = PathfindingGrid(nodes, segments)

# Find path
path = pathfinder.find_path("node_a0_n0", "node_a5_n20")
print(f"Path distance: {path.total_distance:.1f}m")
print(f"Estimated time: {path.estimated_time:.1f}s")
```

## 🔧 Configuration

### Warehouse Parameters
- **Dimensions**: Any size (tested up to 500m × 300m × 15m)
- **Aisles**: No limit (efficiently handles 100,000+)
- **Shelves**: Automatically calculated based on rack configuration
- **Zones**: Configurable A/B/C/D distribution

### Performance Tips
- For warehouses with **< 100 aisles**: Full structure generation
- For warehouses with **> 100 aisles**: Automatic lightweight mode
- Product visualization capped at 1,000 by default (configurable)
- Navigation grid sampling for very large warehouses

## 📚 Documentation

### Key Classes

#### `WarehouseDigitalTwin`
Main orchestration class for all warehouse operations.

```python
twin = WarehouseDigitalTwin()
twin.create_warehouse(num_aisles=5000)
twin.load_products(df)
twin.optimize_allocation()
twin.visualize_warehouse_3d().show()
```

#### `WarehouseAllocator`
ML-powered allocation system.

```python
from optimization import WarehouseAllocator

allocator = WarehouseAllocator(total_space=1000000)
allocator.train(training_df)
results = allocator.predict_with_constraints(products_df)
```

#### `Map3DGenerator`
PyDeck-based geospatial visualizer.

```python
from geo import Map3DGenerator

map_gen = Map3DGenerator()
deck = map_gen.create_supply_chain_map(network)
deck.show()
```

## 🤝 Contributing

Contributions welcome! This is a modern, modular architecture ready for extension.

### Areas for Enhancement
- Additional ML models (XGBoost, Neural Networks)
- Real-time AGV simulation
- IoT sensor integration
- Multi-warehouse optimization
- Advanced scheduling algorithms

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details

## 🙏 Acknowledgments

- Built with Pydantic, Plotly, PyDeck, and scikit-learn
- Designed for Google Colab compatibility
- Architecture inspired by modern microservices patterns

---

**Note**: This system supports **unlimited aisles and shelves** - no hardcoded limits! Perfect for massive distribution centers and future warehouse expansion.
---

## 📁 CSV Upload & Cost-Optimized Routing

### CSV Format Specification

The system supports importing inventory data via CSV files with 23 columns:

```csv
item_id,category,description,stock_level,reorder_point,reorder_frequency_days,lead_time_days,daily_demand,demand_std_dev,item_popularity_score,storage_location_id,zone,picking_time_seconds,handling_cost_per_unit,unit_price,holding_cost_per_unit_day,stockout_count_last_month,order_fulfillment_rate,total_orders_last_month,turnover_ratio,layout_efficiency_score,last_restock_date,forecasted_demand_next_7d,KPI_score
ITM100000,Telemedicine,Portable Health Monitor,260,150,30,7,12.65,2.3,8.5,L195,A,45,0.52,89.99,0.15,1,0.98,378,2.4,0.92,2024-01-15,88.55,85.2
ITM100001,Electronics,Smart Display,450,200,25,5,18.2,3.1,9.2,L7,A,38,0.48,124.50,0.18,0,0.99,546,2.8,0.94,2024-01-20,127.4,88.5
```

### Column Descriptions

| Column | Type | Description |
|--------|------|-------------|
| `item_id` | String | Unique product identifier (e.g., ITM100000) |
| `category` | String | Product category (Electronics, VR Headsets, etc.) |
| `description` | String | Product description |
| `stock_level` | Integer | Current stock quantity |
| `reorder_point` | Integer | Minimum stock before reorder |
| `reorder_frequency_days` | Integer | Days between reorders |
| `lead_time_days` | Integer | Supplier lead time |
| `daily_demand` | Float | Average daily demand |
| `demand_std_dev` | Float | Demand standard deviation |
| `item_popularity_score` | Float | Popularity rating (1-10) |
| `storage_location_id` | String | Storage location (e.g., L195) |
| `zone` | String | Warehouse zone (A/B/C/D) |
| `picking_time_seconds` | Float | Time to pick item |
| `handling_cost_per_unit` | Float | Handling cost per unit ($) |
| `unit_price` | Float | Unit price ($) |
| `holding_cost_per_unit_day` | Float | Daily holding cost ($) |
| `stockout_count_last_month` | Integer | Number of stockouts |
| `order_fulfillment_rate` | Float | Fulfillment rate (0-1) |
| `total_orders_last_month` | Integer | Orders last month |
| `turnover_ratio` | Float | Inventory turnover ratio |
| `layout_efficiency_score` | Float | Layout efficiency (0-1) |
| `last_restock_date` | Date | Last restock date (YYYY-MM-DD) |
| `forecasted_demand_next_7d` | Float | 7-day demand forecast |
| `KPI_score` | Float | Overall KPI score |

### Usage Example

```python
from main import WarehouseDigitalTwin
from utils.csv_loader import CSVLoader
from routing.cost_optimizer import CostOptimizedRouter

# Initialize system
twin = WarehouseDigitalTwin()

# Load products from CSV
products = twin.load_products_from_csv("inventory.csv")
print(f"Loaded {len(products)} products")

# Create warehouse with multi-access points
warehouse = twin.create_warehouse(
    name="Multi-Access Distribution Center",
    length=200.0,
    width=150.0,
    height=12.0,
    num_aisles=50
)

# Add default entry/exit points
warehouse.add_default_access_points()

# Find optimal routes
routes = twin.create_cost_optimized_routes(products[:10], operation="retrieve")

# Generate cost report
report = twin.generate_cost_report(products[:10], routes, "shipping_costs.csv")

# Create visualizations
fig_3d = twin.visualize_warehouse_3d()
fig_heatmap = twin.visualize_cost_heatmap(products, routes)
fig_animation = twin.visualize_product_movement(products[0], routes[0])
```

### Multi-Access Point System

The system supports multiple entry and exit points with different capabilities and costs:

#### Default Entry Points
1. **Main Entry** - Front-Left (5m, 5m, 0)
   - Capabilities: All (standard, fragile, heavy, bulk, express)
   - Cost: $2.00 | Capacity: 200/hr

2. **Receiving Dock** - Back-Left (5m, Length-5m, 0)
   - Capabilities: Heavy, Bulk
   - Cost: $1.50 | Capacity: 150/hr

3. **Express Entry** - Front-Right (Width-5m, 5m, 0)
   - Capabilities: Fragile, Express
   - Cost: $3.00 | Capacity: 100/hr

4. **Bulk Entry** - Mid-Left (5m, Length/2, 0)
   - Capabilities: Bulk only
   - Cost: $1.00 | Capacity: 300/hr

#### Default Exit Points
1. **Shipping Dock A** - Front-Right (Width-5m, 5m, 0)
   - Capabilities: All
   - Cost: $2.50 | Capacity: 200/hr

2. **Shipping Dock B** - Back-Right (Width-5m, Length-5m, 0)
   - Capabilities: Standard, Heavy
   - Cost: $2.00 | Capacity: 250/hr

3. **Express Dock** - Front-Center (Width/2, 5m, 0)
   - Capabilities: Fragile, Express
   - Cost: $4.00 | Capacity: 80/hr

4. **Return Center** - Mid-Right (Width-5m, Length/2, 0)
   - Capabilities: All
   - Cost: $1.50 | Capacity: 120/hr

### Cost Calculation

The cost optimizer considers multiple factors:

```python
total_cost = (
    base_distance_cost +           # $0.10 per meter
    weight_penalty +                # +50% if weight > 20kg
    fragility_penalty +             # +20% for fragile items
    size_penalty +                  # +30% if size_score > 3.0
    access_point_cost +             # From AccessPoint.base_cost
    handling_cost +                 # From CSV data
    time_cost                       # $0.05 per second
)
```

### Fragile Item Categories
- Electronics
- VR Headsets
- Quantum Devices
- Telemedicine
- Wearables

### Zone Mapping
- **Zone A**: High-Value, High-Turnover items (closest to exits)
- **Zone B**: Medium-Value items
- **Zone C**: Bulky items
- **Zone D**: Low-demand, Long-term storage

### Storage Location Mapping

Storage location IDs (e.g., "L195") are automatically mapped to 3D coordinates:
- Format: `L{number}` (e.g., L195, L7, L234)
- Mapped to: Aisle number, Rack ID, Shelf position
- Algorithm assumes: 50 aisles, 10 racks per aisle, 20 shelves per rack

### Animated Product Movement

Create animated visualizations showing:
- Product moving from shelf → exit
- Color-coded path (green/yellow/red based on cost)
- Running cost counter
- Access points highlighted
- Trail effect

```python
from viz.movement_animation import MovementAnimator

animator = MovementAnimator()
fig = animator.animate_product_movement(
    product=products[0],
    route=routes[0],
    warehouse_config=warehouse,
    duration_seconds=5.0
)
fig.write_html("movement_animation.html")
```

### Cost Heatmap

Visualize expensive vs. cheap shipping zones:
- **Green areas**: Low cost (<$5)
- **Yellow areas**: Medium cost ($5-$10)
- **Red areas**: High cost (>$10)

```python
from utils.cost_reporter import CostReporter

reporter = CostReporter(warehouse)
fig = reporter.create_cost_heatmap(products, routes)
fig.write_html("cost_heatmap.html")
```

### Complete Demo

Run the complete integration demo:

```bash
cd 3d_mapping
python examples/csv_upload_demo.py
```

This generates:
- `warehouse_3d_multi_access.html` - 3D warehouse with access points
- `product_movement_animation.html` - Animated product movement
- `shipping_cost_report.csv` - Cost analysis CSV
- `cost_heatmap.html` - 3D cost heatmap
- `cost_breakdown.html` - Cost breakdown chart
- `rack_detail.html` - Detailed rack view

---
