#!/usr/bin/env python3
"""
Final CLI to render:
1) EMPTY 3D warehouse map (zones/racks/aisles)
2) FILLED 3D map with CSV items placed on racks/shelves/aisles
3) Animated AGV/product movement along optimized path

The script keeps the familiar prompts from earlier versions while
handling dimension attributes safely to avoid AttributeErrors.
"""

import sys
import traceback
from pathlib import Path
from typing import List, Tuple

# Ensure repository root is importable when the script is executed directly
PROJECT_ROOT = Path(__file__).parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from interactive_warehouse import assign_position, determine_zone
from main import WarehouseDigitalTwin, generate_sample_data
from models import Position3D, Product
from routing.cost_optimizer import CostOptimizedRouter
from utils.csv_loader import CSVLoader
from viz.movement_animation import MovementAnimator
from viz.warehouse_3d import Warehouse3DVisualizer

SHELF_BASE_OFFSET = 100


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
    aisles = getattr(layout, "num_aisles", 50)

    return length, width, height, max(int(aisles), 1)


def _load_products_from_csv(csv_path: str, warehouse) -> List[Product]:
    """Load products from CSV with 3D positions preserved."""
    dims = getattr(warehouse, "dimensions", None)
    loader = CSVLoader({"dimensions": dims} if dims is not None else None)
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
    length, width, height, aisles = _safe_dimensions(warehouse)

    products: List[Product] = []
    for idx, row in enumerate(df.itertuples(index=False), start=0):
        pos = assign_position(
            idx,
            aisles,
            length,
            width,
            height,
        )
        zone = determine_zone(getattr(row, "daily_demand", 0))
        rack_slot = (idx % aisles) + 1
        products.append(
            Product(
                item_id=row.item_id,
                category=row.category,
                description=row.description,
                stock_level=int(row.stock_level),
                daily_demand=int(row.daily_demand),
                profit_per_unit=float(getattr(row, "profit_per_unit", 50.0)),
                holding_cost_per_unit_day=float(getattr(row, "holding_cost_per_unit_day", 0.15)),
                turnover_ratio=float(getattr(row, "turnover_ratio", 2.5)),
                size_score=float(getattr(row, "size_score", 3.0)),
                predicted_zone=zone,
                final_zone=zone,
                position=pos,
                shelf=f"L{SHELF_BASE_OFFSET + idx}",
                rack_id=f"R{rack_slot}",
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

    if not products:
        print("   ⚠️ No products available; skipping filled map and animation.")
        return

    # 2) Filled map with enhanced hover tooltips
    # We'll modify the visualizer to add detailed hover information
    filled_fig = visualizer.create_visualization(
        products=products,
        show_products=True,
        show_access_points=True,
    )
    
    filled_path = PROJECT_ROOT / "warehouse_filled_map.html"
    filled_fig.write_html(filled_path)
    print(f"   ✅ Filled 3D map saved to: {filled_path}")

    # 3) Animated movement for multiple products
    sorted_products = sorted(
        products, key=lambda p: getattr(p, "daily_demand", 0), reverse=True
    )
    top_products = sorted_products[:5]  # Animate top 5 products by demand

    animator = MovementAnimator()
    for product in top_products:
        router = CostOptimizedRouter(warehouse)
        route = router.find_optimal_route(
            product=product,
            start_position=product.position or Position3D(x=0, y=0, z=0),
            operation="retrieve",
        )

        # Guarantee waypoints exist for animation
        if not route.waypoints:
            route.waypoints = [
                route.start_position,
                route.end_position,
            ]

        anim_fig = animator.animate_product_movement(
            product=product,
            route=route,
            warehouse_config=warehouse,
            duration_seconds=6.0,
        )
        anim_path = PROJECT_ROOT / f"warehouse_movement_animation_{product.item_id}.html"
        anim_fig.write_html(anim_path)
        print(f"   ✅ Animated movement for product {product.item_id} saved to: {anim_path}")


def main():
    """Run the complete CLI workflow."""
    print("=" * 70)
    print("🏭  WAREHOUSE 3D UI - FINAL COMPLETE EDITION")
    print("=" * 70)

    def _prompt_positive_float(prompt_text: str, default: float) -> float:
        while True:
            raw = input(prompt_text).strip()
            if not raw:
                return float(default)
            try:
                value = float(raw)
                if value > 0:
                    return value
                print("❌ Please enter a positive number.")
            except ValueError:
                print("❌ Invalid number. Please try again.")

    def _prompt_positive_int(prompt_text: str, default: int) -> int:
        while True:
            raw = input(prompt_text).strip()
            if not raw:
                return int(default)
            try:
                value = int(raw)
                if value > 0:
                    return value
                print("❌ Please enter a positive integer.")
            except ValueError:
                print("❌ Invalid number. Please try again.")

    # 1) Dimensions
    use_custom = input("\n[1] Customize dimensions? (y/n) [n]: ").lower().strip()
    if use_custom == "y":
        length = _prompt_positive_float("    Length (m): ", 200)
        width = _prompt_positive_float("    Width (m):  ", 150)
        height = _prompt_positive_float("    Height (m): ", 12)
        aisles = _prompt_positive_int("    Aisles:      ", 50)
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
        raw_csv = input("    📂 CSV Path: ").strip().strip("'\"")
        if not raw_csv:
            sys.exit("❌ No CSV path provided.")
        csv_path = Path(raw_csv).expanduser().resolve()

        repo_root = PROJECT_ROOT.resolve()
        try:
            csv_path.relative_to(repo_root)
        except ValueError:
            sys.exit("❌ CSV path must be inside the repository directory.")

        if not csv_path.exists() or not csv_path.is_file():
            sys.exit(f"❌ File not found: {csv_path}")

        products = _load_products_from_csv(str(csv_path), warehouse)
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
