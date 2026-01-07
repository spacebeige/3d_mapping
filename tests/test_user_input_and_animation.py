import sys
from pathlib import Path

# Ensure repository root is on path
sys.path.insert(0, str(Path(__file__).parent.parent))

from interactive_warehouse import get_warehouse_dimensions
from models.warehouse import (
    Dimensions3D,
    Position3D,
    WarehouseConfig,
    WarehouseLayout,
    Product,
)
from routing.cost_optimizer import OptimalRoute
from viz.movement_animation import MovementAnimator


def test_get_warehouse_dimensions_requires_user_values(monkeypatch):
    """Warehouse dimensions must come from user input, not defaults."""

    inputs = iter([
        "User Warehouse",  # name
        "", "120",         # length (blank first to trigger reprompt)
        "80",              # width
        "12",              # height
        "15",              # aisles
    ])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    name, length, width, height, num_aisles = get_warehouse_dimensions()

    assert name == "User Warehouse"
    assert (length, width, height, num_aisles) == (120.0, 80.0, 12.0, 15)


def test_animation_reaches_final_waypoint():
    """Animation frames should end at the final waypoint with full cost shown."""

    warehouse = WarehouseConfig(
        name="Animation Warehouse",
        dimensions=Dimensions3D(width=20.0, depth=100.0, height=5.0, length=100.0),
        layout=WarehouseLayout(
            aisle_width=3.0,
            num_aisles=4,
            rack_bay_width=2.0,
            rack_depth=1.2,
            shelves_per_rack=3,
        ),
    )

    waypoints = [
        Position3D(x=0.0, y=0.0, z=0.0),
        Position3D(x=10.0, y=5.0, z=2.0),
    ]

    product = Product(
        item_id="P1",
        description="Test Product",
        category="test",
        profit_per_unit=1.0,
        daily_demand=1,
        stock_level=1,
        holding_cost_per_unit_day=0.1,
        turnover_ratio=0.5,
        size_score=1.0,
        position=waypoints[0],
    )

    route = OptimalRoute(
        product=product,
        start_position=waypoints[0],
        end_position=waypoints[-1],
        waypoints=waypoints,
        total_distance=12.0,
        total_cost=25.0,
        estimated_time_seconds=8.0,
    )

    animator = MovementAnimator()
    frames = animator._generate_frames(
        product,
        route,
        warehouse,
        num_frames=5,
        product_trace_idx=0,
        trail_trace_idx=1,
    )

    final_trace = frames[-1].data[0]
    assert list(final_trace.x) == [waypoints[-1].x]
    assert list(final_trace.y) == [waypoints[-1].y]
    assert list(final_trace.z) == [waypoints[-1].z]

    title_text = frames[-1].layout.title.text if frames[-1].layout.title else ""
    assert f"/ ${route.total_cost:.2f}" in title_text
