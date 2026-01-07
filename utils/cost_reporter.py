"""
Cost Analysis and Reporting

Generate shipping cost reports and cost heatmap visualizations.
"""

import pandas as pd
import plotly.graph_objects as go
import numpy as np
from typing import List, Dict, Optional

from models.warehouse import WarehouseConfig, Product, Position3D
from routing.cost_optimizer import OptimalRoute


class CostReporter:
    """
    Generate cost analysis reports and visualizations.
    
    Features:
    - CSV shipping cost reports
    - 3D cost heatmaps
    - Cost breakdown analysis
    - Access point utilization reports
    """
    
    def __init__(self, warehouse_config: Optional[WarehouseConfig] = None):
        """
        Initialize cost reporter.
        
        Args:
            warehouse_config: Warehouse configuration
        """
        self.warehouse = warehouse_config
    
    def generate_shipping_report(
        self,
        products: List[Product],
        routes: List[OptimalRoute]
    ) -> pd.DataFrame:
        """
        Generate detailed shipping cost report.
        
        Args:
            products: List of products
            routes: List of optimal routes
            
        Returns:
            DataFrame with cost breakdown
        """
        if len(products) != len(routes):
            raise ValueError("Number of products must match number of routes")
        
        report_data = []
        
        for product, route in zip(products, routes):
            row = {
                'item_id': product.item_id,
                'category': product.category,
                'current_location': self._format_location(route.start_position),
                'optimal_exit': route.exit_point.name if route.exit_point else 'N/A',
                'distance_meters': round(route.total_distance, 2),
                'base_cost': round(route.base_distance_cost, 2),
                'weight_cost': round(route.weight_cost, 2),
                'fragility_cost': round(route.fragility_cost, 2),
                'size_cost': round(route.size_cost, 2),
                'handling_cost': round(route.handling_cost, 2),
                'access_point_cost': round(route.access_point_cost, 2),
                'time_cost': round(route.time_cost, 2),
                'total_cost': round(route.total_cost, 2),
                'estimated_time_seconds': round(route.estimated_time_seconds, 1),
                'cost_per_meter': round(route.total_cost / max(route.total_distance, 1), 2),
                'zone': str(product.final_zone or product.predicted_zone or 'Unknown'),
                'stock_level': product.stock_level,
                'daily_demand': product.daily_demand
            }
            
            report_data.append(row)
        
        df = pd.DataFrame(report_data)
        
        # Sort by total cost (descending)
        df = df.sort_values('total_cost', ascending=False)
        
        return df
    
    def generate_summary_statistics(
        self, routes: List[OptimalRoute]
    ) -> Dict:
        """
        Generate summary statistics for routes.
        
        Args:
            routes: List of optimal routes
            
        Returns:
            Dictionary with statistics
        """
        if not routes:
            return {}
        
        costs = [r.total_cost for r in routes]
        distances = [r.total_distance for r in routes]
        times = [r.estimated_time_seconds for r in routes]
        
        # Count by exit point
        exit_counts = {}
        for route in routes:
            if route.exit_point:
                exit_name = route.exit_point.name
                exit_counts[exit_name] = exit_counts.get(exit_name, 0) + 1
        
        return {
            'total_routes': len(routes),
            'total_cost': round(sum(costs), 2),
            'average_cost': round(np.mean(costs), 2),
            'median_cost': round(np.median(costs), 2),
            'min_cost': round(min(costs), 2),
            'max_cost': round(max(costs), 2),
            'std_cost': round(np.std(costs), 2),
            'total_distance': round(sum(distances), 2),
            'average_distance': round(np.mean(distances), 2),
            'total_time': round(sum(times), 2),
            'average_time': round(np.mean(times), 2),
            'exit_point_usage': exit_counts
        }
    
    def create_cost_heatmap(
        self,
        products: Optional[List[Product]] = None,
        routes: Optional[List[OptimalRoute]] = None
    ) -> go.Figure:
        """
        Create 3D cost heatmap showing expensive vs cheap zones.
        
        Args:
            products: Optional list of products
            routes: Optional list of routes
            
        Returns:
            Plotly Figure
        """
        if not self.warehouse:
            raise ValueError("Warehouse configuration required for heatmap")
        
        fig = go.Figure()
        
        # Create grid for heatmap
        width = self.warehouse.dimensions.width
        length = self.warehouse.warehouse_length
        height = self.warehouse.dimensions.height
        
        # Grid resolution
        grid_size = 10
        x_grid = np.linspace(5, width - 5, grid_size)
        y_grid = np.linspace(5, length - 5, grid_size)
        
        # Calculate cost at each grid point
        if routes and products:
            # Use actual route data
            cost_grid = self._calculate_cost_grid_from_routes(
                x_grid, y_grid, products, routes
            )
        else:
            # Estimate based on distance to exits
            cost_grid = self._estimate_cost_grid(x_grid, y_grid)
        
        # Create 3D scatter plot with color coding
        for i, x in enumerate(x_grid):
            for j, y in enumerate(y_grid):
                cost = cost_grid[i, j]
                
                # Color based on cost
                if cost < 5:
                    color = 'green'
                    opacity = 0.3
                elif cost < 10:
                    color = 'yellow'
                    opacity = 0.5
                else:
                    color = 'red'
                    opacity = 0.7
                
                fig.add_trace(go.Scatter3d(
                    x=[x],
                    y=[y],
                    z=[height / 2],  # Mid-height
                    mode='markers',
                    marker=dict(
                        size=15,
                        color=color,
                        opacity=opacity,
                        symbol='square'
                    ),
                    name=f"Cost: ${cost:.2f}",
                    hovertemplate=(
                        f"Position: ({x:.1f}, {y:.1f})<br>" +
                        f"Estimated Cost: ${cost:.2f}<br>" +
                        "<extra></extra>"
                    ),
                    showlegend=False
                ))
        
        # Add exit points
        if self.warehouse.exit_points:
            for exit_point in self.warehouse.exit_points:
                fig.add_trace(go.Scatter3d(
                    x=[exit_point.position.x],
                    y=[exit_point.position.y],
                    z=[exit_point.position.z],
                    mode='markers+text',
                    marker=dict(
                        size=20,
                        color='blue',
                        symbol='diamond',
                        line=dict(color='darkblue', width=2)
                    ),
                    text=exit_point.name,
                    textposition='top center',
                    name=exit_point.name,
                    hovertemplate=(
                        f"<b>{exit_point.name}</b><br>" +
                        f"Base Cost: ${exit_point.base_cost:.2f}<br>" +
                        "<extra></extra>"
                    )
                ))
        
        # Update layout
        fig.update_layout(
            title="Warehouse Cost Heatmap<br>" +
                  "<sub>Green: Low Cost ($<5) | Yellow: Medium Cost ($5-10) | Red: High Cost ($>10)</sub>",
            scene=dict(
                xaxis_title="Width (m)",
                yaxis_title="Length (m)",
                zaxis_title="Height (m)",
                aspectmode='data'
            ),
            width=1000,
            height=800,
            showlegend=True
        )
        
        return fig
    
    def create_cost_breakdown_chart(
        self, routes: List[OptimalRoute]
    ) -> go.Figure:
        """
        Create stacked bar chart showing cost breakdown.
        
        Args:
            routes: List of optimal routes
            
        Returns:
            Plotly Figure
        """
        # Prepare data
        items = [r.product.item_id for r in routes[:20]]  # Top 20
        
        base_costs = [r.base_distance_cost for r in routes[:20]]
        weight_costs = [r.weight_cost for r in routes[:20]]
        fragility_costs = [r.fragility_cost for r in routes[:20]]
        size_costs = [r.size_cost for r in routes[:20]]
        access_costs = [r.access_point_cost for r in routes[:20]]
        handling_costs = [r.handling_cost for r in routes[:20]]
        time_costs = [r.time_cost for r in routes[:20]]
        
        # Create stacked bar chart
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            name='Base Distance',
            x=items,
            y=base_costs,
            marker_color='lightblue'
        ))
        
        fig.add_trace(go.Bar(
            name='Weight Penalty',
            x=items,
            y=weight_costs,
            marker_color='orange'
        ))
        
        fig.add_trace(go.Bar(
            name='Fragility Penalty',
            x=items,
            y=fragility_costs,
            marker_color='pink'
        ))
        
        fig.add_trace(go.Bar(
            name='Size Penalty',
            x=items,
            y=size_costs,
            marker_color='yellow'
        ))
        
        fig.add_trace(go.Bar(
            name='Access Point',
            x=items,
            y=access_costs,
            marker_color='purple'
        ))
        
        fig.add_trace(go.Bar(
            name='Handling',
            x=items,
            y=handling_costs,
            marker_color='green'
        ))
        
        fig.add_trace(go.Bar(
            name='Time',
            x=items,
            y=time_costs,
            marker_color='red'
        ))
        
        fig.update_layout(
            title="Cost Breakdown by Product (Top 20)",
            xaxis_title="Product ID",
            yaxis_title="Cost ($)",
            barmode='stack',
            width=1200,
            height=600
        )
        
        return fig
    
    def _format_location(self, position: Position3D) -> str:
        """Format position as human-readable location"""
        return f"({position.x:.1f}, {position.y:.1f}, {position.z:.1f})"
    
    def _calculate_cost_grid_from_routes(
        self,
        x_grid: np.ndarray,
        y_grid: np.ndarray,
        products: List[Product],
        routes: List[OptimalRoute]
    ) -> np.ndarray:
        """Calculate cost grid from actual route data"""
        cost_grid = np.zeros((len(x_grid), len(y_grid)))
        
        # Create mapping from position to cost
        position_costs = {}
        for product, route in zip(products, routes):
            if product.position:
                key = (
                    round(product.position.x),
                    round(product.position.y)
                )
                position_costs[key] = route.total_cost
        
        # Interpolate to grid
        for i, x in enumerate(x_grid):
            for j, y in enumerate(y_grid):
                # Find nearest known cost
                min_dist = float('inf')
                nearest_cost = 5.0  # Default
                
                for (px, py), cost in position_costs.items():
                    dist = np.sqrt((x - px)**2 + (y - py)**2)
                    if dist < min_dist:
                        min_dist = dist
                        nearest_cost = cost
                
                cost_grid[i, j] = nearest_cost
        
        return cost_grid
    
    def _estimate_cost_grid(
        self, x_grid: np.ndarray, y_grid: np.ndarray
    ) -> np.ndarray:
        """Estimate cost grid based on distance to exits"""
        cost_grid = np.zeros((len(x_grid), len(y_grid)))
        
        if not self.warehouse or not self.warehouse.exit_points:
            return cost_grid + 5.0  # Default cost
        
        for i, x in enumerate(x_grid):
            for j, y in enumerate(y_grid):
                # Find minimum distance to any exit
                min_dist = float('inf')
                
                for exit_point in self.warehouse.exit_points:
                    dx = x - exit_point.position.x
                    dy = y - exit_point.position.y
                    dist = np.sqrt(dx**2 + dy**2)
                    
                    if dist < min_dist:
                        min_dist = dist
                
                # Estimate cost based on distance
                # Base cost + distance cost + typical exit cost
                cost_grid[i, j] = 0.10 * min_dist + 2.5
        
        return cost_grid
