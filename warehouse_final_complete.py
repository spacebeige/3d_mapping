def _generate_interactive_product_movement_animation(warehouse, products, rack_height):
        """
        Generate a dynamic product movement animation HTML file with top selling and top profitable products.
        The output file is named dynamic_product_movement_animation.html.
        This will include the union of the top 15 by daily demand and top 15 by profit per unit.
        """
        import plotly
        import json
        from pathlib import Path
        from routing.cost_optimizer import CostOptimizedRouter
        from viz.movement_animation import MovementAnimator
        from models import Position3D

        # Helper to choose sensible start position for animations
        def _choose_start_position(prod):
            # try zone-matched access points first
            zone = getattr(prod, "final_zone", None) or getattr(prod, "predicted_zone", None)
            points = []
            if hasattr(warehouse, "entry_points") and warehouse.entry_points:
                points.extend([p for p in warehouse.entry_points if getattr(p, "active", True)])
            if hasattr(warehouse, "exit_points") and warehouse.exit_points:
                points.extend([p for p in warehouse.exit_points if getattr(p, "active", True)])
            # prefer access point whose zone matches product zone
            if zone and points:
                for ap in points:
                    if getattr(ap, "zone", None) == zone:
                        return ap.position
            # if product has known position, return it (start at product zone)
            pos = getattr(prod, "position", None)
            if pos is not None:
                return pos
            # otherwise choose nearest access point to product position if available
            if points and pos is not None:
                def _dist(a, b):
                    ax, ay, az = float(getattr(a, "x", 0) or 0), float(getattr(a, "y", 0) or 0), float(getattr(a, "z", 0) or 0)
                    bx, by, bz = float(getattr(b, "x", 0) or 0), float(getattr(b, "y", 0) or 0), float(getattr(b, "z", 0) or 0)
                    return (ax-bx)**2 + (ay-by)**2 + (az-bz)**2
                nearest = min(points, key=lambda ap: _dist(getattr(prod, "position", pos), getattr(ap, "position", pos)))
                return nearest.position
            # fallback to first access point if any
            if points:
                return points[0].position
            # last resort: origin
            return Position3D(x=0, y=0, z=0)

        # Select top 15 by daily_demand and top 15 by profit_per_unit (union)
        TOP_N = 15
        top_by_demand = sorted(products, key=lambda p: getattr(p, "daily_demand", 0), reverse=True)[:TOP_N]
        top_by_profit = sorted(products, key=lambda p: getattr(p, "profit_per_unit", 0), reverse=True)[:TOP_N]
        # Use a dict to preserve order and uniqueness
        unique_products = {}
        for p in top_by_demand + top_by_profit:
            unique_products[str(p.item_id)] = p
        selected_products = list(unique_products.values())

        product_data = []
        total = len(selected_products)
        print(f"Generating movement animations for {total} top selling/profitable products...")
        for idx, product in enumerate(selected_products):
            print(f"  [{idx+1}/{total}] Item ID: {product.item_id}")
            router = CostOptimizedRouter(warehouse)
            # choose start position sensibly (zone-based / nearest / product / fallback)
            start_pos = _choose_start_position(product)
            route = router.find_optimal_route(
                product=product,
                start_position=start_pos,
                operation="retrieve",
            )
            if not route.waypoints:
                route.waypoints = [route.start_position, route.end_position]
            animator = MovementAnimator()
            fig = animator.animate_product_movement(
                product=product,
                route=route,
                warehouse_config=warehouse,
                duration_seconds=6.0,
            )
            # Extract Plotly figure JSON
            fig_json = fig.to_plotly_json()
            product_data.append({
                "item_id": str(product.item_id),
                "category": product.category,
                "fig": fig_json
            })
        print("Animation generation complete.")

        # Build HTML with dropdown and JS
        item_ids = [p["item_id"] for p in product_data]
        html = f"""
<html>
<head>
    <meta charset='utf-8'/>
    <script src='https://cdn.plot.ly/plotly-latest.min.js'></script>
</head>
<body>
    <h2>Dynamic Product Movement Animation</h2>
    <label for='itemSelect'>Select Item ID:</label>
    <select id='itemSelect'>
        {''.join([f'<option value="{item_id}">{item_id}</option>' for item_id in item_ids])}
    </select>
    <div id='plotlyDiv' style='width:90vw; height:80vh;'></div>
    <script>
        const productData = {json.dumps(product_data)};
        function renderFig(itemId) {{
            const prod = productData.find(p => p.item_id === itemId);
            if (prod) {{
                Plotly.newPlot('plotlyDiv', prod.fig.data, prod.fig.layout, {{responsive: true, displayModeBar: true}});
                if (prod.fig.frames) {{
                    Plotly.addFrames('plotlyDiv', prod.fig.frames);
                }}
            }}
        }}
        document.getElementById('itemSelect').addEventListener('change', function(e) {{
            renderFig(e.target.value);
        }});
        // Initial render
        renderFig(document.getElementById('itemSelect').value);
    </script>
</body>
</html>
"""
        out_path = Path(PROJECT_ROOT) / "dynamic_product_movement_animation.html"
        with open(out_path, "w", encoding="utf-8") as f:
                f.write(html)
        print(f"   ✅ Dynamic product movement animation (interactive) saved to: {out_path}")
