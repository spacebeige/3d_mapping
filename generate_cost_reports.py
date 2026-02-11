"""
Automated cost breakdown and heatmap generation for warehouse workflow.
Supports CSV uploads for real product and route data integration.
"""

import sys
from pathlib import Path
from utils.cost_reporter import CostReporter
from main import WarehouseDigitalTwin, generate_sample_data
from models import Product
from utils.csv_loader import CSVLoader

# --- User-dependent configuration ---
WAREHOUSE_NAME = "Zone Hub"
WAREHOUSE_LENGTH = 200.0
WAREHOUSE_WIDTH = 150.0
WAREHOUSE_HEIGHT = 12.0
NUM_AISLES = 50
RACK_HEIGHT = 8.0
NUM_PRODUCTS = 500

def load_products_from_csv(csv_path, warehouse):
    dims = getattr(warehouse, "dimensions", None)
    loader = CSVLoader({"dimensions": dims} if dims is not None else None)
    products = loader.load_products(csv_path)
    return products

def main():
    twin = WarehouseDigitalTwin()
    warehouse = twin.create_warehouse(
        name=WAREHOUSE_NAME,
        length=WAREHOUSE_LENGTH,
        width=WAREHOUSE_WIDTH,
        height=WAREHOUSE_HEIGHT,
        num_aisles=NUM_AISLES,
        rack_height=RACK_HEIGHT
    )
    warehouse.add_default_access_points()

    use_csv = input("Upload CSV for products? (y/n) [n]: ").lower().strip()
    products = []
    if use_csv == "y":
        csv_path = input("CSV Path: ").strip().strip("'\"")
        if not csv_path:
            sys.exit("No CSV path provided.")
        csv_path = Path(csv_path).expanduser().resolve()
        if not csv_path.exists() or not csv_path.is_file():
            sys.exit(f"File not found: {csv_path}")
        products = load_products_from_csv(str(csv_path), warehouse)
        print(f"Loaded {len(products)} products from CSV.")
    else:
        print("Generating sample products...")
        df = generate_sample_data(NUM_PRODUCTS)
        for idx, row in enumerate(df.itertuples(index=False), start=0):
            products.append(Product(
                item_id=row.item_id,
                category=row.category,
                description=row.description,
                stock_level=int(row.stock_level),
                daily_demand=int(row.daily_demand),
                profit_per_unit=float(getattr(row, "profit_per_unit", 50.0)),
                holding_cost_per_unit_day=float(getattr(row, "holding_cost_per_unit_day", 0.15)),
                turnover_ratio=float(getattr(row, "turnover_ratio", 2.5)),
                size_score=float(getattr(row, "size_score", 3.0)),
                predicted_zone=row.predicted_zone,
                final_zone=row.final_zone,
                position=row.position,
                shelf=row.shelf,
                rack_id=row.rack_id,
            ))

    # --- Generate routes (if needed for cost breakdown) ---
    # If you have a routing system, generate routes here. For demo, use empty list.
    routes = []

    # --- Generate and save cost heatmap ---
    reporter = CostReporter(warehouse)
    fig_heatmap = reporter.create_cost_heatmap(products, routes)
    fig_heatmap.write_html("cost_heatmap.html")
    print("✅ cost_heatmap.html generated.")

    # --- Generate and save cost breakdown chart ---
    fig_breakdown = reporter.create_cost_breakdown_chart(routes)
    fig_breakdown.write_html("cost_breakdown.html")
    print("✅ cost_breakdown.html generated.")

if __name__ == "__main__":
    main()
