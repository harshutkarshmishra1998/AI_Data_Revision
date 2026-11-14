"""
OpenML Dataset Downloader

Run:
    python -m data.csv.openml_downloader

Supported:
    - Classification
    - Regression
    - Clustering

Features:
    - Centralized configuration
    - Configurable dataset count
    - Minimum / maximum rows
    - Minimum / maximum total features
    - Minimum / maximum categorical features
    - Minimum / maximum numerical features
    - Largest-first / smallest-first
    - Skip previously downloaded datasets
    - Prevent duplicate downloads using OpenML IDs
    - Continue searching after failed datasets
    - Save CSV files directly in the data directory
    - Optional JSON metadata sidecars
"""

# Uncomment with the optional metadata sidecar block in save_dataset().
# import json
import re
from pathlib import Path
from types import SimpleNamespace

import openml
import pandas as pd

# =====================================================
# DIRECTORY CONFIGURATION
# =====================================================

DATA_ROOT = Path("data/csv")
DATA_ROOT.mkdir(parents=True, exist_ok=True)

# =====================================================
# DATASET FILE PATH
# =====================================================

def get_dataset_path(dataset_name, dataset_id):
    dataset_name = re.sub(
        r"[^a-zA-Z0-9_-]+",
        "_",
        str(dataset_name).strip().lower()
    ).strip("_")
    return DATA_ROOT / f"{dataset_name}_{dataset_id}.csv"

# =====================================================
# CHECK EXISTING DOWNLOAD
# =====================================================

def is_dataset_downloaded(dataset_id):

    # Check by OpenML dataset ID.
    # Metadata sidecars are optional while their save block is disabled.

    for data_path in DATA_ROOT.glob(f"*_{dataset_id}.csv"):
        if data_path.is_file() and data_path.stat().st_size > 0:
            return True

    # Also recognize datasets downloaded before CSVs were saved flat.
    for directory in DATA_ROOT.glob(f"*_{dataset_id}"):
        data_path = directory / "data.csv"
        if data_path.is_file() and data_path.stat().st_size > 0:
            return True
    return False

# =====================================================
# DATASET SEARCH
# =====================================================

def search_datasets(args):
    print("\nSearching OpenML datasets...")
    print(f"Problem type: {args.problem}")
    df = openml.datasets.list_datasets(
        output_format="dataframe"
    )
    if df.empty:
        print("No datasets returned by OpenML.")
        return df
    print(f"Available metadata columns: {df.columns.tolist()}")

    # -------------------------------------------------
    # CONVERT NUMERIC METADATA
    # -------------------------------------------------

    numeric_columns = [
        "NumberOfInstances",
        "NumberOfFeatures",
        "NumberOfClasses",
    ]
    for col in numeric_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(
                df[col],
                errors="coerce"
            )

    # -------------------------------------------------
    # FILTER BY ROW COUNT
    # -------------------------------------------------

    df = df[
        df["NumberOfInstances"].between(
            args.min_rows,
            args.max_rows
        )
    ]

    # -------------------------------------------------
    # FILTER BY TOTAL FEATURES
    # -------------------------------------------------

    df = df[
        df["NumberOfFeatures"].between(
            args.min_features,
            args.max_features
        )
    ]

    # -------------------------------------------------
    # PRELIMINARY PROBLEM-TYPE FILTERING
    # -------------------------------------------------

    if "NumberOfClasses" in df.columns:
        classes = df["NumberOfClasses"]
        if args.problem == "classification":
            df = df[
                classes.isna() | (classes > 1)
            ]
        elif args.problem == "regression":
            df = df[
                classes.isna() | (classes == 0)
            ]

    # Clustering does not require a target.

    # -------------------------------------------------
    # SORT DATASETS
    # -------------------------------------------------

    df = df.sort_values(
        "NumberOfInstances",
        ascending=not args.largest_first
    )
    print(f"\nCandidate datasets found: {len(df)}")
    return df

# =====================================================
# IDENTIFY FEATURE TYPES
# =====================================================

