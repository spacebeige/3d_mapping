"""
Chart Visualizations for Warehouse Analytics

Creates utilization charts, cluster analysis plots, and performance dashboards.
"""

from typing import List, Dict, Optional, Any
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend

from models.warehouse import Product
from optimization.clustering import ProductClusterer


class WarehouseCharts:
    """Generate various charts for warehouse analytics"""
    
    @staticmethod
    def create_utilization_chart(
        utilization: Dict[str, Dict[str, float]],
        title: str = "Zone Space Utilization"
    ) -> go.Figure:
        """
        Create interactive utilization chart.
        
        Args:
            utilization: Zone utilization data
            title: Chart title
            
        Returns:
            Plotly Figure
        """
        zones = list(utilization.keys())
        used = [utilization[z]["used"] for z in zones]
        total = [utilization[z]["limit"] for z in zones]
        percent = [utilization[z]["percent"] for z in zones]
        
        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=("Capacity vs Usage", "Utilization Distribution"),
            specs=[[{"type": "bar"}, {"type": "pie"}]]
        )
        
        # Bar chart
        fig.add_trace(
            go.Bar(
                x=zones,
                y=total,
                name="Capacity",
                marker_color='lightgray',
                opacity=0.5,
                text=[f"{t:,.0f} m³" for t in total],
                textposition='outside'
            ),
            row=1, col=1
        )
        
        fig.add_trace(
            go.Bar(
                x=zones,
                y=used,
                name="Used",
                marker_color='steelblue',
                text=[f"{u:,.0f} m³<br>({p:.1f}%)" for u, p in zip(used, percent)],
                textposition='outside'
            ),
            row=1, col=1
        )
        
        # Pie chart
        fig.add_trace(
            go.Pie(
                labels=[f"Zone {z} ({p:.1f}%)" for z, p in zip(zones, percent)],
                values=used,
                hole=0.4,
                marker=dict(colors=['#4caf50', '#2196f3', '#ff9800', '#f44336'])
            ),
            row=1, col=2
        )
        
        # Update layout
        total_used = sum(used)
        total_capacity = sum(total)
        utilization_percent = (total_used / total_capacity * 100) if total_capacity > 0 else 0
        
        fig.update_layout(
            title=dict(
                text=f"{title}<br><sub>Total: {total_capacity:,.0f} m³ | "
                     f"Used: {total_used:,.0f} m³ ({utilization_percent:.1f}%)</sub>",
                x=0.5,
                xanchor='center'
            ),
            height=500,
            showlegend=True
        )
        
        fig.update_xaxes(title_text="Zone", row=1, col=1)
        fig.update_yaxes(title_text="Space (m³)", row=1, col=1)
        
        return fig
    
    @staticmethod
    def create_cluster_scatter(
        df: pd.DataFrame,
        x_col: str = "daily_demand",
        y_col: str = "profit_per_unit",
        color_col: str = "cluster",
        title: str = "Product Clusters"
    ) -> go.Figure:
        """
        Create scatter plot for cluster visualization.
        
        Args:
            df: Dataframe with clustering results
            x_col: Column for x-axis
            y_col: Column for y-axis
            color_col: Column for color coding
            title: Chart title
            
        Returns:
            Plotly Figure
        """
        if x_col not in df.columns or y_col not in df.columns:
            # Fallback to available columns
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            if len(numeric_cols) >= 2:
                x_col = numeric_cols[0]
                y_col = numeric_cols[1]
            else:
                raise ValueError("Not enough numeric columns for scatter plot")
        
        fig = go.Figure()
        
        # Add scatter by cluster
        if color_col in df.columns and "cluster_name" in df.columns:
            for cluster_name in df["cluster_name"].unique():
                cluster_df = df[df["cluster_name"] == cluster_name]
                
                fig.add_trace(go.Scatter(
                    x=cluster_df[x_col],
                    y=cluster_df[y_col],
                    mode='markers',
                    name=cluster_name,
                    marker=dict(size=8, opacity=0.7),
                    text=cluster_df.get("description", cluster_df.get("item_id", "")),
                    hovertemplate=f'<b>%{{text}}</b><br>{x_col}: %{{x}}<br>{y_col}: %{{y}}<extra></extra>'
                ))
        else:
            fig.add_trace(go.Scatter(
                x=df[x_col],
                y=df[y_col],
                mode='markers',
                marker=dict(size=8, opacity=0.7, color=df.get(color_col, 'blue')),
                text=df.get("description", df.get("item_id", "")),
                hovertemplate=f'<b>%{{text}}</b><br>{x_col}: %{{x}}<br>{y_col}: %{{y}}<extra></extra>'
            ))
        
        fig.update_layout(
            title=title,
            xaxis_title=x_col.replace('_', ' ').title(),
            yaxis_title=y_col.replace('_', ' ').title(),
            height=600,
            hovermode='closest'
        )
        
        return fig
    
    @staticmethod
    def create_zone_cluster_heatmap(
        df: pd.DataFrame,
        title: str = "Zone-Cluster Distribution"
    ) -> go.Figure:
        """
        Create heatmap showing distribution of clusters across zones.
        
        Args:
            df: Dataframe with zone and cluster assignments
            title: Chart title
            
        Returns:
            Plotly Figure
        """
        if "final_zone" not in df.columns or "cluster_name" not in df.columns:
            raise ValueError("DataFrame must have 'final_zone' and 'cluster_name' columns")
        
        # Create cross-tabulation
        crosstab = pd.crosstab(df["final_zone"], df["cluster_name"])
        
        fig = go.Figure(data=go.Heatmap(
            z=crosstab.values,
            x=crosstab.columns,
            y=crosstab.index,
            colorscale='Viridis',
            text=crosstab.values,
            texttemplate='%{text}',
            textfont={"size": 12},
            hovertemplate='Zone: %{y}<br>Cluster: %{x}<br>Count: %{z}<extra></extra>'
        ))
        
        fig.update_layout(
            title=title,
            xaxis_title="Cluster Type",
            yaxis_title="Warehouse Zone",
            height=500
        )
        
        return fig
    
    @staticmethod
    def create_allocation_summary(
        df: pd.DataFrame,
        title: str = "Allocation Summary by Zone"
    ) -> go.Figure:
        """
        Create summary charts for allocation results.
        
        Args:
            df: Dataframe with allocation results
            title: Chart title
            
        Returns:
            Plotly Figure
        """
        if "final_zone" not in df.columns:
            raise ValueError("DataFrame must have 'final_zone' column")
        
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                "Item Count by Zone",
                "Total Value by Zone",
                "Average Profit by Zone",
                "Size Distribution by Zone"
            ),
            specs=[
                [{"type": "bar"}, {"type": "bar"}],
                [{"type": "bar"}, {"type": "box"}]
            ]
        )
        
        # Count by zone
        zone_counts = df["final_zone"].value_counts().sort_index()
        fig.add_trace(
            go.Bar(
                x=zone_counts.index,
                y=zone_counts.values,
                marker_color='steelblue',
                text=zone_counts.values,
                textposition='outside'
            ),
            row=1, col=1
        )
        
        # Total value by zone
        if "profit_per_unit" in df.columns and "stock_level" in df.columns:
            df["total_value"] = df["profit_per_unit"] * df["stock_level"]
            zone_values = df.groupby("final_zone")["total_value"].sum().sort_index()
            
            fig.add_trace(
                go.Bar(
                    x=zone_values.index,
                    y=zone_values.values,
                    marker_color='#4caf50',
                    text=[f"${v:,.0f}" for v in zone_values.values],
                    textposition='outside'
                ),
                row=1, col=2
            )
        
        # Average profit by zone
        if "profit_per_unit" in df.columns:
            zone_profits = df.groupby("final_zone")["profit_per_unit"].mean().sort_index()
            
            fig.add_trace(
                go.Bar(
                    x=zone_profits.index,
                    y=zone_profits.values,
                    marker_color='#ff9800',
                    text=[f"${v:.2f}" for v in zone_profits.values],
                    textposition='outside'
                ),
                row=2, col=1
            )
        
        # Size distribution by zone
        if "size_score" in df.columns:
            for zone in sorted(df["final_zone"].unique()):
                zone_data = df[df["final_zone"] == zone]["size_score"]
                
                fig.add_trace(
                    go.Box(
                        y=zone_data,
                        name=f"Zone {zone}",
                        boxmean='sd'
                    ),
                    row=2, col=2
                )
        
        fig.update_layout(
            title=title,
            height=800,
            showlegend=False
        )
        
        fig.update_yaxes(title_text="Count", row=1, col=1)
        fig.update_yaxes(title_text="Total Value ($)", row=1, col=2)
        fig.update_yaxes(title_text="Avg Profit ($)", row=2, col=1)
        fig.update_yaxes(title_text="Size Score", row=2, col=2)
        
        return fig
    
    @staticmethod
    def create_performance_dashboard(
        utilization: Dict[str, Dict[str, float]],
        df_products: pd.DataFrame,
        metrics: Optional[Dict[str, Any]] = None
    ) -> go.Figure:
        """
        Create comprehensive performance dashboard.
        
        Args:
            utilization: Zone utilization data
            df_products: Products dataframe
            metrics: Additional metrics to display
            
        Returns:
            Plotly Figure
        """
        fig = make_subplots(
            rows=2, cols=3,
            subplot_titles=(
                "Zone Utilization",
                "Product Distribution",
                "Value Distribution",
                "Profit vs Demand",
                "Category Breakdown",
                "Performance Metrics"
            ),
            specs=[
                [{"type": "bar"}, {"type": "pie"}, {"type": "pie"}],
                [{"type": "scatter"}, {"type": "bar"}, {"type": "indicator"}]
            ]
        )
        
        # Zone utilization bar
        zones = list(utilization.keys())
        percents = [utilization[z]["percent"] for z in zones]
        
        fig.add_trace(
            go.Bar(
                x=zones,
                y=percents,
                marker_color=['#4caf50' if p < 75 else '#ff9800' if p < 90 else '#f44336' for p in percents],
                text=[f"{p:.1f}%" for p in percents],
                textposition='outside'
            ),
            row=1, col=1
        )
        
        # Product distribution pie
        if "final_zone" in df_products.columns:
            zone_counts = df_products["final_zone"].value_counts()
            fig.add_trace(
                go.Pie(
                    labels=zone_counts.index,
                    values=zone_counts.values,
                    hole=0.3
                ),
                row=1, col=2
            )
        
        # Value distribution pie
        if "profit_per_unit" in df_products.columns and "stock_level" in df_products.columns and "final_zone" in df_products.columns:
            df_products["value"] = df_products["profit_per_unit"] * df_products["stock_level"]
            zone_values = df_products.groupby("final_zone")["value"].sum()
            
            fig.add_trace(
                go.Pie(
                    labels=zone_values.index,
                    values=zone_values.values,
                    hole=0.3
                ),
                row=1, col=3
            )
        
        # Profit vs Demand scatter
        if "profit_per_unit" in df_products.columns and "daily_demand" in df_products.columns:
            fig.add_trace(
                go.Scatter(
                    x=df_products["daily_demand"],
                    y=df_products["profit_per_unit"],
                    mode='markers',
                    marker=dict(size=5, opacity=0.6, color='steelblue')
                ),
                row=2, col=1
            )
        
        # Category breakdown
        if "category" in df_products.columns:
            category_counts = df_products["category"].value_counts().head(10)
            fig.add_trace(
                go.Bar(
                    x=category_counts.values,
                    y=category_counts.index,
                    orientation='h',
                    marker_color='#2196f3'
                ),
                row=2, col=2
            )
        
        # Performance indicator
        total_products = len(df_products)
        total_value = df_products.get("value", pd.Series([0])).sum()
        
        fig.add_trace(
            go.Indicator(
                mode="number+delta",
                value=total_products,
                title={"text": "Total Products"},
                domain={'x': [0, 1], 'y': [0, 1]}
            ),
            row=2, col=3
        )
        
        fig.update_layout(
            title="Warehouse Performance Dashboard",
            height=900,
            showlegend=False
        )
        
        fig.update_yaxes(title_text="Utilization %", row=1, col=1)
        fig.update_xaxes(title_text="Daily Demand", row=2, col=1)
        fig.update_yaxes(title_text="Profit per Unit", row=2, col=1)
        fig.update_xaxes(title_text="Count", row=2, col=2)
        
        return fig