def _generate_dynamic_product_movement_animation(warehouse, products, item_id, rack_height):
    """
    Generate a dynamic product movement animation HTML for a specific item_id.
    The output file is named dynamic_product_movement_animation_<item_id>.html.
    """
    from routing.cost_optimizer import CostOptimizedRouter
    from viz.movement_animation import MovementAnimator
    from models import Position3D
    from pathlib import Path
    # Find the product by item_id
    product = next((p for p in products if str(p.item_id) == str(item_id)), None)
    if not product:
        print(f"❌ Item ID {item_id} not found in products.")
        return

    # same helper logic (small inline version) to pick start position
    def _choose_start_position(prod):
        zone = getattr(prod, "final_zone", None) or getattr(prod, "predicted_zone", None)
        points = []
        if hasattr(warehouse, "entry_points") and warehouse.entry_points:
            points.extend([p for p in warehouse.entry_points if getattr(p, "active", True)])
        if hasattr(warehouse, "exit_points") and warehouse.exit_points:
            points.extend([p for p in warehouse.exit_points if getattr(p, "active", True)])
        if zone and points:
            for ap in points:
                if getattr(ap, "zone", None) == zone:
                    return ap.position
        pos = getattr(prod, "position", None)
        if pos is not None:
            return pos
        if points and pos is not None:
            def _dist(a, b):
                ax, ay, az = float(getattr(a, "x", 0) or 0), float(getattr(a, "y", 0) or 0), float(getattr(a, "z", 0) or 0)
                bx, by, bz = float(getattr(b, "x", 0) or 0), float(getattr(b, "y", 0) or 0), float(getattr(b, "z", 0) or 0)
                return (ax-bx)**2 + (ay-by)**2 + (az-bz)**2
            nearest = min(points, key=lambda ap: _dist(getattr(prod, "position", pos), getattr(ap, "position", pos)))
            return nearest.position
        if points:
            return points[0].position
        return Position3D(x=0, y=0, z=0)

    router = CostOptimizedRouter(warehouse)
    start_pos = _choose_start_position(product)
    route = router.find_optimal_route(
        product=product,
        start_position=start_pos,
        operation="retrieve",
    )
    if not route.waypoints:
        route.waypoints = [route.start_position, route.end_position]
    animator = MovementAnimator()
    anim_fig = animator.animate_product_movement(
        product=product,
        route=route,
        warehouse_config=warehouse,
        duration_seconds=6.0,
    )
    out_path = Path(PROJECT_ROOT) / f"dynamic_product_movement_animation_{item_id}.html"
    anim_fig.write_html(out_path)
    print(f"   ✅ Dynamic product movement animation for item {item_id} saved to: {out_path}")
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