def identify_features(X, categorical):
    categorical_cols = set()

    # -------------------------------------------------
    # OPENML CATEGORICAL METADATA
    # -------------------------------------------------

    if categorical is not None:
        for col, is_categorical in zip(
            X.columns,
            categorical
        ):
            if is_categorical:
                categorical_cols.add(col)

    # -------------------------------------------------
    # PANDAS DTYPE DETECTION
    # -------------------------------------------------

    for col in X.columns:
        dtype = X[col].dtype
        if (
            pd.api.types.is_object_dtype(dtype)
            or isinstance(dtype, pd.CategoricalDtype)
            or pd.api.types.is_bool_dtype(dtype)
        ):
            categorical_cols.add(col)

    # -------------------------------------------------
    # NUMERICAL FEATURES
    # -------------------------------------------------

    numerical_cols = [
        col for col in X.columns
        if (
            col not in categorical_cols
            and pd.api.types.is_numeric_dtype(X[col])
        )
    ]
    return list(categorical_cols), numerical_cols

# =====================================================
# VALIDATE TARGET
# =====================================================

def validate_target(y, problem_type, number_of_classes=None):
    if problem_type == "clustering":
        return None
    if y is None:
        raise ValueError("Target column is missing")
    if y.notna().sum() == 0:
        raise ValueError("Target contains only missing values")
    unique_values = y.nunique(dropna=True)
    if unique_values < 2:
        raise ValueError("Target has insufficient unique values")

    # -------------------------------------------------
    # CLASSIFICATION
    # -------------------------------------------------

    if problem_type == "classification":
        if (
            number_of_classes is not None
            and pd.notna(number_of_classes)
            and number_of_classes <= 1
        ):
            raise ValueError(
                "OpenML metadata does not indicate classification"
            )

        # Preserve classification target
        return y

    # -------------------------------------------------
    # REGRESSION
    # -------------------------------------------------

    if problem_type == "regression":
        if (
            number_of_classes is not None
            and pd.notna(number_of_classes)
            and number_of_classes > 0
        ):
            raise ValueError(
                "OpenML metadata identifies this as classification"
            )
        y_numeric = pd.to_numeric(
            y,
            errors="coerce"
        )
        if y_numeric.notna().sum() != y.notna().sum():
            raise ValueError(
                "Regression target contains non-numeric values"
            )
        if y_numeric.nunique(dropna=True) < 2:
            raise ValueError(
                "Regression target has insufficient variation"
            )
        return y_numeric
    raise ValueError(f"Unsupported problem type: {problem_type}")

# =====================================================
# DOWNLOAD SINGLE DATASET
# =====================================================

