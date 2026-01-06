"""
Product Clustering Module

K-means clustering for warehouse products to identify patterns and optimize storage.
"""

from typing import List, Dict, Optional
import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

from models.warehouse import Product


class ProductClusterer:
    """
    Cluster products using K-means to identify storage patterns.
    """
    
    def __init__(self, n_clusters: int = 5):
        """
        Initialize clusterer.
        
        Args:
            n_clusters: Number of clusters
        """
        self.n_clusters = n_clusters
        self.scaler = StandardScaler()
        self.model: Optional[KMeans] = None
        self.feature_names: List[str] = []
        
        self.cluster_names = {
            0: "Low Value",
            1: "Medium Value",
            2: "High Value",
            3: "Premium",
            4: "Economy",
            5: "Standard",
            6: "Premium Plus",
            7: "Bulk Items",
            8: "Specialty",
            9: "Seasonal"
        }
    
    def fit(self, df: pd.DataFrame, features: Optional[List[str]] = None) -> "ProductClusterer":
        """
        Fit clustering model on product data.
        
        Args:
            df: Products dataframe
            features: Features to use for clustering
            
        Returns:
            Self for chaining
        """
        # Determine features to use
        if features is None:
            available_features = []
            for feature in ["profit_per_unit", "daily_demand", "size_score", "stock_level", "turnover_ratio"]:
                if feature in df.columns:
                    available_features.append(feature)
            features = available_features
        
        if not features:
            raise ValueError("No suitable features available for clustering")
        
        self.feature_names = features
        
        # Prepare data
        X = df[features].fillna(0)
        X_scaled = self.scaler.fit_transform(X)
        
        # Fit K-means
        self.model = KMeans(n_clusters=self.n_clusters, random_state=42, n_init=10)
        self.model.fit(X_scaled)
        
        return self
    
    def predict(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Predict cluster labels for products.
        
        Args:
            df: Products dataframe
            
        Returns:
            DataFrame with cluster assignments
        """
        if self.model is None:
            raise ValueError("Model not fitted. Call fit() first.")
        
        df = df.copy()
        
        # Prepare data
        X = df[self.feature_names].fillna(0)
        X_scaled = self.scaler.transform(X)
        
        # Predict
        cluster_labels = self.model.predict(X_scaled)
        
        df["cluster"] = cluster_labels
        df["cluster_name"] = df["cluster"].map(
            lambda x: self.cluster_names.get(x, f"Cluster {x}")
        )
        
        return df
    
    def fit_predict(self, df: pd.DataFrame, features: Optional[List[str]] = None) -> pd.DataFrame:
        """
        Fit model and predict in one step.
        
        Args:
            df: Products dataframe
            features: Features to use
            
        Returns:
            DataFrame with cluster assignments
        """
        self.fit(df, features)
        return self.predict(df)
    
    def get_cluster_summary(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Get summary statistics for each cluster.
        
        Args:
            df: Clustered products dataframe
            
        Returns:
            Summary dataframe
        """
        if "cluster" not in df.columns:
            raise ValueError("DataFrame must have 'cluster' column. Call predict() first.")
        
        # Get numeric columns
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        
        # Remove cluster column itself
        if "cluster" in numeric_cols:
            numeric_cols.remove("cluster")
        
        if not numeric_cols:
            return pd.DataFrame()
        
        # Group by cluster name if available
        group_col = "cluster_name" if "cluster_name" in df.columns else "cluster"
        
        summary = df.groupby(group_col)[numeric_cols].agg(['mean', 'std', 'min', 'max'])
        
        return summary
    
    def get_zone_cluster_distribution(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Get distribution of clusters across zones.
        
        Args:
            df: Clustered products with zone assignments
            
        Returns:
            Cross-tabulation of zones and clusters
        """
        if "cluster_name" not in df.columns or "final_zone" not in df.columns:
            raise ValueError("DataFrame must have 'cluster_name' and 'final_zone' columns")
        
        return pd.crosstab(df["final_zone"], df["cluster_name"])
    
    def get_cluster_characteristics(self, df: pd.DataFrame) -> Dict[str, Dict[str, float]]:
        """
        Get detailed characteristics of each cluster.
        
        Args:
            df: Clustered products dataframe
            
        Returns:
            Dictionary of cluster characteristics
        """
        if "cluster_name" not in df.columns:
            raise ValueError("DataFrame must have 'cluster_name' column")
        
        characteristics = {}
        
        for cluster_name in df["cluster_name"].unique():
            cluster_df = df[df["cluster_name"] == cluster_name]
            
            char = {
                "count": len(cluster_df),
                "avg_profit": cluster_df["profit_per_unit"].mean() if "profit_per_unit" in cluster_df else 0,
                "avg_demand": cluster_df["daily_demand"].mean() if "daily_demand" in cluster_df else 0,
                "avg_size": cluster_df["size_score"].mean() if "size_score" in cluster_df else 0,
                "total_value": (
                    cluster_df["profit_per_unit"].sum() * cluster_df["stock_level"].sum()
                    if "profit_per_unit" in cluster_df and "stock_level" in cluster_df
                    else 0
                )
            }
            
            characteristics[cluster_name] = char
        
        return characteristics


def suggest_optimal_clusters(
    df: pd.DataFrame,
    max_clusters: int = 10,
    features: Optional[List[str]] = None
) -> int:
    """
    Suggest optimal number of clusters using elbow method.
    
    Args:
        df: Products dataframe
        max_clusters: Maximum clusters to test
        features: Features to use
        
    Returns:
        Suggested number of clusters
    """
    if features is None:
        features = []
        for feature in ["profit_per_unit", "daily_demand", "size_score"]:
            if feature in df.columns:
                features.append(feature)
    
    if not features:
        return 5  # Default
    
    # Prepare data
    X = df[features].fillna(0)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Calculate inertia for different cluster counts
    inertias = []
    K_range = range(2, min(max_clusters + 1, len(df)))
    
    for k in K_range:
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
        kmeans.fit(X_scaled)
        inertias.append(kmeans.inertia_)
    
    # Find elbow point (simplified)
    if len(inertias) < 3:
        return 5
    
    # Calculate rate of change
    deltas = np.diff(inertias)
    delta_deltas = np.diff(deltas)
    
    # Find point where rate of change slows
    if len(delta_deltas) > 0:
        elbow_idx = np.argmax(delta_deltas) + 2  # +2 because of double diff
        return min(K_range[elbow_idx], 8)  # Cap at 8
    
    return 5