def _generate_dynamic_rack_detail(warehouse, products, rack_height):
    """
    Generate a dynamic rack detail HTML file with a dropdown to select racks and view their details and contained products.
    The output file is named dynamic_rack_detail.html.
    """
    import json
    from pathlib import Path
    # Group products by rack_id
    rack_map = {}
    for p in products:
        rack_map.setdefault(p.rack_id, []).append({
            "item_id": str(p.item_id),
            "category": p.category,
            "description": getattr(p, "description", ""),
            "stock_level": getattr(p, "stock_level", 0),
            "daily_demand": getattr(p, "daily_demand", 0)
        })
    rack_ids = sorted(rack_map.keys())
    dropdown_html = ''.join([f'<option value="{rack_id}">{rack_id}</option>' for rack_id in rack_ids])
    html = (
        "<html>"
        "<head>"
        "    <meta charset='utf-8'/>"
        "    <title>Dynamic Rack Detail</title>"
        "    <style>"
        "        body {{ font-family: Arial, sans-serif; background: #f8f8f8; }}"
        "        #main {{ max-width: 900px; margin: 30px auto; background: #fff; border-radius: 8px; box-shadow: 0 2px 8px #ccc; padding: 24px; }}"
        "        h2 {{ margin-top: 0; }}"
        "        #rackSelect {{ margin-bottom: 18px; }}"
        "        table {{ border-collapse: collapse; width: 100%; }}"
        "        th, td {{ border: 1px solid #ccc; padding: 8px; text-align: left; }}"
        "        th {{ background: #eee; }}"
        "    </style>"
        "</head>"
        "<body>"
        "<div id='main'>"
        "    <h2>Dynamic Rack Detail</h2>"
        "    <label for='rackSelect'>Select Rack:</label>"
        f"    <select id='rackSelect'>{dropdown_html}</select>"
        "    <div id='rackDetail'></div>"
        "</div>"
        "<script>"
        f"    const rackData = {json.dumps(rack_map)};"
        "    function renderRack(rackId) {"
        "        const products = rackData[rackId] || [];"
        "        let html = `<h3>Rack: ${{rackId}}</h3>`;"
        "        if (products.length === 0) {"
        "            html += '<p>No products in this rack.</p>';"
        "        } else {"
        "            html += `<table><tr><th>Item ID</th><th>Category</th><th>Description</th><th>Stock</th><th>Daily Demand</th></tr>`;"
        "            for (const p of products) {"
        "                html += `<tr><td>${p.item_id}</td><td>${p.category}</td><td>${p.description}</td><td>${p.stock_level}</td><td>${p.daily_demand}</td></tr>`;"
        "            }"
        "            html += `</table>`;"
        "        }"
        "        document.getElementById('rackDetail').innerHTML = html;"
        "    }"
        "    document.getElementById('rackSelect').addEventListener('change', function(e) {"
        "        renderRack(e.target.value);"
        "    });"
        "    // Initial render"
        "    renderRack(document.getElementById('rackSelect').value);"
        "</script>"
        "</body>"
        "</html>"
    )
    out_path = Path(PROJECT_ROOT) / "dynamic_rack_detail.html"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"   ✅ Dynamic rack detail saved to: {out_path}")

def _build_visuals(warehouse, products: List[Product], rack_height: float):
    # --- Generate and save cost heatmap and breakdown reports (from generate_cost_reports.py) ---
    try:
        from utils.cost_reporter import CostReporter
        reporter = CostReporter(warehouse)
        # If you have a routing system, generate routes here. For now, use empty list for demo.
        routes = []
        fig_heatmap = reporter.create_cost_heatmap(products, routes)
        fig_heatmap.write_html("cost_heatmap.html")
        print("✅ cost_heatmap.html generated.")
        fig_breakdown = reporter.create_cost_breakdown_chart(routes)
        fig_breakdown.write_html("cost_breakdown.html")
        print("✅ cost_breakdown.html generated.")
    except Exception as e:
        print(f"⚠️ Could not generate cost reports: {e}")

    # Create empty map, filled map, and animation outputs. Also generate dynamic cost breakdown and heatmap.
    length, width, height, aisles = _safe_dimensions(warehouse)
    print(f"   📐 Using dimensions LxWxH: {length}m x {width}m x {height}m | Aisles: {aisles}")

    visualizer = Warehouse3DVisualizer(warehouse, rack_height)


    # 1) Empty map
    empty_fig = visualizer.create_visualization(
        products=None,
        show_products=False,
        show_access_points=True,
    )
    empty_path = PROJECT_ROOT / "warehouse_empty_map.html"
    empty_fig.write_html(empty_path)
    print(f"   ✅ Empty 3D map saved to: {empty_path}")

    # 2) Filled map (with products)
    filled_fig = visualizer.create_visualization(
        products=products,
        show_products=True,
        show_access_points=True,
    )
    filled_path = PROJECT_ROOT / "warehouse_filled_map.html"
    filled_fig.write_html(filled_path)
    print(f"   ✅ Filled 3D map saved to: {filled_path}")

    # Generate dynamic cost breakdown, heatmap, multi-access, rack detail, and interactive animation HTMLs
    _generate_dynamic_cost_breakdown(warehouse, products, height)
    _generate_dynamic_cost_heatmap(warehouse, products, height)
    _generate_dynamic_warehouse_3d_multi_access(warehouse, products, height)
    _generate_dynamic_rack_detail(warehouse, products, height)
    _generate_interactive_product_movement_animation(warehouse, products, height)

    if not products:
        print("   ⚠️ No products available; skipping filled map and animation.")
        return