def download_dataset(dataset_id, args, number_of_classes=None):
    dataset = openml.datasets.get_dataset(
        dataset_id
    )

    # -------------------------------------------------
    # GET TARGET
    # -------------------------------------------------

    target = (
        None
        if args.problem == "clustering"
        else dataset.default_target_attribute
    )
    if args.problem != "clustering" and not target:
        raise ValueError(
            "Dataset does not have a default target attribute"
        )

    # -------------------------------------------------
    # DOWNLOAD DATA
    # -------------------------------------------------

    X, y, categorical, feature_names = dataset.get_data(
        dataset_format="dataframe",
        target=target
    )
    if X is None or X.empty:
        raise ValueError("Dataset is empty")

    # -------------------------------------------------
    # IDENTIFY FEATURE TYPES
    # -------------------------------------------------

    categorical_cols, numerical_cols = identify_features(
        X,
        categorical
    )

    # -------------------------------------------------
    # ACTUAL DIMENSIONS
    # -------------------------------------------------

    n_rows = len(X)
    n_features = X.shape[1]
    n_categorical = len(categorical_cols)
    n_numerical = len(numerical_cols)
    n_other = (
        n_features - n_categorical - n_numerical
    )
    print("\nDataset information")
    print("-" * 40)
    print(f"Name           : {dataset.name}")
    print(f"Rows           : {n_rows}")
    print(f"Total features : {n_features}")
    print(f"Categorical    : {n_categorical}")
    print(f"Numerical      : {n_numerical}")
    print(f"Other          : {n_other}")

    # -------------------------------------------------
    # VALIDATE ROW COUNT
    # -------------------------------------------------

    if not args.min_rows <= n_rows <= args.max_rows:
        raise ValueError(
            f"Row count mismatch: {n_rows}"
        )

    # -------------------------------------------------
    # VALIDATE TOTAL FEATURES
    # -------------------------------------------------

    if not args.min_features <= n_features <= args.max_features:
        raise ValueError(
            f"Feature count mismatch: {n_features}"
        )

    # -------------------------------------------------
    # VALIDATE CATEGORICAL FEATURES
    # -------------------------------------------------

    if not (
        args.min_categorical
        <= n_categorical
        <= args.max_categorical
    ):
        raise ValueError(
            f"Categorical count mismatch: {n_categorical}"
        )

    # -------------------------------------------------
    # VALIDATE NUMERICAL FEATURES
    # -------------------------------------------------

    if not (
        args.min_numerical
        <= n_numerical
        <= args.max_numerical
    ):
        raise ValueError(
            f"Numerical count mismatch: {n_numerical}"
        )

    # -------------------------------------------------
    # VALIDATE TARGET
    # -------------------------------------------------

    y = validate_target(
        y,
        args.problem,
        number_of_classes
    )

    # -------------------------------------------------
    # METADATA
    # -------------------------------------------------

    # Runtime metadata is still needed for dataset validation and CSV output.
    metadata = {
        "dataset_id": int(dataset_id),
        "name": dataset.name,
        "problem_type": args.problem,
        "target": target,
        "n_rows": n_rows,
        "n_features": n_features,
        "n_categorical": n_categorical,
        "n_numerical": n_numerical,
        "n_other": n_other,
        "categorical_features": categorical_cols,
        "numerical_features": numerical_cols,
        "other_features": [
            col for col in X.columns
            if col not in categorical_cols
            and col not in numerical_cols
        ],
    }
    return X, y, metadata

# =====================================================
# SAVE DATASET
# =====================================================

def save_dataset(X, y, metadata):
    data_path = get_dataset_path(
        metadata["name"],
        metadata["dataset_id"]
    )
    df = X.copy()

    # -------------------------------------------------
    # PRESERVE CATEGORICAL FEATURES
    # -------------------------------------------------

    for col in metadata["categorical_features"]:
        df[col] = df[col].astype("string")

    # -------------------------------------------------
    # ADD TARGET
    # -------------------------------------------------

    if y is not None:
        df[metadata["target"]] = y

    # -------------------------------------------------
    # SAVE CSV
    # -------------------------------------------------

    df.to_csv(
        data_path,
        index=False
    )

    # -------------------------------------------------
    # OPTIONAL METADATA SIDECAR
    # Uncomment this block and the json import when metadata sidecars are needed.
    # -------------------------------------------------

    # metadata_path = data_path.with_name(f"{data_path.stem}_metadata.json")
    #
    # with open(
    #     metadata_path,
    #     "w",
    #     encoding="utf-8"
    # ) as f:
    #
    #     json.dump(
    #         metadata,
    #         f,
    #         indent=4,
    #         ensure_ascii=False,
    #         default=str
    #     )

    print(f"\nSaved successfully: {data_path}")
    return data_path

# =====================================================
# CONFIG VALIDATION
# =====================================================

def validate_config(args):
    if args.problem not in [
        "classification",
        "regression",
        "clustering"
    ]:
        raise ValueError("Invalid problem type")
    if args.limit < 1:
        raise ValueError("Limit must be at least 1")
    if args.min_rows < 1 or args.max_rows < args.min_rows:
        raise ValueError("Invalid row range")
    if args.min_features < 1 or args.max_features < args.min_features:
        raise ValueError("Invalid total feature range")
    if args.min_categorical < 0 or args.max_categorical < args.min_categorical:
        raise ValueError("Invalid categorical feature range")
    if args.min_numerical < 0 or args.max_numerical < args.min_numerical:
        raise ValueError("Invalid numerical feature range")
    if (
        args.min_categorical + args.min_numerical
        > args.max_features
    ):
        raise ValueError(
            "Minimum categorical + numerical features "
            "cannot exceed maximum total features"
        )
    if (
        args.min_categorical + args.min_numerical
        < args.min_features
    ):
        raise ValueError(
            "Minimum categorical + numerical features "
            "must meet minimum total features"
        )

