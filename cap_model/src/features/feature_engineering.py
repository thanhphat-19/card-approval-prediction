"""
Feature engineering and preprocessing module
"""

from pathlib import Path
from typing import List, Tuple

import joblib
import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import (
    LabelEncoder,
    MinMaxScaler,
    OneHotEncoder,
    RobustScaler,
    StandardScaler,
)


class FeatureEngineer:
    """Feature engineering and preprocessing pipeline"""

    def __init__(self, config: dict):
        """
        Initialize FeatureEngineer

        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.numerical_features = config["features"]["numerical_features"]
        self.categorical_features = config["features"]["categorical_features"]
        self.target = config["features"]["target"]

        # Initialize transformers
        self.scaler = None
        self.encoders = {}
        self.imputers = {}
        self.feature_names = []

    def fit_transform(
        self, df: pd.DataFrame
    ) -> Tuple[np.ndarray, np.ndarray, List[str]]:
        """
        Fit and transform features (use on training data)

        Args:
            df: Input DataFrame

        Returns:
            Tuple of (X, y, feature_names)
        """
        print("\n" + "=" * 60)
        print("FEATURE ENGINEERING")
        print("=" * 60)

        df = df.copy()

        # 1. Handle missing values
        df = self._handle_missing_values(df, fit=True)

        # 2. Create derived features
        df = self._create_derived_features(df)

        # 3. Encode categorical variables
        df = self._encode_categorical(df, fit=True)

        # 4. Scale numerical features
        X = self._scale_features(df, fit=True)

        # 5. Extract target
        y = df[self.target].values

        print(f"\nFinal feature matrix shape: {X.shape}")
        print(f"Target distribution: {np.bincount(y)}")

        return X, y, self.feature_names

    def transform(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """
        Transform features (use on validation/test data)

        Args:
            df: Input DataFrame

        Returns:
            Tuple of (X, y)
        """
        df = df.copy()

        # Apply same transformations
        df = self._handle_missing_values(df, fit=False)
        df = self._create_derived_features(df)
        df = self._encode_categorical(df, fit=False)
        X = self._scale_features(df, fit=False)
        y = df[self.target].values

        return X, y

    def _handle_missing_values(
        self, df: pd.DataFrame, fit: bool = False
    ) -> pd.DataFrame:
        """Handle missing values in numerical and categorical features"""

        print("\n1. Handling missing values...")

        # Numerical features
        if self.numerical_features:
            if fit:
                strategy = self.config["features"]["handle_missing"]
                self.imputers["numerical"] = SimpleImputer(strategy=strategy)
                df[self.numerical_features] = self.imputers["numerical"].fit_transform(
                    df[self.numerical_features]
                )
            else:
                df[self.numerical_features] = self.imputers["numerical"].transform(
                    df[self.numerical_features]
                )

        # Categorical features - fill with mode
        if self.categorical_features:
            if fit:
                self.imputers["categorical"] = SimpleImputer(strategy="most_frequent")
                df[self.categorical_features] = self.imputers[
                    "categorical"
                ].fit_transform(df[self.categorical_features])
            else:
                df[self.categorical_features] = self.imputers["categorical"].transform(
                    df[self.categorical_features]
                )

        missing_counts = df.isnull().sum()
        if missing_counts.sum() > 0:
            print(f"   Remaining missing values: {missing_counts[missing_counts > 0]}")
        else:
            print(f"   ✓ No missing values remaining")

        return df

    def _create_derived_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create derived features based on domain knowledge"""

        print("\n2. Creating derived features...")

        # Credit utilization ratio
        if (
            "total_credit_limit" in df.columns
            and "num_existing_credit_cards" in df.columns
        ):
            df["credit_limit_per_card"] = df["total_credit_limit"] / (
                df["num_existing_credit_cards"] + 1
            )

        # Income to credit ratio
        if "annual_income" in df.columns and "total_credit_limit" in df.columns:
            df["income_to_credit_ratio"] = df["annual_income"] / (
                df["total_credit_limit"] + 1
            )

        # Age groups
        if "age" in df.columns:
            df["age_group"] = pd.cut(
                df["age"],
                bins=[0, 25, 35, 50, 100],
                labels=["young", "adult", "middle_age", "senior"],
            )

        # Income groups
        if "annual_income" in df.columns:
            df["income_group"] = pd.cut(
                df["annual_income"],
                bins=[0, 30000, 60000, 100000, float("inf")],
                labels=["low", "medium", "high", "very_high"],
            )

        # Credit score groups
        if "credit_score" in df.columns:
            df["credit_score_group"] = pd.cut(
                df["credit_score"],
                bins=[0, 580, 670, 740, 800, 850],
                labels=["poor", "fair", "good", "very_good", "excellent"],
            )

        new_features = [
            col
            for col in df.columns
            if col
            not in self.numerical_features + self.categorical_features + [self.target]
        ]
        print(f"   Created {len(new_features)} derived features: {new_features}")

        # Update categorical features list
        self.categorical_features.extend(
            [
                col
                for col in new_features
                if df[col].dtype == "object"
                or isinstance(df[col].dtype, pd.CategoricalDtype)
            ]
        )
        self.numerical_features.extend(
            [col for col in new_features if col not in self.categorical_features]
        )

        return df

    def _encode_categorical(self, df: pd.DataFrame, fit: bool = False) -> pd.DataFrame:
        """Encode categorical variables"""

        print("\n3. Encoding categorical variables...")

        encoding_method = self.config["features"]["encoding_method"]

        if encoding_method == "onehot":
            if fit:
                # Use pd.get_dummies for one-hot encoding
                df_encoded = pd.get_dummies(
                    df,
                    columns=self.categorical_features,
                    prefix=self.categorical_features,
                    drop_first=True,
                )
                # Store the columns for future transformation
                self.encoded_columns = df_encoded.columns.tolist()
            else:
                # Apply same encoding to new data
                df_encoded = pd.get_dummies(
                    df,
                    columns=self.categorical_features,
                    prefix=self.categorical_features,
                    drop_first=True,
                )
                # Align columns with training data
                for col in self.encoded_columns:
                    if col not in df_encoded.columns:
                        df_encoded[col] = 0
                df_encoded = df_encoded[self.encoded_columns]

            print(f"   One-hot encoded {len(self.categorical_features)} features")
            df = df_encoded

        elif encoding_method == "label":
            for col in self.categorical_features:
                if fit:
                    self.encoders[col] = LabelEncoder()
                    df[col] = self.encoders[col].fit_transform(df[col].astype(str))
                else:
                    df[col] = self.encoders[col].transform(df[col].astype(str))
            print(f"   Label encoded {len(self.categorical_features)} features")

        return df

    def _scale_features(self, df: pd.DataFrame, fit: bool = False) -> np.ndarray:
        """Scale numerical features"""

        print("\n4. Scaling numerical features...")

        # Separate features and target
        X_df = df.drop(columns=[self.target])

        scaling_method = self.config["features"]["scaling_method"]

        if fit:
            if scaling_method == "standard":
                self.scaler = StandardScaler()
            elif scaling_method == "minmax":
                self.scaler = MinMaxScaler()
            elif scaling_method == "robust":
                self.scaler = RobustScaler()
            else:
                raise ValueError(f"Unknown scaling method: {scaling_method}")

            X = self.scaler.fit_transform(X_df)
            self.feature_names = X_df.columns.tolist()
            print(f"   Scaled {X.shape[1]} features using {scaling_method} scaling")
        else:
            X = self.scaler.transform(X_df)

        return X

    def save(self, output_dir: str = "models/preprocessors"):
        """Save fitted transformers"""

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Save scaler
        if self.scaler:
            joblib.dump(self.scaler, output_path / "scaler.pkl")

        # Save imputers
        for name, imputer in self.imputers.items():
            joblib.dump(imputer, output_path / f"imputer_{name}.pkl")

        # Save encoders
        for name, encoder in self.encoders.items():
            joblib.dump(encoder, output_path / f"encoder_{name}.pkl")

        # Save feature names
        joblib.dump(self.feature_names, output_path / "feature_names.pkl")

        # Save encoded columns (for one-hot encoding)
        if hasattr(self, "encoded_columns"):
            joblib.dump(self.encoded_columns, output_path / "encoded_columns.pkl")

        print(f"\n✓ Saved preprocessors to {output_path}")

    def load(self, input_dir: str = "models/preprocessors"):
        """Load fitted transformers"""

        input_path = Path(input_dir)

        # Load scaler
        scaler_path = input_path / "scaler.pkl"
        if scaler_path.exists():
            self.scaler = joblib.load(scaler_path)

        # Load imputers
        for imputer_file in input_path.glob("imputer_*.pkl"):
            name = imputer_file.stem.replace("imputer_", "")
            self.imputers[name] = joblib.load(imputer_file)

        # Load encoders
        for encoder_file in input_path.glob("encoder_*.pkl"):
            name = encoder_file.stem.replace("encoder_", "")
            self.encoders[name] = joblib.load(encoder_file)

        # Load feature names
        feature_names_path = input_path / "feature_names.pkl"
        if feature_names_path.exists():
            self.feature_names = joblib.load(feature_names_path)

        # Load encoded columns
        encoded_cols_path = input_path / "encoded_columns.pkl"
        if encoded_cols_path.exists():
            self.encoded_columns = joblib.load(encoded_cols_path)

        print(f"✓ Loaded preprocessors from {input_path}")

    def get_feature_importance_mapping(self) -> dict:
        """Get mapping of feature names for interpretation"""
        return {i: name for i, name in enumerate(self.feature_names)}