def _generate_dynamic_warehouse_3d_multi_access(warehouse, products, rack_height):
    """
    Generate a dynamic 3D warehouse multi-access HTML file using user warehouse and rack details.
    The output file is named dynamic_warehouse_3d_multi_access.html.
    """
    import plotly.graph_objects as go
    from pathlib import Path
    import numpy as np

    # Example: Show all entry/exit points and racks in 3D
    width = getattr(warehouse.dimensions, 'width', 150)
    length = getattr(warehouse.dimensions, 'length', 200)
    height = getattr(warehouse.dimensions, 'height', 12)
    aisles = getattr(warehouse.layout, 'num_aisles', 10)
    aisle_width = getattr(warehouse.layout, 'aisle_width', 3)
    rack_depth = getattr(warehouse.layout, 'rack_depth', 2)

    fig = go.Figure()

    # Draw warehouse floor
    fig.add_trace(go.Mesh3d(
        x=[0, width, width, 0],
        y=[0, 0, length, length],
        z=[0, 0, 0, 0],
        i=[0, 0],
        j=[1, 2],
        k=[2, 3],
        color='lightgray',
        opacity=0.2,
        name='Floor',
        showlegend=True,
        hoverinfo='name'
    ))

    # Draw racks (simplified)
    aisle_spacing = width / (aisles + 1)
    for i in range(aisles):
        x_pos = (i + 1) * aisle_spacing
        for side in [-1, 1]:
            rack_x = x_pos + side * (aisle_width/2 + rack_depth/2)
            fig.add_trace(go.Scatter3d(
                x=[rack_x, rack_x],
                y=[0, length],
                z=[0, rack_height],
                mode='lines',
                line=dict(color='#404040', width=4),
                name='Rack',
                showlegend=(i == 0 and side == -1),
                hoverinfo='name'
            ))

    # Draw entry/exit points
    if hasattr(warehouse, 'entry_points') and warehouse.entry_points:
        for entry in warehouse.entry_points:
            if not getattr(entry, 'active', True):
                continue
            fig.add_trace(go.Scatter3d(
                x=[entry.position.x],
                y=[entry.position.y],
                z=[entry.position.z + 1],
                mode='markers+text',
                marker=dict(size=15, color='green', symbol='diamond', line=dict(color='darkgreen', width=2)),
                text=entry.name,
                textposition='top center',
                textfont=dict(size=10, color='darkgreen'),
                name=f'Entry: {entry.name}',
                hoverinfo='name',
                showlegend=True
            ))
    if hasattr(warehouse, 'exit_points') and warehouse.exit_points:
        for exit_point in warehouse.exit_points:
            if not getattr(exit_point, 'active', True):
                continue
            fig.add_trace(go.Scatter3d(
                x=[exit_point.position.x],
                y=[exit_point.position.y],
                z=[exit_point.position.z + 1],
                mode='markers+text',
                marker=dict(size=15, color='red', symbol='diamond', line=dict(color='darkred', width=2)),
                text=exit_point.name,
                textposition='top center',
                textfont=dict(size=10, color='darkred'),
                name=f'Exit: {exit_point.name}',
                hoverinfo='name',
                showlegend=True
            ))

    fig.update_layout(
        title=f"Dynamic 3D Warehouse Multi-Access (Rack Height: {rack_height}m)",
        scene=dict(
            xaxis=dict(title='Width (X)', range=[0, width]),
            yaxis=dict(title='Length (Y)', range=[0, length]),
            zaxis=dict(title='Height (Z)', range=[0, max(height, rack_height)]),
            aspectmode='cube',
        ),
        margin=dict(l=10, r=10, b=10, t=80),
        template="plotly_white",
        annotations=[dict(
            text=f"Rack Height: {rack_height}m",
            xref="paper", yref="paper",
            x=1, y=1.08, showarrow=False, font=dict(size=12, color="#444")
        )]
    )
    out_path = Path(PROJECT_ROOT) / "dynamic_warehouse_3d_multi_access.html"
    fig.write_html(out_path)
    print(f"   ✅ Dynamic 3D warehouse multi-access saved to: {out_path}")

    # (Removed) Individual animated movement files for top products. Use dynamic_product_movement_animation.html for all products.
