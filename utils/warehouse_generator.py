"""
Warehouse Generator Utility

Creates warehouse configurations with racks, aisles, and shelves.
Supports massive scale warehouses with 100,000+ aisles and shelves.
"""

from typing import Optional, List, Dict
import numpy as np

from models.warehouse import (
    WarehouseConfig,
    WarehouseLayout,
    Dimensions3D,
    RackSystem,
    RackLevel,
    Shelf,
    Aisle,
    Position3D,
    RackType,
    ZoneType
)


class WarehouseGenerator:
    """
    Generate warehouse configurations with detailed structures.
    Optimized for large-scale warehouses.
    """
    
    @staticmethod
    def create_warehouse(
        name: str,
        length: float,
        width: float,
        height: float,
        aisle_width: float = 3.0,
        num_aisles: int = 4,
        rack_height: float = 8.0,
        rack_depth: float = 1.2,
        shelves_per_rack: int = 5,
        generate_full_structure: bool = True
    ) -> WarehouseConfig:
        """
        Create a complete warehouse configuration.
        
        Args:
            name: Warehouse name
            length: Length in meters
            width: Width in meters
            height: Height in meters
            aisle_width: Width of each aisle
            num_aisles: Number of aisles (no limit)
            rack_height: Height of racks
            rack_depth: Depth of racks
            shelves_per_rack: Shelves per rack level
            generate_full_structure: If False, creates lightweight config for very large warehouses
            
        Returns:
            WarehouseConfig instance
        """
        # Calculate layout
        total_rack_width = width - (num_aisles * aisle_width)
        rack_bay_width = total_rack_width / (num_aisles * 2) if num_aisles > 0 else width / 2
        
        # Create layout
        layout = WarehouseLayout(
            aisle_width=aisle_width,
            num_aisles=num_aisles,
            rack_bay_width=rack_bay_width,
            rack_depth=rack_depth,
            shelves_per_rack=shelves_per_rack,
            aisle_positions=[]
        )
        
        # Create dimensions
        dimensions = Dimensions3D(
            width=width,
            depth=rack_depth,
            height=height,
            length=length
        )
        
        # Create warehouse config
        warehouse = WarehouseConfig(
            name=name,
            dimensions=dimensions,
            layout=layout,
            storage_systems=[],
            metadata={
                "generate_full_structure": generate_full_structure,
                "estimated_total_shelves": 0
            }
        )
        
        # Generate structure
        if generate_full_structure and num_aisles <= 100:
            # Full generation for reasonable sizes
            warehouse = WarehouseGenerator._generate_full_structure(
                warehouse, length, width, height, aisle_width, num_aisles,
                rack_bay_width, rack_height, rack_depth, shelves_per_rack
            )
        else:
            # Lightweight for massive warehouses
            warehouse = WarehouseGenerator._generate_lightweight_structure(
                warehouse, length, width, height, aisle_width, num_aisles,
                rack_bay_width, rack_height, rack_depth
            )
        
        return warehouse
    
    @staticmethod
    def _generate_full_structure(
        warehouse: WarehouseConfig,
        length: float,
        width: float,
        height: float,
        aisle_width: float,
        num_aisles: int,
        rack_bay_width: float,
        rack_height: float,
        rack_depth: float,
        shelves_per_rack: int
    ) -> WarehouseConfig:
        """Generate full detailed warehouse structure"""
        
        # Generate aisles
        for i in range(num_aisles):
            # Calculate aisle position: racks on left + aisle spacing
            aisle_x = rack_bay_width + (rack_bay_width + aisle_width) * i
            
            aisle = Aisle(
                id=f"aisle_{i+1}",
                x_position=aisle_x,
                width=aisle_width,
                length=length
            )
            warehouse.layout.aisle_positions.append(aisle)
            
            # Generate racks on both sides of aisle
            for side, side_name in [(0, "left"), (1, "right")]:
                if side == 0:
                    # Left rack: before aisle, but ensure it's >= 0
                    rack_x = max(0, aisle_x - rack_depth)
                else:
                    # Right rack: after aisle
                    rack_x = aisle_x + aisle_width
                
                # Assign zones (distribute across racks)
                zone_idx = (i * 2 + side) % 4
                zone = ZoneType(["A", "B", "C", "D"][zone_idx])
                
                # Create rack levels
                num_levels = int(rack_height / 1.5)
                levels = []
                
                for level_num in range(1, num_levels + 1):
                    level_height = (level_num - 0.5) * (rack_height / num_levels)
                    
                    # Create shelves for this level
                    shelves = []
                    for shelf_pos in range(1, shelves_per_rack + 1):
                        shelf = Shelf(
                            id=f"A{i+1}_R{side+1}_L{level_num}_S{shelf_pos}",
                            aisle_id=aisle.id,
                            rack_id=f"rack_{side_name}_{i+1}",
                            level_number=level_num,
                            position_in_rack=shelf_pos,
                            capacity=1.5,  # m³
                            max_load_kg=1000
                        )
                        shelves.append(shelf)
                    
                    level = RackLevel(
                        level_number=level_num,
                        height_from_floor=level_height,
                        load_capacity=1000 * shelves_per_rack,
                        shelves=shelves
                    )
                    levels.append(level)
                
                # Create rack system
                rack = RackSystem(
                    id=f"rack_{side_name}_{i+1}",
                    type=RackType.PALLET_RACKING,
                    position=Position3D(x=rack_x, y=0, z=0),
                    dimensions=Dimensions3D(
                        width=rack_bay_width,
                        depth=rack_depth,
                        height=rack_height,
                        length=length
                    ),
                    levels=levels,
                    zone=zone
                )
                
                warehouse.storage_systems.append(rack)
        
        return warehouse
    
    @staticmethod
    def _generate_lightweight_structure(
        warehouse: WarehouseConfig,
        length: float,
        width: float,
        height: float,
        aisle_width: float,
        num_aisles: int,
        rack_bay_width: float,
        rack_height: float,
        rack_depth: float
    ) -> WarehouseConfig:
        """
        Generate lightweight structure for massive warehouses.
        Only creates representative samples.
        """
        # Sample aisles (create only every Nth aisle for visualization)
        sample_rate = max(1, num_aisles // 50)  # Max 50 aisles for visualization
        
        for i in range(0, num_aisles, sample_rate):
            # Calculate aisle position: racks on left + aisle spacing
            aisle_x = rack_bay_width + (rack_bay_width + aisle_width) * i
            
            aisle = Aisle(
                id=f"aisle_{i+1}",
                x_position=aisle_x,
                width=aisle_width,
                length=length
            )
            warehouse.layout.aisle_positions.append(aisle)
            
            # Sample racks
            for side, side_name in [(0, "left"), (1, "right")]:
                if side == 0:
                    # Left rack: before aisle, but ensure it's >= 0
                    rack_x = max(0, aisle_x - rack_depth)
                else:
                    # Right rack: after aisle
                    rack_x = aisle_x + aisle_width
                
                zone_idx = (i * 2 + side) % 4
                zone = ZoneType(["A", "B", "C", "D"][zone_idx])
                
                # Create minimal rack structure
                num_levels = int(rack_height / 1.5)
                levels = []
                
                for level_num in range(1, num_levels + 1):
                    level = RackLevel(
                        level_number=level_num,
                        height_from_floor=(level_num - 0.5) * (rack_height / num_levels),
                        load_capacity=10000,
                        shelves=[]  # No detailed shelves for lightweight mode
                    )
                    levels.append(level)
                
                rack = RackSystem(
                    id=f"rack_{side_name}_{i+1}",
                    type=RackType.PALLET_RACKING,
                    position=Position3D(x=rack_x, y=0, z=0),
                    dimensions=Dimensions3D(
                        width=rack_bay_width,
                        depth=rack_depth,
                        height=rack_height,
                        length=length
                    ),
                    levels=levels,
                    zone=zone
                )
                
                warehouse.storage_systems.append(rack)
        
        # Update metadata with estimates
        warehouse.metadata["sampled"] = True
        warehouse.metadata["sample_rate"] = sample_rate
        warehouse.metadata["actual_aisles"] = num_aisles
        
        return warehouse
    
    @staticmethod
    def estimate_capacity(
        length: float,
        width: float,
        height: float,
        num_aisles: int,
        aisle_width: float = 3.0,
        rack_depth: float = 1.2
    ) -> Dict[str, float]:
        """
        Estimate warehouse capacity without generating full structure.
        
        Args:
            length: Length in meters
            width: Width in meters
            height: Height in meters
            num_aisles: Number of aisles
            aisle_width: Aisle width
            rack_depth: Rack depth
            
        Returns:
            Dictionary with capacity estimates
        """
        # Calculate total aisle space
        total_aisle_space = num_aisles * aisle_width
        
        # Ensure we have space for aisles
        if total_aisle_space >= width * 0.9:  # Leave at least 10% for racks
            # Adjust assumption: aisles take less space in very large warehouses
            effective_aisle_width = (width * 0.4) / num_aisles  # Use 40% for aisles
            total_aisle_space = num_aisles * effective_aisle_width
        
        # Calculate rack space
        total_rack_space = width - total_aisle_space
        
        # Each aisle has 2 racks (one on each side)
        total_racks = num_aisles * 2
        rack_bay_width = total_rack_space / total_racks if total_racks > 0 else 1.0
        
        # Calculate rack volume
        single_rack_volume = max(0, rack_bay_width * rack_depth * height * length)
        total_rack_volume = single_rack_volume * total_racks
        
        # Estimate usable space (accounting for structure)
        usable_ratio = 0.7  # 70% usable
        usable_volume = total_rack_volume * usable_ratio
        
        # Estimate shelves
        levels_per_rack = max(1, int(height / 1.5))
        shelves_per_level = 15  # Average
        total_shelves = total_racks * levels_per_rack * shelves_per_level
        
        return {
            "total_volume_m3": total_rack_volume,
            "usable_volume_m3": usable_volume,
            "estimated_shelves": total_shelves,
            "estimated_pallet_positions": int(usable_volume / 2.5),  # Assume 2.5m³ per pallet
            "total_racks": total_racks,
            "levels_per_rack": levels_per_rack
        }