# =====================================================
# FETCH DATASETS
# =====================================================

def fetch_datasets(args):
    validate_config(args)
    candidates = search_datasets(args)
    if candidates.empty:
        print("\nNo matching datasets found.")
        return []
    saved_paths = []
    skipped_count = 0
    failed_count = 0
    checked_count = 0

    # -------------------------------------------------
    # ITERATE THROUGH CANDIDATES
    # -------------------------------------------------

    for _, row in candidates.iterrows():

        # Stop after downloading requested number
        # of NEW datasets.

        if len(saved_paths) >= args.limit:
            break
        dataset_id = int(row["did"])
        checked_count += 1
        print("\n" + "=" * 60)
        print(f"Checking dataset ID: {dataset_id}")

        # -------------------------------------------------
        # SKIP ALREADY DOWNLOADED DATASETS
        # -------------------------------------------------

        if is_dataset_downloaded(dataset_id):
            print(
                f"SKIPPED: Dataset {dataset_id} "
                "has already been downloaded."
            )
            skipped_count += 1
            continue
        try:

            # -------------------------------------------------
            # GET DATASET METADATA
            # -------------------------------------------------

            dataset = openml.datasets.get_dataset(
                dataset_id
            )
            print(f"Dataset: {dataset.name}")

            # -------------------------------------------------
            # DOWNLOAD AND VALIDATE
            # -------------------------------------------------

            number_of_classes = row.get(
                "NumberOfClasses",
                None
            )
            X, y, metadata = download_dataset(
                dataset_id,
                args,
                number_of_classes
            )

            # -------------------------------------------------
            # SAVE
            # -------------------------------------------------

            path = save_dataset(
                X,
                y,
                metadata
            )
            saved_paths.append(path)
        except Exception as e:
            print(
                f"FAILED: Dataset {dataset_id}: {e}"
            )
            failed_count += 1
            continue

    # -------------------------------------------------
    # FINAL SUMMARY
    # -------------------------------------------------

    print("\n" + "=" * 60)
    print("DOWNLOAD SUMMARY")
    print("=" * 60)
    print(f"Requested new datasets : {args.limit}")
    print(f"Candidates checked     : {checked_count}")
    print(f"New datasets downloaded: {len(saved_paths)}")
    print(f"Already downloaded     : {skipped_count}")
    print(f"Failed validation      : {failed_count}")
    if len(saved_paths) < args.limit:
        print(
            "\nCould not find enough new matching datasets."
        )
    return saved_paths

# =====================================================
# MAIN
# =====================================================

if __name__ == "__main__":

    # =================================================
    # USER CONFIGURATION
    # =================================================

    CONFIG = {

        # Problem type
        "problem": "classification",
        # classification / regression / clustering

        # Number of NEW datasets
        "limit": 1,

        # Dataset size
        "min_rows": 5000,
        "max_rows": 50000,

        # Total features
        "min_features": 8,
        "max_features": 20,

        # Categorical features
        "min_categorical": 3,
        "max_categorical": 8,

        # Numerical features
        "min_numerical": 5,
        "max_numerical": 12,

        # Sorting
        "largest_first": True,
    }

    # =================================================
    # CREATE CONFIG OBJECT
    # =================================================

    args = SimpleNamespace(**CONFIG)

    # =================================================
    # EXECUTE
    # =================================================

    paths = fetch_datasets(args)

    # =================================================
    # FINAL OUTPUT
    # =================================================

    print("\n" + "=" * 60)
    print("NEWLY DOWNLOADED DATASETS")
    print("=" * 60)
    if paths:
        for path in paths:
            print(path)
    else:
        print("No new datasets downloaded.")
