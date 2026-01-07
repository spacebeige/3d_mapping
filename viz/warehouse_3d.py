"""
Warehouse 3D Visualization Module

Creates interactive 3D visualizations of warehouse layouts with products,
racks, aisles, and entry/exit paths.
"""

import plotly.graph_objects as go
import numpy as np
from typing import List, Optional, Tuple, Dict
from models.warehouse import WarehouseConfig, Product, ZoneType, Position3D


class Warehouse3DVisualizer:
    """
    Create interactive 3D warehouse visualizations with Plotly.
    
    Features:
    - Warehouse structure (walls, floor, ceiling, aisles, racks)
    - Product placement with zone-based colors
    - Entry and exit path highlighting
    - Adaptive sizing based on warehouse dimensions
    """
    
    # Zone descriptions for consistency
    ZONE_DESCRIPTIONS = {
        'A': 'High-Value, High-Turnover',
        'B': 'Medium-Value',
        'C': 'Bulky Items',
        'D': 'Long-Term Storage'
    }
    
    def __init__(self, warehouse_config: WarehouseConfig):
        """
        Initialize visualizer with warehouse configuration.
        
        Args:
            warehouse_config: Warehouse configuration model
        """
        if not warehouse_config or not warehouse_config.dimensions:
            raise ValueError("Valid warehouse_config with dimensions is required")
        
        self.config = warehouse_config
        self.warehouse_length = warehouse_config.warehouse_length
        self.warehouse_width = getattr(warehouse_config.dimensions, 'width', 0)
        self.warehouse_height = getattr(warehouse_config.dimensions, 'height', 0)
        
        if self.warehouse_width <= 0 or self.warehouse_height <= 0:
            raise ValueError("Warehouse dimensions must be positive values")
        
        # Zone colors for product visualization
        self.zone_colors = {
            "A": "#4caf50",  # Green - high-value
            "B": "#2196f3",  # Blue - medium-value
            "C": "#ff9800",  # Orange - bulky items
            "D": "#f44336",  # Red - long-term storage
        }
        
        # Entry/Exit positions (calculated based on warehouse layout)
        self.entry_position = self._calculate_entry_position()
        self.exit_position = self._calculate_exit_position()
    
    def _calculate_entry_position(self) -> Position3D:
        """
        Calculate optimal entry position based on warehouse layout.
        Typically at the front-left corner.
        """
        return Position3D(x=2.0, y=2.0, z=0.0)
    
    def _calculate_exit_position(self) -> Position3D:
        """
        Calculate optimal exit position based on warehouse layout.
        Typically at the front-right corner.
        """
        return Position3D(x=self.warehouse_width - 2.0, y=2.0, z=0.0)
    
    def create_visualization(
        self,
        products: Optional[List[Product]] = None,
        show_products: bool = True,
        max_products_display: int = 1000,
        show_entry_exit: bool = True,
        show_access_points: bool = False,
        show_cost_heatmap: bool = False
    ) -> go.Figure:
        """
        Create complete 3D warehouse visualization.
        
        Args:
            products: List of products to display
            show_products: Whether to show products
            max_products_display: Maximum number of products to display
            show_entry_exit: Whether to show entry/exit paths
            show_access_points: Whether to show access points
            show_cost_heatmap: Whether to show cost heatmap overlay
            
        Returns:
            Plotly Figure object
        """
        fig = go.Figure()
        
        # Add warehouse structure
        self._add_warehouse_structure(fig)
        
        # Add zone dividers to show A, B, C, D zones
        self._add_zone_dividers(fig)
        
        # Add racks/aisles
        self._add_racks_and_aisles(fig)
        
        # Add entry/exit paths
        if show_entry_exit:
            self._add_entry_exit_paths(fig)
        
        # Add access points (new feature)
        if show_access_points:
            self._add_access_points_visualization(fig)
        
        # Add cost heatmap (new feature)
        if show_cost_heatmap:
            self._add_cost_heatmap_overlay(fig)
        
        # Add products if provided
        if show_products and products:
            self._add_products_with_exact_locations(fig, products, max_products_display)
        
        # Configure layout
        self._configure_layout(fig)
        
        return fig
    
    def _add_warehouse_structure(self, fig: go.Figure):
        """Add warehouse walls, floor, and ceiling."""
        # Floor
        fig.add_trace(go.Mesh3d(
            x=[0, self.warehouse_width, self.warehouse_width, 0],
            y=[0, 0, self.warehouse_length, self.warehouse_length],
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
        
        # Walls outline (using scatter3d for edges)
        # Front wall
        fig.add_trace(go.Scatter3d(
            x=[0, self.warehouse_width, self.warehouse_width, 0, 0],
            y=[0, 0, 0, 0, 0],
            z=[0, 0, self.warehouse_height, self.warehouse_height, 0],
            mode='lines',
            line=dict(color='gray', width=2),
            name='Walls',
            showlegend=True,
            hoverinfo='name'
        ))
        
        # Back wall
        fig.add_trace(go.Scatter3d(
            x=[0, self.warehouse_width, self.warehouse_width, 0, 0],
            y=[self.warehouse_length, self.warehouse_length, self.warehouse_length, self.warehouse_length, self.warehouse_length],
            z=[0, 0, self.warehouse_height, self.warehouse_height, 0],
            mode='lines',
            line=dict(color='gray', width=2),
            name='Walls',
            showlegend=False,
            hoverinfo='name'
        ))
        
        # Side edges
        for x_pos in [0, self.warehouse_width]:
            fig.add_trace(go.Scatter3d(
                x=[x_pos, x_pos],
                y=[0, self.warehouse_length],
                z=[0, 0],
                mode='lines',
                line=dict(color='gray', width=2),
                name='Walls',
                showlegend=False,
                hoverinfo='name'
            ))
            fig.add_trace(go.Scatter3d(
                x=[x_pos, x_pos],
                y=[0, self.warehouse_length],
                z=[self.warehouse_height, self.warehouse_height],
                mode='lines',
                line=dict(color='gray', width=2),
                name='Walls',
                showlegend=False,
                hoverinfo='name'
            ))
    
    def _add_zone_dividers(self, fig: go.Figure):
        """Add visual dividers to show warehouse zones A, B, C, D."""
        # Zone boundaries based on length
        zone_boundaries = {
            "A": 0.30,   # 0-30% = Zone A
            "B": 0.60,   # 30-60% = Zone B
            "C": 0.80,   # 60-80% = Zone C
            "D": 1.00    # 80-100% = Zone D
        }
        
        zone_colors_divider = {
            "A": "rgba(76, 175, 80, 0.3)",   # Green
            "B": "rgba(33, 150, 243, 0.3)",  # Blue
            "C": "rgba(255, 152, 0, 0.3)",   # Orange
            "D": "rgba(244, 67, 54, 0.3)"    # Red
        }
        
        prev_y = 0
        for i, (zone, boundary) in enumerate(zone_boundaries.items()):
            y_pos = self.warehouse_length * boundary
            
            # Draw vertical divider line
            if i < len(zone_boundaries) - 1:  # Don't draw line at the end
                fig.add_trace(go.Scatter3d(
                    x=[0, self.warehouse_width, self.warehouse_width, 0, 0],
                    y=[y_pos, y_pos, y_pos, y_pos, y_pos],
                    z=[0, 0, self.warehouse_height, self.warehouse_height, 0],
                    mode='lines',
                    line=dict(color='rgba(100, 100, 100, 0.4)', width=2, dash='dash'),
                    name=f'Zone {zone} Boundary' if i == 0 else '',
                    showlegend=(i == 0),
                    hoverinfo='name'
                ))
            
            # Add zone label at the center of each zone
            zone_center_y = (prev_y + y_pos) / 2
            zone_center_x = self.warehouse_width / 2
            
            zone_desc = self.ZONE_DESCRIPTIONS.get(zone, '')
            
            fig.add_trace(go.Scatter3d(
                x=[zone_center_x],
                y=[zone_center_y],
                z=[self.warehouse_height * 0.95],
                mode='text',
                text=[f'ZONE {zone}'],
                textfont=dict(size=14, color=self.zone_colors.get(zone, 'gray'), family='Arial Black'),
                name=f'Zone {zone}' if i == 0 else '',
                showlegend=False,
                hoverinfo='text',
                hovertext=f'Zone {zone}: {zone_desc}'
            ))
            
            prev_y = y_pos
    
    def _add_racks_and_aisles(self, fig: go.Figure):
        """Add rack structures and aisles to the visualization."""
        num_aisles = self.config.layout.num_aisles
        aisle_width = self.config.layout.aisle_width
        
        # Determine how many aisles to visualize (sample for large warehouses)
        aisles_to_show = min(num_aisles, 20) if num_aisles > 50 else num_aisles
        
        # Calculate aisle positions
        total_width = self.warehouse_width
        aisle_spacing = total_width / (aisles_to_show + 1)
        
        for i in range(aisles_to_show):
            x_pos = (i + 1) * aisle_spacing
            
            # Add aisle marker (center line)
            fig.add_trace(go.Scatter3d(
                x=[x_pos, x_pos],
                y=[0, self.warehouse_length],
                z=[0, 0],
                mode='lines',
                line=dict(color='yellow', width=1, dash='dash'),
                name=f'Aisle {i+1}' if i == 0 else '',
                showlegend=(i == 0),
                hoverinfo='name'
            ))
            
            # Add rack representations on both sides of aisle
            rack_height = min(self.warehouse_height * 0.8, 8.0)
            rack_depth = self.config.layout.rack_depth
            
            # Left rack
            if x_pos - aisle_width/2 > 0:
                self._add_rack_representation(
                    fig,
                    x_pos - aisle_width/2 - rack_depth/2,
                    0,
                    self.warehouse_length,
                    rack_depth,
                    rack_height,
                    show_legend=(i == 0)
                )
            
            # Right rack
            if x_pos + aisle_width/2 < total_width:
                self._add_rack_representation(
                    fig,
                    x_pos + aisle_width/2 + rack_depth/2,
                    0,
                    self.warehouse_length,
                    rack_depth,
                    rack_height,
                    show_legend=False
                )
    
    def _add_rack_representation(
        self,
        fig: go.Figure,
        x_center: float,
        y_start: float,
        y_end: float,
        depth: float,
        height: float,
        show_legend: bool = False
    ):
        """Add a simplified rack representation."""
        # Rack as a vertical plane
        x_left = x_center - depth/2
        x_right = x_center + depth/2
        
        # Draw vertical posts at intervals
        num_posts = max(3, int((y_end - y_start) / 5))
        y_positions = np.linspace(y_start, y_end, num_posts)
        
        for y_pos in y_positions:
            fig.add_trace(go.Scatter3d(
                x=[x_center, x_center],
                y=[y_pos, y_pos],
                z=[0, height],
                mode='lines',
                line=dict(color='darkgray', width=3),
                name='Racks' if show_legend else '',
                showlegend=show_legend,
                hoverinfo='name'
            ))
            show_legend = False
    
    def _add_entry_exit_paths(self, fig: go.Figure):
        """Add entry and exit path markers."""
        # Entry path (green)
        entry = self.entry_position
        fig.add_trace(go.Scatter3d(
            x=[entry.x],
            y=[entry.y],
            z=[entry.z + 0.5],
            mode='markers+text',
            marker=dict(
                symbol='diamond',  # Valid Plotly symbol
                size=15,
                color='green',
                line=dict(color='darkgreen', width=2)
            ),
            text=['ENTRY'],
            textposition='top center',
            textfont=dict(size=12, color='green', family='Arial Black'),
            name='Entry Path',
            showlegend=True,
            hoverinfo='name'
        ))
        
        # Exit path (red)
        exit_pos = self.exit_position
        fig.add_trace(go.Scatter3d(
            x=[exit_pos.x],
            y=[exit_pos.y],
            z=[exit_pos.z + 0.5],
            mode='markers+text',
            marker=dict(
                symbol='diamond',  # Valid Plotly symbol
                size=15,
                color='red',
                line=dict(color='darkred', width=2)
            ),
            text=['EXIT'],
            textposition='top center',
            textfont=dict(size=12, color='red', family='Arial Black'),
            name='Exit Path',
            showlegend=True,
            hoverinfo='name'
        ))
        
        # Draw path lines from entry to main warehouse area
        center_y = self.warehouse_length / 2
        fig.add_trace(go.Scatter3d(
            x=[entry.x, entry.x],
            y=[entry.y, center_y],
            z=[0.1, 0.1],
            mode='lines',
            line=dict(color='green', width=4, dash='dot'),
            name='Entry Path',
            showlegend=False,
            hoverinfo='name'
        ))
        
        # Draw path lines from exit to main warehouse area
        fig.add_trace(go.Scatter3d(
            x=[exit_pos.x, exit_pos.x],
            y=[exit_pos.y, center_y],
            z=[0.1, 0.1],
            mode='lines',
            line=dict(color='red', width=4, dash='dot'),
            name='Exit Path',
            showlegend=False,
            hoverinfo='name'
        ))
    
    def _extract_zone_key(self, zone) -> Optional[str]:
        """
        Extract zone key from ZoneType enum or string.
        
        Args:
            zone: ZoneType enum, string, or None
            
        Returns:
            Zone key as string, or None if zone is invalid/falsy
        """
        if not zone:
            return None
        return zone.value if hasattr(zone, 'value') else str(zone)
    
    def _add_products(
        self,
        fig: go.Figure,
        products: List[Product],
        max_display: int
    ):
        """
        Add product markers to the visualization.
        
        Uses valid Plotly Scatter3d symbols: 'circle', 'square', 'diamond', 'cross'.
        """
        # Sample products if too many
        display_products = products[:max_display] if len(products) > max_display else products
        
        # Group products by zone
        products_by_zone = {}
        unallocated_products = []
        
        for product in display_products:
            zone = product.final_zone or product.predicted_zone
            zone_key = self._extract_zone_key(zone)
            
            if zone_key:
                if zone_key not in products_by_zone:
                    products_by_zone[zone_key] = []
                products_by_zone[zone_key].append(product)
            else:
                # Products without zone assignment
                unallocated_products.append(product)
        
        # Add unallocated products to a default zone if any exist
        if unallocated_products:
            products_by_zone['UNALLOCATED'] = unallocated_products
        
        # Add products for each zone
        for zone, zone_products in products_by_zone.items():
            # Generate positions if not already assigned
            positions = self._generate_product_positions(zone_products, zone)
            
            x_coords = [p[0] for p in positions]
            y_coords = [p[1] for p in positions]
            z_coords = [p[2] for p in positions]
            
            # Get zone color
            color = self.zone_colors.get(zone, '#9e9e9e')
            
            # Use valid Plotly symbols
            fig.add_trace(go.Scatter3d(
                x=x_coords,
                y=y_coords,
                z=z_coords,
                mode='markers',
                marker=dict(
                    symbol='square',  # Valid symbols: square, circle, diamond, cross
                    size=4,
                    color=color,
                    opacity=0.7,
                    line=dict(color='white', width=0.5)
                ),
                name=f'Products Zone {zone}',
                text=[f"{p.item_id}<br>Zone: {zone}<br>Category: {p.category}" 
                      for p in zone_products],
                hoverinfo='text',
                showlegend=True
            ))
    
    def _generate_product_positions(
        self,
        products: List[Product],
        zone: str
    ) -> List[Tuple[float, float, float]]:
        """
        Generate 3D positions for products based on zone and warehouse layout.
        
        This method optimizes product placement considering:
        - Distance from entry/exit paths for accessibility
        - Zone allocation based on profitability and turnover
        - Product characteristics (size, demand, value)
        
        Zone Strategy:
        - Zone A (High-value, high-turnover): Near entry (10-30%) for quick access
        - Zone B (Medium-value): Middle area (30-60%) for balanced access
        - Zone C (Bulky, low-value): Back-middle (60-80%) for space efficiency
        - Zone D (Low-turnover): Far back (80-95%) for long-term storage
        """
        positions = []
        
        # Zone-based positioning optimized for entry/exit accessibility
        zone_ranges = {
            "A": (0.05, 0.30),  # Front 5-30% - closest to entry for high turnover
            "B": (0.30, 0.60),  # Middle 30-60% - moderate access
            "C": (0.60, 0.80),  # Back-middle 60-80% - space for bulky items
            "D": (0.80, 0.95),  # Far back 80-95% - long-term storage
            "UNALLOCATED": (0.1, 0.95)  # Anywhere
        }
        
        # Width ranges by zone (optimize horizontal positioning too)
        # Zone A gets priority positioning on the sides with better access
        zone_width_preference = {
            "A": (0.15, 0.85),  # Central corridor access
            "B": (0.10, 0.90),  # Wider distribution
            "C": (0.05, 0.95),  # Full width for bulky items
            "D": (0.05, 0.95),  # Full width
            "UNALLOCATED": (0.10, 0.90)
        }
        
        y_range = zone_ranges.get(zone, (0.2, 0.8))
        y_min = self.warehouse_length * y_range[0]
        y_max = self.warehouse_length * y_range[1]
        
        width_range = zone_width_preference.get(zone, (0.1, 0.9))
        x_min = self.warehouse_width * width_range[0]
        x_max = self.warehouse_width * width_range[1]
        
        for i, product in enumerate(products):
            # Check if product has assigned position
            if product.position:
                positions.append((
                    product.position.x,
                    product.position.y,
                    product.position.z
                ))
            else:
                # Generate optimized position within zone range
                # For high-value items (Zone A), position closer to entry path
                if zone == "A":
                    # Prefer positions closer to entry (left side of warehouse)
                    x = np.random.triangular(x_min, x_min + (x_max - x_min) * 0.3, x_max)
                    # Prefer lower shelves for faster access
                    z = np.random.uniform(0.5, min(self.warehouse_height * 0.5, 4.0))
                elif zone == "B":
                    # More balanced distribution
                    x = np.random.uniform(x_min, x_max)
                    z = np.random.uniform(0.5, min(self.warehouse_height * 0.6, 5.0))
                elif zone == "C":
                    # Bulky items - use more floor space and lower shelves
                    x = np.random.uniform(x_min, x_max)
                    z = np.random.uniform(0.3, min(self.warehouse_height * 0.4, 3.0))
                else:  # Zone D
                    # Back storage - can use full height
                    x = np.random.uniform(x_min, x_max)
                    z = np.random.uniform(0.5, min(self.warehouse_height * 0.8, 6.0))
                
                y = np.random.uniform(y_min, y_max)
                
                positions.append((x, y, z))
        
        return positions
    
    def _configure_layout(self, fig: go.Figure):
        """Configure the 3D plot layout."""
        fig.update_layout(
            title=dict(
                text=f"🏭 {self.config.name} - 3D Warehouse Layout<br>"
                     f"<sub>Dimensions: {self.warehouse_length:.0f}m × "
                     f"{self.warehouse_width:.0f}m × {self.warehouse_height:.0f}m | "
                     f"Aisles: {self.config.layout.num_aisles}</sub>",
                x=0.5,
                xanchor='center',
                font=dict(size=16)
            ),
            scene=dict(
                xaxis=dict(
                    title='Width (m)',
                    backgroundcolor='white',
                    gridcolor='lightgray',
                    showbackground=True,
                    range=[0, self.warehouse_width]
                ),
                yaxis=dict(
                    title='Length (m)',
                    backgroundcolor='white',
                    gridcolor='lightgray',
                    showbackground=True,
                    range=[0, self.warehouse_length]
                ),
                zaxis=dict(
                    title='Height (m)',
                    backgroundcolor='white',
                    gridcolor='lightgray',
                    showbackground=True,
                    range=[0, self.warehouse_height]
                ),
                aspectmode='data',
                camera=dict(
                    eye=dict(x=1.5, y=1.5, z=1.2),
                    center=dict(x=0, y=0, z=0)
                )
            ),
            showlegend=True,
            legend=dict(
                x=1.02,
                y=1,
                xanchor='left',
                yanchor='top',
                bgcolor='rgba(255, 255, 255, 0.8)',
                bordercolor='gray',
                borderwidth=1
            ),
            margin=dict(l=0, r=0, t=80, b=0),
            height=700,
            hovermode='closest'
        )
    
    def _add_access_points_visualization(self, fig: go.Figure):
        """
        Add entry and exit access points to visualization.
        
        Shows access points as special markers with capabilities and costs.
        """
        # Entry points (green diamonds)
        if self.config.entry_points:
            for entry in self.config.entry_points:
                if not entry.active:
                    continue
                
                fig.add_trace(go.Scatter3d(
                    x=[entry.position.x],
                    y=[entry.position.y],
                    z=[entry.position.z + 1],  # Slightly elevated
                    mode='markers+text',
                    marker=dict(
                        size=15,
                        color='green',
                        symbol='diamond',
                        line=dict(color='darkgreen', width=2)
                    ),
                    text=entry.name,
                    textposition='top center',
                    textfont=dict(size=10, color='darkgreen'),
                    name=f'Entry: {entry.name}',
                    hovertemplate=(
                        f"<b>{entry.name}</b><br>" +
                        f"Type: Entry Point<br>" +
                        f"Cost: ${entry.base_cost:.2f}<br>" +
                        f"Capacity: {entry.capacity_per_hour}/hr<br>" +
                        f"Capabilities: {', '.join(entry.capabilities)}<br>" +
                        "<extra></extra>"
                    ),
                    showlegend=True
                ))
        
        # Exit points (red diamonds)
        if self.config.exit_points:
            for exit_point in self.config.exit_points:
                if not exit_point.active:
                    continue
                
                fig.add_trace(go.Scatter3d(
                    x=[exit_point.position.x],
                    y=[exit_point.position.y],
                    z=[exit_point.position.z + 1],
                    mode='markers+text',
                    marker=dict(
                        size=15,
                        color='red',
                        symbol='diamond',
                        line=dict(color='darkred', width=2)
                    ),
                    text=exit_point.name,
                    textposition='top center',
                    textfont=dict(size=10, color='darkred'),
                    name=f'Exit: {exit_point.name}',
                    hovertemplate=(
                        f"<b>{exit_point.name}</b><br>" +
                        f"Type: Exit Point<br>" +
                        f"Cost: ${exit_point.base_cost:.2f}<br>" +
                        f"Capacity: {exit_point.capacity_per_hour}/hr<br>" +
                        f"Capabilities: {', '.join(exit_point.capabilities)}<br>" +
                        "<extra></extra>"
                    ),
                    showlegend=True
                ))
    
    def _add_cost_heatmap_overlay(self, fig: go.Figure):
        """
        Add cost heatmap overlay showing expensive vs cheap zones.
        
        Green areas: Low cost to ship from
        Yellow areas: Medium cost to ship from
        Red areas: High cost to ship from
        """
        # Create grid for heatmap
        grid_size = 8
        x_grid = np.linspace(5, self.warehouse_width - 5, grid_size)
        y_grid = np.linspace(5, self.warehouse_length - 5, grid_size)
        
        # Calculate cost at each grid point based on distance to exits
        for x in x_grid:
            for y in y_grid:
                # Find minimum distance to any exit point
                min_dist = float('inf')
                if self.config.exit_points:
                    for exit_point in self.config.exit_points:
                        dx = x - exit_point.position.x
                        dy = y - exit_point.position.y
                        dist = np.sqrt(dx**2 + dy**2)
                        min_dist = min(min_dist, dist)
                
                # Estimate cost (base cost + distance cost + typical exit cost)
                estimated_cost = 0.10 * min_dist + 2.5
                
                # Determine color
                if estimated_cost < 5:
                    color = 'green'
                    opacity = 0.2
                elif estimated_cost < 10:
                    color = 'yellow'
                    opacity = 0.3
                else:
                    color = 'red'
                    opacity = 0.4
                
                # Add marker
                fig.add_trace(go.Scatter3d(
                    x=[x],
                    y=[y],
                    z=[self.warehouse_height / 2],
                    mode='markers',
                    marker=dict(
                        size=20,
                        color=color,
                        opacity=opacity,
                        symbol='square'
                    ),
                    name=f'Cost Zone',
                    hovertemplate=(
                        f"Position: ({x:.1f}, {y:.1f})<br>" +
                        f"Est. Cost: ${estimated_cost:.2f}<br>" +
                        "<extra></extra>"
                    ),
                    showlegend=False
                ))
    
    def _add_products_with_exact_locations(
        self,
        fig: go.Figure,
        products: List[Product],
        max_display: int,
        show_labels: bool = True
    ):
        """
        Enhanced product visualization with exact shelf positions.
        
        Shows:
        - Exact shelf position
        - Hover text with full location details
        - Color by zone
        - Size by daily_demand
        - Opacity by stock_level
        """
        # Sample products if too many
        display_products = products[:max_display] if len(products) > max_display else products
        
        # Group by zone
        products_by_zone = {}
        for product in display_products:
            zone = product.final_zone or product.predicted_zone
            zone_key = self._extract_zone_key(zone)
            
            if zone_key not in products_by_zone:
                products_by_zone[zone_key] = []
            products_by_zone[zone_key].append(product)
        
        # Add products for each zone
        for zone, zone_products in products_by_zone.items():
            x_coords = []
            y_coords = []
            z_coords = []
            hover_texts = []
            sizes = []
            
            for product in zone_products:
                # Use actual position if available
                if product.position:
                    x_coords.append(product.position.x)
                    y_coords.append(product.position.y)
                    z_coords.append(product.position.z)
                else:
                    # Generate position
                    pos = self._generate_single_product_position(product, zone)
                    x_coords.append(pos[0])
                    y_coords.append(pos[1])
                    z_coords.append(pos[2])
                
                # Parse storage location
                aisle, rack, shelf = self._parse_storage_location(
                    product.storage_location_id or product.shelf or ""
                )
                
                # Build hover text
                hover_text = (
                    f"📦 <b>{product.item_id}</b><br>" +
                    f"Category: {product.category}<br>" +
                    f"Zone: {zone} ({self.ZONE_DESCRIPTIONS.get(zone, 'Unknown')})<br>" +
                    f"Location: Aisle {aisle}, Rack {rack}, Shelf {shelf}<br>" +
                    f"Stock: {product.stock_level} units<br>" +
                    f"Daily Demand: {product.daily_demand} units<br>"
                )
                
                if product.handling_cost_per_unit:
                    hover_text += f"Handling Cost: ${product.handling_cost_per_unit:.2f}<br>"
                
                hover_texts.append(hover_text)
                
                # Size by daily demand (4-12 range)
                size = min(12, max(4, 4 + product.daily_demand / 10))
                sizes.append(size)
            
            # Get zone color
            color = self.zone_colors.get(zone, '#9e9e9e')
            
            # Add trace
            fig.add_trace(go.Scatter3d(
                x=x_coords,
                y=y_coords,
                z=z_coords,
                mode='markers+text' if show_labels and len(zone_products) < 20 else 'markers',
                marker=dict(
                    symbol='diamond',
                    size=sizes,
                    color=color,
                    opacity=0.7,
                    line=dict(color='white', width=1)
                ),
                text=[p.item_id for p in zone_products] if show_labels else None,
                textposition='top center',
                textfont=dict(size=6),
                name=f'Zone {zone} Products',
                hovertemplate='%{hovertext}<extra></extra>',
                hovertext=hover_texts,
                showlegend=True
            ))
    
    def _parse_storage_location(self, storage_location_id: str) -> Tuple[int, str, str]:
        """
        Parse storage_location_id to extract aisle, rack, shelf.
        
        Args:
            storage_location_id: Storage location ID (e.g., "L195", "L7")
            
        Returns:
            Tuple of (aisle_num, rack_id, shelf_id)
        """
        if not storage_location_id or storage_location_id == 'nan':
            return (0, "R0", "L0")
        
        try:
            # Extract numeric part
            location_num = int(''.join(filter(str.isdigit, storage_location_id)))
            
            # Calculate aisle, rack, shelf
            aisle_num = (location_num // 200) + 1
            rack_num = ((location_num % 200) // 20) + 1
            shelf_num = (location_num % 20) + 1
            
            return (aisle_num, f"R{rack_num}", storage_location_id)
        except:
            return (0, "R0", storage_location_id)
    
    def _generate_single_product_position(
        self, product: Product, zone: str
    ) -> Tuple[float, float, float]:
        """Generate position for a single product"""
        positions = self._generate_product_positions([product], zone)
        return positions[0] if positions else (0, 0, 0)
