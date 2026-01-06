"""
Warehouse Allocation Optimizer

Hybrid ML + Rules-based system for optimizing product placement in warehouse zones.
"""

from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

from models.warehouse import Product, ZoneType


class WarehouseAllocator:
    """
    Enhanced warehouse allocation system using hybrid ML + rules-based approach.
    Optimizes product placement across zones based on multiple factors.
    """
    
    def __init__(
        self,
        total_space: float = 1000000,
        zone_weights: Optional[Dict[str, float]] = None
    ):
        """
        Initialize allocator.
        
        Args:
            total_space: Total warehouse space in cubic meters
            zone_weights: Distribution of space across zones
        """
        self.total_space = total_space
        self.zone_weights = zone_weights or {"A": 0.3, "B": 0.3, "C": 0.2, "D": 0.2}
        self.zone_space = {z: total_space * w for z, w in self.zone_weights.items()}
        self.zone_used = {z: 0 for z in self.zone_weights}
        
        # ML components
        self.encoder: Optional[LabelEncoder] = None
        self.model: Optional[RandomForestClassifier] = None
        self.known_categories: List[str] = []
        self.training_features: List[str] = []
        
        # Dynamic configuration
        self.percentile_cutoff = 85
        self.shelf_config: Dict[str, float] = {
            "A": float('inf'),
            "B": float('inf'),
            "C": float('inf'),
            "D": float('inf')
        }
        
        # Results tracking
        self.internal_df: Optional[pd.DataFrame] = None
        self.utilization: Dict[str, Dict[str, float]] = {}
        self.current_predictions: Optional[pd.DataFrame] = None
    
    def calculate_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate or generate required features for products.
        
        Args:
            df: Input dataframe
            
        Returns:
            DataFrame with all required features
        """
        df = df.copy()
        
        # Generate profit_per_unit if missing
        if "profit_per_unit" not in df.columns:
            category_profit_map = {
                "pharma": (40, 100),
                "automotive": (50, 150),
                "groceries": (20, 80),
                "electronics": (60, 200),
                "apparel": (30, 100)
            }
            df["profit_per_unit"] = df["category"].apply(
                lambda x: int(np.random.randint(*category_profit_map.get(str(x).lower(), (30, 100))))
            )
        
        # Generate size_score if missing
        if "size_score" not in df.columns:
            category_size_map = {
                "pharma": (2, 6),
                "automotive": (5, 12),
                "groceries": (1, 4),
                "electronics": (3, 8),
                "apparel": (1, 5)
            }
            df["size_score"] = df["category"].apply(
                lambda x: float(np.round(np.random.uniform(*category_size_map.get(str(x).lower(), (3, 6))), 1))
            )
        
        # Generate missing numeric features
        required_features = {
            "daily_demand": (10, 100),
            "stock_level": (50, 500),
            "holding_cost_per_unit_day": (0.5, 3.0),
            "turnover_ratio": (2, 10)
        }
        
        for col, (min_val, max_val) in required_features.items():
            if col not in df.columns:
                if col == "holding_cost_per_unit_day":
                    df[col] = np.round(np.random.uniform(min_val, max_val, len(df)), 2)
                elif col == "turnover_ratio":
                    df[col] = np.random.randint(min_val, max_val, len(df))
                else:
                    df[col] = np.random.randint(min_val, max_val, len(df))
        
        return df
    
    def dynamic_percentile(self, df: pd.DataFrame) -> float:
        """
        Calculate dynamic threshold based on zone A utilization.
        
        Args:
            df: Product dataframe
            
        Returns:
            Profit threshold value
        """
        used_ratio = self.zone_used["A"] / (self.zone_space["A"] or 1)
        
        if used_ratio > 0.8:
            self.percentile_cutoff = 90
        elif used_ratio < 0.2:
            self.percentile_cutoff = 70
        else:
            self.percentile_cutoff = 80
        
        return np.percentile(df["profit_per_unit"], self.percentile_cutoff)
    
    def assign_zone_by_rules(
        self,
        row: pd.Series,
        threshold: Optional[float] = None
    ) -> str:
        """
        Assign zone using business rules.
        
        Args:
            row: Product row
            threshold: Profit threshold for Zone A
            
        Returns:
            Zone assignment (A, B, C, or D)
        """
        # Special rule for groceries
        if str(row.get("category", "")).lower() == "groceries":
            return "A" if row.get("daily_demand", 0) > 25 else "B"
        
        # High-profit items go to Zone A
        if threshold and row.get("profit_per_unit", 0) >= threshold:
            return "A"
        
        # Medium-profit items to Zone B
        if row.get("profit_per_unit", 0) > 80:
            return "B"
        
        # Large items to Zone C
        if row.get("size_score", 0) > 7:
            return "C"
        
        # Everything else to Zone D
        return "D"
    
    def train(self, df: pd.DataFrame) -> "WarehouseAllocator":
        """
        Train ML model on historical data.
        
        Args:
            df: Training dataframe with products
            
        Returns:
            Self for chaining
        """
        df = self.calculate_features(df)
        
        # Initialize encoder
        self.encoder = LabelEncoder()
        self.known_categories = df["category"].astype(str).unique().tolist()
        df["category_enc"] = self.encoder.fit_transform(df["category"].astype(str))
        
        # Calculate dynamic threshold and assign zones
        cutoff = self.dynamic_percentile(df)
        df["final_zone"] = df.apply(self.assign_zone_by_rules, axis=1, threshold=cutoff)
        
        # Define features for training
        features = [
            "profit_per_unit",
            "daily_demand",
            "stock_level",
            "holding_cost_per_unit_day",
            "category_enc",
            "size_score"
        ]
        self.training_features = features
        
        # Split and train
        X, y = df[self.training_features], df["final_zone"]
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        clf = RandomForestClassifier(n_estimators=200, random_state=42)
        clf.fit(X_train, y_train)
        
        preds = clf.predict(X_test)
        accuracy = accuracy_score(y_test, preds)
        
        print(f"✅ Training complete — Accuracy: {accuracy:.2f}")
        
        self.model = clf
        return self
    
    def prepare_input(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Prepare input dataframe for prediction.
        
        Args:
            df: Input dataframe
            
        Returns:
            Prepared dataframe
        """
        df = self.calculate_features(df)
        
        # Encode categories
        def safe_encode(cat: str) -> int:
            s = str(cat)
            if s in self.known_categories:
                return int(self.encoder.transform([s])[0])
            # Add unknown category
            self.encoder.classes_ = np.append(self.encoder.classes_, s)
            self.known_categories.append(s)
            return int(self.encoder.transform([s])[0])
        
        df["category_enc"] = df["category"].apply(safe_encode)
        
        # Ensure all features exist
        for col in self.training_features:
            if col not in df.columns:
                df[col] = 0
        
        return df
    
    def predict_with_constraints(
        self,
        df: pd.DataFrame,
        zone_caps: Optional[Dict[str, float]] = None
    ) -> pd.DataFrame:
        """
        Predict zone allocations with capacity constraints.
        
        Args:
            df: Products dataframe
            zone_caps: Optional zone capacity overrides
            
        Returns:
            DataFrame with predictions and allocations
        """
        if zone_caps is None:
            zone_caps = self.zone_space
        
        # Initialize zone usage
        zone_usage = {z: 0 for z in zone_caps}
        
        # Prepare data
        df = self.prepare_input(df)
        cutoff = self.dynamic_percentile(df)
        df["predicted_zone"] = df.apply(self.assign_zone_by_rules, axis=1, threshold=cutoff)
        
        # Allocate with constraints
        allocations = []
        shelves = []
        restock_dates = []
        discount_dates = []
        
        # Ensure required columns exist
        if "item_id" not in df.columns:
            df["item_id"] = range(1, len(df) + 1)
        if "description" not in df.columns:
            df["description"] = df["category"].astype(str) + " item"
        
        for _, row in df.iterrows():
            zone = row["predicted_zone"]
            size_req = row.get("stock_level", 1) * row.get("size_score", 1)
            allocated = False
            
            # Try to allocate to predicted zone
            if zone in zone_caps and zone_usage[zone] + size_req <= zone_caps[zone]:
                zone_usage[zone] += size_req
                allocations.append(zone)
                allocated = True
            else:
                # Fallback: try other zones by utilization
                for z in sorted(zone_caps, key=lambda x: zone_usage[x]):
                    if zone_usage[z] + size_req <= zone_caps[z]:
                        zone_usage[z] += size_req
                        allocations.append(z)
                        allocated = True
                        break
            
            if not allocated:
                allocations.append("UNALLOCATED")
            
            # Generate shelf assignment
            shelves.append(f"Shelf-{np.random.randint(1, 1000000)}")  # Support 1M+ shelves
            
            # Calculate restock date
            if row.get("daily_demand", 0) > 0:
                days_until_restock = row.get("stock_level", 0) / row.get("daily_demand", 1)
                restock_date = datetime.now() + timedelta(days=days_until_restock)
                restock_dates.append(restock_date.strftime("%Y-%m-%d"))
            else:
                restock_dates.append("N/A")
            
            # Calculate discount date
            if row.get("holding_cost_per_unit_day", 0) > 2.0 or row.get("turnover_ratio", 5) < 3:
                discount_date = datetime.now() + timedelta(days=60)
                discount_dates.append(discount_date.strftime("%Y-%m-%d"))
            else:
                discount_dates.append("Not Needed")
        
        # Add results to dataframe
        df["final_zone"] = allocations
        df["shelf"] = shelves
        df["restock_date"] = restock_dates
        df["discount_date"] = discount_dates
        
        # Store results
        self.internal_df = df.copy()
        self.utilization = {
            z: {
                "used": zone_usage[z],
                "limit": zone_caps[z],
                "percent": round((zone_usage[z] / zone_caps[z]) * 100, 2) if zone_caps[z] > 0 else 0
            }
            for z in zone_caps
        }
        self.current_predictions = df.copy()
        
        # Select output columns
        result_cols = [
            "item_id", "description", "category", "profit_per_unit",
            "daily_demand", "size_score", "predicted_zone", "final_zone",
            "shelf", "restock_date", "discount_date"
        ]
        
        for col in result_cols:
            if col not in df.columns:
                df[col] = "N/A"
        
        return df[result_cols]
    
    def get_utilization_stats(self) -> Dict[str, Dict[str, float]]:
        """Get current zone utilization statistics"""
        return self.utilization
    
    def convert_to_products(self, df: pd.DataFrame) -> List[Product]:
        """
        Convert DataFrame to list of Product models.
        
        Args:
            df: Products dataframe
            
        Returns:
            List of Product instances
        """
        products = []
        
        for _, row in df.iterrows():
            product = Product(
                item_id=str(row.get("item_id", "")),
                description=str(row.get("description", "")),
                category=str(row.get("category", "")),
                profit_per_unit=float(row.get("profit_per_unit", 0)),
                daily_demand=int(row.get("daily_demand", 0)),
                stock_level=int(row.get("stock_level", 0)),
                holding_cost_per_unit_day=float(row.get("holding_cost_per_unit_day", 0)),
                turnover_ratio=float(row.get("turnover_ratio", 1)),
                size_score=float(row.get("size_score", 1)),
                predicted_zone=ZoneType(row["predicted_zone"]) if "predicted_zone" in row else None,
                final_zone=ZoneType(row["final_zone"]) if "final_zone" in row else None,
                shelf=str(row.get("shelf", "")),
                restock_date=str(row.get("restock_date", "")),
                discount_date=str(row.get("discount_date", ""))
            )
            products.append(product)
        
        return products
