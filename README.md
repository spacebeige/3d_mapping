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

### Google Colab (Recommended)

```python
# Install in Colab
!git clone https://github.com/spacebeige/3d_mapping.git
%cd 3d_mapping
!pip install -r requirements.txt

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

### Local Installation

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