def _generate_dynamic_cost_breakdown(warehouse, products, rack_height):
    """
    Generate a dynamic cost breakdown HTML file using user warehouse and product data.
    The output file is named dynamic_cost_breakdown.html.
    """
    from utils.cost_reporter import CostReporter
    from routing.cost_optimizer import CostOptimizedRouter
    from pathlib import Path
    import os

    # Generate routes for all products
    router = CostOptimizedRouter(warehouse)
    routes = []
    for product in products:
        route = router.find_optimal_route(
            product=product,
            start_position=product.position,
            operation="retrieve",
        )
        routes.append(route)

    # Generate cost breakdown chart using CostReporter
    reporter = CostReporter(warehouse)
    fig = reporter.create_cost_breakdown_chart(routes)
    out_path = Path(os.path.abspath(os.getcwd())) / "dynamic_cost_breakdown.html"
    fig.write_html(out_path)
    print(f"   ✅ Dynamic cost breakdown saved to: {out_path}")

def _generate_dynamic_cost_heatmap(warehouse, products, rack_height):
    """
    Generate dynamic_cost_heatmap.html showing a heatmap of aggregated metrics
    (total_cost = daily_demand * profit_per_unit, daily_demand, profit_per_unit)
    per aisle x vertical level. Heatmap is interactive and allows switching metric.
    """
    from pathlib import Path
    import json

    # Safe extraction of aisles and defaults
    layout = getattr(warehouse, "layout", None)
    num_aisles = max(1, int(getattr(layout, "num_aisles", 10))) if layout else 10

    # Derive aisle and vertical level for each product robustly
    def prod_coords(p):
        pos = getattr(p, "position", None)
        # aisle from position.x (if numeric) or from rack_id fallback
        aisle = None
        if pos is not None:
            try:
                aisle = int(getattr(pos, "x", 0))
            except Exception:
                aisle = 0
        if aisle is None:
            # fallback: try rack/zone attributes
            aisle = int(getattr(p, "aisle", 0) or 0)
        # vertical level: use z / rack_height if available
        try:
            z = float(getattr(pos, "z", 0) or 0)
            level = max(0, int(z // max(1.0, float(rack_height or 1.0))))
        except Exception:
            level = 0
        # clamp aisle into range
        aisle = max(0, min(num_aisles - 1, aisle))
        return aisle, level

    # Aggregate metrics into cells (aisle, level)
    cells = {}
    max_level = 0
    for p in products:
        aisle, level = prod_coords(p)
        max_level = max(max_level, level)
        key = f"{aisle}|{level}"
        entry = cells.setdefault(key, {"aisle": aisle, "level": level, "daily_demand": 0.0, "profit_per_unit": 0.0, "count": 0})
        entry["daily_demand"] += float(getattr(p, "daily_demand", 0) or 0)
        entry["profit_per_unit"] += float(getattr(p, "profit_per_unit", 0) or 0)
        entry["count"] += 1

    # Build grids
    levels = max_level + 1
    x_labels = [f"Aisle {i}" for i in range(num_aisles)]
    y_labels = [f"Level {i}" for i in range(levels)]

    # initialize matrices
    def init_matrix():
        return [[0.0 for _ in range(num_aisles)] for _ in range(levels)]

    mat_demand = init_matrix()
    mat_profit = init_matrix()
    mat_cost = init_matrix()

    for v in cells.values():
        a = v["aisle"]
        l = v["level"]
        mat_demand[l][a] = v["daily_demand"]
        # average profit per unit if multiple products
        mat_profit[l][a] = (v["profit_per_unit"] / v["count"]) if v["count"] else 0.0
        mat_cost[l][a] = mat_demand[l][a] * mat_profit[l][a]

    product_data = {
        "x_labels": x_labels,
        "y_labels": y_labels,
        "mat_demand": mat_demand,
        "mat_profit": mat_profit,
        "mat_cost": mat_cost,
    }

    # Build HTML with Plotly heatmap + JS update function
    html = f"""
<html>
<head>
  <meta charset="utf-8" />
  <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 12px; }}
    #controls {{ margin-bottom: 8px; }}
  </style>
</head>
<body>
  <h3>Dynamic Cost Heatmap</h3>
  <div id="controls">
    <label for="metric">Metric:</label>
    <select id="metric">
      <option value="mat_cost">Total Cost (demand * profit)</option>
      <option value="mat_demand">Daily Demand</option>
      <option value="mat_profit">Avg Profit/Unit</option>
    </select>
    <button id="download">Download PNG</button>
  </div>
  <div id="heatmap" style="width:90vw; height:70vh;"></div>

  <script>
    const productData = {json.dumps(product_data)};
    const layout = {{
      title: 'Heatmap (aisles x levels)',
      xaxis: {{ title: 'Aisles', tickvals: [...Array(productData.x_labels.length).keys()], ticktext: productData.x_labels }},
      yaxis: {{ title: 'Levels', autorange: 'reversed', tickvals: [...Array(productData.y_labels.length).keys()], ticktext: productData.y_labels }},
      margin: {{ t: 40, l: 90, r: 40, b: 120 }},
      colorbar: {{ title: '' }}
    }};

    const config = {{ responsive: true }};

    function draw(metricKey) {{
      const z = productData[metricKey];
            const data = [{{
                z: z,
                x: productData.x_labels,
                y: productData.y_labels,
                type: 'heatmap',
                colorscale: 'YlOrRd',
                hovertemplate: 'Aisle: %{{x}}<br>Level: %{{y}}<br>Value: %{{z}}<extra></extra>'
            }}];
      Plotly.react('heatmap', data, layout, config);
    }}

    // initial draw
    draw('mat_cost');

    document.getElementById('metric').addEventListener('change', function(e) {{
      draw(e.target.value);
    }});

    document.getElementById('download').addEventListener('click', function() {{
      Plotly.toImage(document.getElementById('heatmap'), {{format: 'png', height: 800, width: 1200}})
        .then(function(url) {{
          const a = document.createElement('a');
          a.href = url;
          a.download = 'dynamic_cost_heatmap.png';
          document.body.appendChild(a);
          a.click();
          a.remove();
        }});
    }});

    // Optional: expose update function to window for external refreshes
    window.updateHeatmapData = function(newData) {{
      // expecting same shape: {{mat_cost, mat_demand, mat_profit, x_labels, y_labels}}
      productData.x_labels = newData.x_labels || productData.x_labels;
      productData.y_labels = newData.y_labels || productData.y_labels;
      productData.mat_cost = newData.mat_cost || productData.mat_cost;
      productData.mat_demand = newData.mat_demand || productData.mat_demand;
      productData.mat_profit = newData.mat_profit || productData.mat_profit;
      // redraw with currently selected metric
      const sel = document.getElementById('metric').value;
      draw(sel);
    }};
  </script>
</body>
</html>
"""
    out_path = Path(PROJECT_ROOT) / "dynamic_cost_heatmap.html"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"   ✅ Dynamic cost heatmap saved to: {out_path}")


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
        rack_height = _prompt_positive_float("    Rack Height (m): ", 8)
    else:
        length, width, height, aisles, rack_height = 200.0, 150.0, 12.0, 50, 8.0

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

    _build_visuals(warehouse, products, rack_height)

    print("\n✅ DONE — Empty map, filled map, and animation are ready.")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        sys.exit(1)
