import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

import joblib
from sklearn.inspection import permutation_importance
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import GroupShuffleSplit, train_test_split

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from models.fine_tuned.features import FEATURE_NAMES
from models.fine_tuned.train_local_evaluator import _build_training_rows_with_groups, _load_rows


def _score_bins(values: List[float]) -> Dict[str, int]:
    bins = {
        "0.0-0.2": 0,
        "0.2-0.4": 0,
        "0.4-0.6": 0,
        "0.6-0.8": 0,
        "0.8-1.0": 0,
    }
    for value in values:
        if value < 0.2:
            bins["0.0-0.2"] += 1
        elif value < 0.4:
            bins["0.2-0.4"] += 1
        elif value < 0.6:
            bins["0.4-0.6"] += 1
        elif value < 0.8:
            bins["0.6-0.8"] += 1
        else:
            bins["0.8-1.0"] += 1
    return bins


def _worst_predictions(
    x_test: List[List[float]],
    y_true: List[float],
    y_pred: List[float],
    top_k: int,
) -> List[Dict[str, Any]]:
    indexed_errors: List[Tuple[int, float]] = []
    for idx, (actual, predicted) in enumerate(zip(y_true, y_pred)):
        indexed_errors.append((idx, abs(actual - predicted)))
    indexed_errors.sort(key=lambda pair: pair[1], reverse=True)

    examples: List[Dict[str, Any]] = []
    for idx, abs_error in indexed_errors[: max(1, top_k)]:
        feature_row = x_test[idx]
        examples.append(
            {
                "index": idx,
                "actual": round(float(y_true[idx]), 4),
                "predicted": round(float(y_pred[idx]), 4),
                "abs_error": round(float(abs_error), 4),
                "features": {name: round(float(value), 4) for name, value in zip(FEATURE_NAMES, feature_row)},
            }
        )
    return examples


def _feature_importance_report(
    model: Any,
    x_test: List[List[float]],
    y_test: List[float],
    random_state: int,
    top_k: int,
) -> Dict[str, Any]:
    if len(x_test) < 5:
        return {
            "enabled": False,
            "reason": "Need at least 5 rows for stable permutation importance",
        }

    result = permutation_importance(
        model,
        x_test,
        y_test,
        scoring="neg_mean_absolute_error",
        n_repeats=10,
        random_state=random_state,
        n_jobs=-1,
    )
    entries = []
    for feature_name, mean_value, std_value in zip(FEATURE_NAMES, result.importances_mean, result.importances_std):
        entries.append(
            {
                "feature": feature_name,
                "importance_mean": round(float(mean_value), 6),
                "importance_std": round(float(std_value), 6),
                "abs_importance_mean": round(abs(float(mean_value)), 6),
            }
        )

    entries.sort(key=lambda item: item["abs_importance_mean"], reverse=True)
    return {
        "enabled": True,
        "top_features": entries[: max(1, top_k)],
    }


def generate_report(
    dataset_path: str,
    model_path: str,
    max_meals_per_group: int,
    random_state: int,
    top_k: int,
    split_strategy: str,
    importance_top_k: int,
) -> Dict[str, Any]:
    rows = _load_rows(dataset_path)
    x_data, y_data, group_labels = _build_training_rows_with_groups(rows, max_meals_per_group=max_meals_per_group)
    if not x_data:
        raise ValueError("No test rows generated from dataset.")

    split_summary: Dict[str, Any] = {"strategy": split_strategy}
    if split_strategy == "group":
        splitter = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=random_state)
        _, test_idx = next(splitter.split(x_data, y_data, groups=group_labels))
        x_test = [x_data[idx] for idx in test_idx]
        y_test = [y_data[idx] for idx in test_idx]
        test_groups = sorted({group_labels[idx] for idx in test_idx})
        split_summary["test_group_count"] = len(test_groups)
        split_summary["test_groups_preview"] = test_groups[:10]
    else:
        _, x_test, _, y_test = train_test_split(
            x_data,
            y_data,
            test_size=0.2,
            random_state=random_state,
        )

    artifact = joblib.load(model_path)
    model = artifact.get("model")
    if model is None:
        raise ValueError("Model artifact is missing the 'model' object.")

    y_pred_raw = model.predict(x_test)
    y_pred = [max(0.0, min(1.0, float(value))) for value in y_pred_raw]

    mae = float(mean_absolute_error(y_test, y_pred))
    rmse = float(math.sqrt(mean_squared_error(y_test, y_pred)))
    r2 = float(r2_score(y_test, y_pred))

    report: Dict[str, Any] = {
        "model_path": model_path,
        "model_version": artifact.get("model_version", "unknown"),
        "dataset_path": dataset_path,
        "evaluation_rows": len(x_test),
        "metrics": {
            "mae": round(mae, 4),
            "rmse": round(rmse, 4),
            "r2": round(r2, 4),
        },
        "split": split_summary,
        "score_distribution": {
            "actual": _score_bins([float(v) for v in y_test]),
            "predicted": _score_bins(y_pred),
        },
        "feature_importance": _feature_importance_report(
            model=model,
            x_test=x_test,
            y_test=y_test,
            random_state=random_state,
            top_k=importance_top_k,
        ),
        "worst_predictions": _worst_predictions(x_test=x_test, y_true=y_test, y_pred=y_pred, top_k=top_k),
        "model_training_metrics": artifact.get("training_metrics", {}),
        "model_training_config": artifact.get("training_config", {}),
    }
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate local nutrition model and print detailed test report")
    parser.add_argument("--dataset", default="kenya_food_dataset.json", help="Path to source dataset JSON")
    parser.add_argument(
        "--model-path",
        default="models/fine_tuned/local_evaluator.joblib",
        help="Path to trained local model artifact",
    )
    parser.add_argument("--max-meals-per-group", type=int, default=200, help="Sampling cap per county-season group")
    parser.add_argument("--random-state", type=int, default=42, help="Random seed for reproducible split")
    parser.add_argument("--top-k", type=int, default=10, help="Number of worst errors to display")
    parser.add_argument(
        "--split-strategy",
        choices=["random", "group"],
        default="group",
        help="Evaluation split type; group keeps county-season groups separated",
    )
    parser.add_argument(
        "--importance-top-k",
        type=int,
        default=8,
        help="Number of top permutation-importance features to display",
    )
    args = parser.parse_args()

    report = generate_report(
        dataset_path=args.dataset,
        model_path=args.model_path,
        max_meals_per_group=args.max_meals_per_group,
        random_state=args.random_state,
        top_k=args.top_k,
        split_strategy=args.split_strategy,
        importance_top_k=args.importance_top_k,
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
