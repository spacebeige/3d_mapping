"""
Movement Animation Module

Creates animated visualizations of product movement through warehouse.
Shows cost-optimized paths with color coding and running cost counters.
"""

import plotly.graph_objects as go
import numpy as np
from typing import List, Optional, Dict
from dataclasses import dataclass

from models.warehouse import WarehouseConfig, Product, Position3D
from routing.cost_optimizer import OptimalRoute


class MovementAnimator:
    """
    Create animated visualizations of product movement.
    
    Features:
    - Smooth transitions along path waypoints
    - Color-coded paths (green/yellow/red based on cost)
    - Running cost counter
    - Entry/exit point highlighting
    - Support for multiple products simultaneously
    """
    
    # Color thresholds for cost visualization
    LOW_COST_THRESHOLD = 5.0  # Green
    MEDIUM_COST_THRESHOLD = 10.0  # Yellow
    # Above medium = Red
    
    def __init__(self):
        """Initialize movement animator"""
        self.animations = []
    
    def animate_product_movement(
        self,
        product: Product,
        route: OptimalRoute,
        warehouse_config: WarehouseConfig,
        duration_seconds: float = 5.0,
        frame_rate: int = 30
    ) -> go.Figure:
        """
        Create animated visualization of product movement.
        
        Args:
            product: Product being moved
            route: Optimal route to follow
            warehouse_config: Warehouse configuration
            duration_seconds: Animation duration in seconds
            frame_rate: Frames per second
            
        Returns:
            Plotly Figure with animation
        """
        num_frames = int(duration_seconds * frame_rate)
        
        # Generate animation frames
        frames = self._generate_frames(
            product, route, warehouse_config, num_frames
        )
        
        # Create base figure
        fig = self._create_base_figure(warehouse_config)
        
        # Add warehouse structure
        self._add_warehouse_structure(fig, warehouse_config)
        
        # Add access points
        self._add_access_points(fig, warehouse_config, route)

        # Add static route path for context
        if route.waypoints:
            fig.add_trace(go.Scatter3d(
                x=[p.x for p in route.waypoints],
                y=[p.y for p in route.waypoints],
                z=[p.z for p in route.waypoints],
                mode='lines',
                line=dict(color=self._get_cost_color(route.total_cost), width=6),
                name='Route Path',
                hoverinfo='skip'
            ))
        
        # Add initial product position
        self._add_product_trace(fig, route.waypoints[0], product, route, 0)
        
        # Add animation frames
        fig.frames = frames
        
        # Add animation controls
        self._add_animation_controls(fig, duration_seconds)
        
        # Update layout
        fig.update_layout(
            title=f"Product Movement Animation: {product.item_id} ({product.category})<br>" +
                  f"Total Cost: ${route.total_cost:.2f} | Distance: {route.total_distance:.1f}m | " +
                  f"Time: {route.estimated_time_seconds:.1f}s",
            showlegend=True,
            hovermode='closest'
        )
        
        return fig
    
    def animate_multiple_products(
        self,
        products: List[Product],
        routes: List[OptimalRoute],
        warehouse_config: WarehouseConfig,
        duration_seconds: float = 5.0
    ) -> go.Figure:
        """
        Create animation showing multiple products moving simultaneously.
        
        Args:
            products: List of products
            routes: List of routes (same length as products)
            warehouse_config: Warehouse configuration
            duration_seconds: Animation duration
            
        Returns:
            Plotly Figure with multi-product animation
        """
        if len(products) != len(routes):
            raise ValueError("Number of products must match number of routes")
        
        fig = self._create_base_figure(warehouse_config)
        self._add_warehouse_structure(fig, warehouse_config)
        
        # Add all access points
        all_routes_set = set()
        for route in routes:
            if route.entry_point:
                all_routes_set.add(route.entry_point.id)
            if route.exit_point:
                all_routes_set.add(route.exit_point.id)
        
        self._add_access_points(fig, warehouse_config, routes[0])
        
        # Generate frames for each product
        frame_rate = 30
        num_frames = int(duration_seconds * frame_rate)
        
        # Create combined frames
        frames = []
        for frame_idx in range(num_frames):
            frame_data = []
            
            # Add each product's position at this frame
            for product, route in zip(products, routes):
                position = self._interpolate_position(
                    route.waypoints, frame_idx / num_frames
                )
                
                # Create trace for this product at this frame
                trace_data = self._create_product_frame_data(
                    position, product, route, frame_idx, num_frames
                )
                frame_data.extend(trace_data)
            
            frames.append(go.Frame(
                data=frame_data,
                name=f"frame_{frame_idx}"
            ))
        
        fig.frames = frames
        self._add_animation_controls(fig, duration_seconds)
        
        return fig
    
    def _generate_frames(
        self,
        product: Product,
        route: OptimalRoute,
        warehouse_config: WarehouseConfig,
        num_frames: int
    ) -> List[go.Frame]:
        """Generate animation frames"""
        frames = []
        
        for frame_idx in range(num_frames):
            if num_frames <= 1:
                progress = 1.0
            else:
                progress = frame_idx / (num_frames - 1)
            
            # Interpolate position along waypoints
            position = self._interpolate_position(route.waypoints, progress)
            
            # Calculate cost at this point
            current_cost = route.total_cost * progress
            
            # Create frame
            frame_data = []
            
            # Product marker
            cost_color = self._get_cost_color(route.total_cost)
            frame_data.append(go.Scatter3d(
                x=[position.x],
                y=[position.y],
                z=[position.z],
                mode='markers+text',
                marker=dict(
                    size=15,
                    color=cost_color,
                    symbol='diamond',
                    line=dict(color='white', width=2)
                ),
                text=f"${current_cost:.2f}",
                textposition='top center',
                name=product.item_id,
                hovertemplate=(
                    f"<b>{product.item_id}</b><br>" +
                    f"Category: {product.category}<br>" +
                    f"Position: ({position.x:.1f}, {position.y:.1f}, {position.z:.1f})<br>" +
                    f"Current Cost: ${current_cost:.2f}<br>" +
                    f"Progress: {progress*100:.0f}%<br>" +
                    "<extra></extra>"
                )
            ))
            
            # Trail effect (path taken so far)
            if frame_idx > 0:
                trail_positions = [
                    self._interpolate_position(
                        route.waypoints,
                        i / (num_frames - 1) if num_frames > 1 else 1.0
                    )
                    for i in range(0, frame_idx, max(1, frame_idx // 20))
                ]
                
                if trail_positions:
                    frame_data.append(go.Scatter3d(
                        x=[p.x for p in trail_positions],
                        y=[p.y for p in trail_positions],
                        z=[p.z for p in trail_positions],
                        mode='lines',
                        line=dict(
                            color=cost_color,
                            width=4,
                            dash='dot'
                        ),
                        name='Trail',
                        showlegend=False,
                        hoverinfo='skip'
                    ))
            
            frames.append(go.Frame(
                data=frame_data,
                name=f"frame_{frame_idx}",
                layout=go.Layout(
                    title_text=f"Cost: ${current_cost:.2f} / ${route.total_cost:.2f}"
                )
            ))
        
        return frames
    
    def _interpolate_position(
        self, waypoints: List[Position3D], progress: float
    ) -> Position3D:
        """
        Interpolate position along waypoints based on progress (0.0 to 1.0).
        
        Args:
            waypoints: List of waypoints
            progress: Progress from 0.0 (start) to 1.0 (end)
            
        Returns:
            Interpolated position
        """
        if not waypoints:
            return Position3D(x=0, y=0, z=0)
        
        if progress <= 0:
            return waypoints[0]
        if progress >= 1:
            return waypoints[-1]
        
        # Calculate segment lengths
        segment_lengths = []
        total_length = 0
        for i in range(len(waypoints) - 1):
            dx = waypoints[i+1].x - waypoints[i].x
            dy = waypoints[i+1].y - waypoints[i].y
            dz = waypoints[i+1].z - waypoints[i].z
            length = np.sqrt(dx**2 + dy**2 + dz**2)
            segment_lengths.append(length)
            total_length += length
        
        # Find which segment we're in
        target_distance = progress * total_length
        accumulated_distance = 0
        
        for i, seg_length in enumerate(segment_lengths):
            if accumulated_distance + seg_length >= target_distance:
                # We're in this segment
                segment_progress = (target_distance - accumulated_distance) / seg_length
                
                # Linear interpolation within segment
                start = waypoints[i]
                end = waypoints[i + 1]
                
                return Position3D(
                    x=start.x + (end.x - start.x) * segment_progress,
                    y=start.y + (end.y - start.y) * segment_progress,
                    z=start.z + (end.z - start.z) * segment_progress
                )
            
            accumulated_distance += seg_length
        
        return waypoints[-1]
    
    def _create_base_figure(self, warehouse_config: WarehouseConfig) -> go.Figure:
        """Create base figure with proper 3D layout"""
        fig = go.Figure()
        
        # Set 3D layout
        fig.update_layout(
            scene=dict(
                xaxis=dict(
                    title='Width (m)',
                    range=[0, warehouse_config.dimensions.width]
                ),
                yaxis=dict(
                    title='Length (m)',
                    range=[0, warehouse_config.warehouse_length]
                ),
                zaxis=dict(
                    title='Height (m)',
                    range=[0, warehouse_config.dimensions.height]
                ),
                aspectmode='data'
            ),
            width=1000,
            height=800,
            margin=dict(l=0, r=0, t=50, b=0)
        )
        
        return fig
    
    def _add_warehouse_structure(
        self, fig: go.Figure, warehouse_config: WarehouseConfig
    ):
        """Add warehouse walls and floor to figure"""
        width = warehouse_config.dimensions.width
        length = warehouse_config.warehouse_length
        height = warehouse_config.dimensions.height
        
        # Floor
        fig.add_trace(go.Mesh3d(
            x=[0, width, width, 0],
            y=[0, 0, length, length],
            z=[0, 0, 0, 0],
            opacity=0.1,
            color='lightgray',
            name='Floor',
            showlegend=False,
            hoverinfo='skip'
        ))
        
        # Walls (simplified)
        wall_points = [
            # Front wall
            ([0, width, width, 0], [0, 0, 0, 0], [0, 0, height, height]),
            # Back wall
            ([0, width, width, 0], [length, length, length, length], [0, 0, height, height]),
        ]
        
        for x, y, z in wall_points:
            fig.add_trace(go.Mesh3d(
                x=x, y=y, z=z,
                opacity=0.05,
                color='gray',
                showlegend=False,
                hoverinfo='skip'
            ))
    
    def _add_access_points(
        self, fig: go.Figure, warehouse_config: WarehouseConfig, route: OptimalRoute
    ):
        """Add entry and exit points to figure"""
        # Entry points (green diamonds)
        if warehouse_config.entry_points:
            for entry in warehouse_config.entry_points:
                is_used = route.entry_point and entry.id == route.entry_point.id
                fig.add_trace(go.Scatter3d(
                    x=[entry.position.x],
                    y=[entry.position.y],
                    z=[entry.position.z],
                    mode='markers+text',
                    marker=dict(
                        size=12 if is_used else 8,
                        color='green',
                        symbol='diamond',
                        line=dict(color='darkgreen', width=2)
                    ),
                    text=entry.name,
                    textposition='top center',
                    name=f"Entry: {entry.name}",
                    hovertemplate=(
                        f"<b>{entry.name}</b><br>" +
                        f"Type: Entry<br>" +
                        f"Cost: ${entry.base_cost:.2f}<br>" +
                        f"Capacity: {entry.capacity_per_hour}/hr<br>" +
                        "<extra></extra>"
                    )
                ))
        
        # Exit points (red diamonds)
        if warehouse_config.exit_points:
            for exit_point in warehouse_config.exit_points:
                is_used = route.exit_point and exit_point.id == route.exit_point.id
                fig.add_trace(go.Scatter3d(
                    x=[exit_point.position.x],
                    y=[exit_point.position.y],
                    z=[exit_point.position.z],
                    mode='markers+text',
                    marker=dict(
                        size=12 if is_used else 8,
                        color='red',
                        symbol='diamond',
                        line=dict(color='darkred', width=2)
                    ),
                    text=exit_point.name,
                    textposition='top center',
                    name=f"Exit: {exit_point.name}",
                    hovertemplate=(
                        f"<b>{exit_point.name}</b><br>" +
                        f"Type: Exit<br>" +
                        f"Cost: ${exit_point.base_cost:.2f}<br>" +
                        f"Capacity: {exit_point.capacity_per_hour}/hr<br>" +
                        "<extra></extra>"
                    )
                ))
    
    def _add_product_trace(
        self, fig: go.Figure, position: Position3D, product: Product,
        route: OptimalRoute, frame_idx: int
    ):
        """Add initial product trace"""
        cost_color = self._get_cost_color(route.total_cost)
        
        fig.add_trace(go.Scatter3d(
            x=[position.x],
            y=[position.y],
            z=[position.z],
            mode='markers',
            marker=dict(
                size=15,
                color=cost_color,
                symbol='diamond'
            ),
            name=product.item_id
        ))
    
    def _add_animation_controls(self, fig: go.Figure, duration_seconds: float):
        """Add play/pause controls and speed slider"""
        fig.update_layout(
            updatemenus=[
                dict(
                    type='buttons',
                    showactive=False,
                    buttons=[
                        dict(
                            label='Play',
                            method='animate',
                            args=[
                                None,
                                dict(
                                    frame=dict(duration=int(1000/30), redraw=True),
                                    fromcurrent=True,
                                    mode='immediate'
                                )
                            ]
                        ),
                        dict(
                            label='Pause',
                            method='animate',
                            args=[
                                [None],
                                dict(
                                    frame=dict(duration=0, redraw=False),
                                    mode='immediate'
                                )
                            ]
                        )
                    ],
                    x=0.1,
                    y=0,
                    xanchor='left',
                    yanchor='bottom'
                )
            ],
            sliders=[
                dict(
                    active=0,
                    steps=[
                        dict(
                            args=[
                                [f"frame_{i}"],
                                dict(
                                    frame=dict(duration=0, redraw=True),
                                    mode='immediate'
                                )
                            ],
                            label=f"{i*100//len(fig.frames) if fig.frames else 0}%",
                            method='animate'
                        )
                        for i in range(len(fig.frames) if fig.frames else 1)
                    ],
                    x=0.1,
                    y=0,
                    len=0.9,
                    xanchor='left',
                    yanchor='top'
                )
            ]
        )
    
    def _get_cost_color(self, total_cost: float) -> str:
        """Get color based on total cost"""
        if total_cost < self.LOW_COST_THRESHOLD:
            return 'green'
        elif total_cost < self.MEDIUM_COST_THRESHOLD:
            return 'yellow'
        else:
            return 'red'
    
    def _create_product_frame_data(
        self,
        position: Position3D,
        product: Product,
        route: OptimalRoute,
        frame_idx: int,
        num_frames: int
    ) -> List:
        """Create frame data for a product"""
        progress = frame_idx / num_frames
        current_cost = route.total_cost * progress
        cost_color = self._get_cost_color(route.total_cost)
        
        return [go.Scatter3d(
            x=[position.x],
            y=[position.y],
            z=[position.z],
            mode='markers',
            marker=dict(
                size=10,
                color=cost_color,
                symbol='diamond'
            ),
            name=product.item_id,
            text=f"${current_cost:.2f}"
        )]
