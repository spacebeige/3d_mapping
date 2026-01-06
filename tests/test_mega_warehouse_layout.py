import sys

from utils.warehouse_generator import WarehouseGenerator


def main():
    width = 150.0
    aisle_width = 3.0
    excessive_aisles = int(width / aisle_width) + 1

    warehouse = WarehouseGenerator.create_warehouse(
        name="Mega Distribution Center",
        length=200.0,
        width=width,
        height=12.0,
        aisle_width=aisle_width,
        num_aisles=excessive_aisles,
        generate_full_structure=False
    )

    assert warehouse.layout.rack_bay_width > 0
    assert warehouse.layout.aisle_width > 0

    print("✅ Mega warehouse layout generated successfully")
    print(f"   rack_bay_width: {warehouse.layout.rack_bay_width:.6f} m")
    print(f"   aisle_width: {warehouse.layout.aisle_width:.6f} m")
    print(f"   sampled_aisles: {len(warehouse.layout.aisle_positions)}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
