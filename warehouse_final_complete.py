#!/usr/bin/env python3
"""
Final CLI to render:
1) EMPTY 3D warehouse map (zones/racks/aisles)
2) FILLED 3D map with CSV items placed on racks/shelves/aisles
3) Animated AGV/product movement along optimized path

The script keeps the familiar prompts from earlier versions while
handling dimension attributes safely to avoid AttributeErrors.
"""

import os
import sys
import traceback
from pathlib import Path
from typing import List, Tuple

import pandas as pd

# Ensure repository root is importable when the script is executed directly
PROJECT_ROOT = Path(__file__).parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from interactive_warehouse import assign_position, determine_zone  # type: ignore
from main import WarehouseDigitalTwin, generate_sample_data
from models.warehouse import Position3D, Product, ZoneType
from routing.cost_optimizer import CostOptimizedRouter
from utils.csv_loader import CSVLoader
from viz.movement_animation import MovementAnimator
from viz.warehouse_3d import Warehouse3DVisualizer


def _safe_dimensions(warehouse) -> Tuple[float, float, float, int]:
    """
    Safely extract dimensions and aisle count from the warehouse config.
    Falls back to sensible defaults when attributes are missing.
    """
    dims = getattr(warehouse, "dimensions", None)
    length = getattr(warehouse, "warehouse_length", None)
    width = getattr(dims, "width", None)
    height = getattr(dims, "height", None)

    # Some models may store "depth" instead of "length"
    if length is None and dims is not None:
        length = getattr(dims, "length", None) or getattr(dims, "depth", None)

    length = float(length or 200.0)
    width = float(width or 150.0)
    height = float(height or 12.0)

    layout = getattr(warehouse, "layout", None)
    aisles = getattr(layout, "num_aisles", 20)

    return length, width, height, int(aisles)


def _load_products_from_csv(csv_path: str, warehouse) -> List[Product]:
    """Load products from CSV with 3D positions preserved."""
    loader = CSVLoader({"dimensions": getattr(warehouse, "dimensions", {})})
    products = loader.load_products(csv_path)
    return products


def _generate_sample_products(
    warehouse, num_products: int = 500
) -> List[Product]:
    """
    Create positioned products when no CSV is provided.
    Uses the same placement and zone rules as the interactive UI.
    """
    df = generate_sample_data(num_products)
    _, _, height, aisles = _safe_dimensions(warehouse)
    length = getattr(warehouse, "warehouse_length", 200.0)
    width = getattr(getattr(warehouse, "dimensions", None), "width", 150.0)

    products: List[Product] = []
    for idx, row in df.iterrows():
        pos = assign_position(
            idx,
            aisles,
            length,
            width,
            height,
        )
        zone = determine_zone(row.get("daily_demand", 0))
        products.append(
            Product(
                item_id=row["item_id"],
                category=row["category"],
                description=row["description"],
                stock_level=int(row["stock_level"]),
                daily_demand=int(row["daily_demand"]),
                profit_per_unit=float(row.get("profit_per_unit", 50.0)),
                holding_cost_per_unit_day=float(row.get("holding_cost_per_unit_day", 0.15)),
                turnover_ratio=float(row.get("turnover_ratio", 2.5)),
                size_score=float(row.get("size_score", 3.0)),
                predicted_zone=zone,
                final_zone=zone,
                position=pos,
                shelf=f"L{100 + idx}",
                rack_id=f"R{1 + idx % max(aisles, 1)}",
            )
        )
    return products


def _build_visuals(warehouse, products: List[Product]):
    """Create empty map, filled map, and animation outputs."""
    length, width, height, aisles = _safe_dimensions(warehouse)
    print(f"   📐 Using dimensions LxWxH: {length}m x {width}m x {height}m | Aisles: {aisles}")

    visualizer = Warehouse3DVisualizer(warehouse)

    # 1) Empty map
    empty_fig = visualizer.create_visualization(
        products=None,
        show_products=False,
        show_access_points=True,
    )
    empty_path = PROJECT_ROOT / "warehouse_empty_map.html"
    empty_fig.write_html(empty_path)
    print(f"   ✅ Empty 3D map saved to: {empty_path}")

    # 2) Filled map
    filled_fig = visualizer.create_visualization(
        products=products,
        show_products=True,
        show_access_points=True,
    )
    filled_path = PROJECT_ROOT / "warehouse_filled_map.html"
    filled_fig.write_html(filled_path)
    print(f"   ✅ Filled 3D map saved to: {filled_path}")

    # 3) Animated movement for the first/highest-demand product
    focus_product = sorted(
        products, key=lambda p: getattr(p, "daily_demand", 0), reverse=True
    )[0]
    router = CostOptimizedRouter(warehouse)
    route = router.find_optimal_route(
        product=focus_product,
        start_position=focus_product.position or Position3D(x=0, y=0, z=0),
        operation="retrieve",
    )

    # Guarantee waypoints exist for animation
    if not route.waypoints:
        route.waypoints = [
            route.start_position,
            route.end_position,
        ]

    animator = MovementAnimator()
    anim_fig = animator.animate_product_movement(
        product=focus_product,
        route=route,
        warehouse_config=warehouse,
        duration_seconds=6.0,
    )
    anim_path = PROJECT_ROOT / "warehouse_movement_animation.html"
    anim_fig.write_html(anim_path)
    print(f"   ✅ Animated movement saved to: {anim_path}")


def main():
    """Run the complete CLI workflow."""
    print("=" * 70)
    print("🏭  WAREHOUSE 3D UI - FINAL COMPLETE EDITION")
    print("=" * 70)

    # 1) Dimensions
    use_custom = input("\n[1] Customize dimensions? (y/n) [n]: ").lower().strip()
    if use_custom == "y":
        length = float(input("    Length (m): ") or 200)
        width = float(input("    Width (m):  ") or 150)
        height = float(input("    Height (m): ") or 12)
        aisles = int(input("    Aisles:      ") or 50)
    else:
        length, width, height, aisles = 200.0, 150.0, 12.0, 50

    # 2) Data
    use_csv = input("\n[2] Upload CSV? (y/n) [n]: ").lower().strip()
    products: List[Product] = []

    # 3) Build warehouse + allocation context
    twin = WarehouseDigitalTwin()
    warehouse = twin.create_warehouse(
        name="Zone Hub",
        length=length,
        width=width,
        height=height,
        num_aisles=aisles,
    )
    warehouse.add_default_access_points()

    if use_csv == "y":
        csv_path = (
            input("    📂 CSV Path: ").strip().strip("'").strip('"').strip()
        )
        if not csv_path:
            sys.exit("❌ No CSV path provided.")
        if not os.path.exists(csv_path):
            sys.exit(f"❌ File not found: {csv_path}")

        products = _load_products_from_csv(csv_path, warehouse)
        print(f"    ✅ Loaded {len(products)} products from CSV.")
    else:
        print("    🎲 Generating sample positioned data...")
        products = _generate_sample_products(warehouse)
        print(f"    ✅ Generated {len(products)} sample products.")

    print("\n" + "=" * 70)
    print("⚙️  BUILDING VISUALS...")
    print("=" * 70)

    _build_visuals(warehouse, products)

    print("\n✅ DONE — Empty map, filled map, and animation are ready.")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        sys.exit(1)
