import argparse
import json
import sys
from collections import defaultdict
from itertools import combinations
from pathlib import Path
from typing import Any, Dict, List, Tuple

import joblib
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split

# Allow direct execution: python models/fine_tuned/train_local_evaluator.py
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from models.fine_tuned.features import FEATURE_NAMES, meal_items_to_features


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _target_score(meal_items: List[Dict[str, Any]]) -> float:
    if not meal_items:
        return 0.1

    avg_gi = sum(_to_float(item.get("GI"), 50.0) for item in meal_items) / len(meal_items)
    total_carbs = sum(_to_float(item.get("Carbs"), 0.0) for item in meal_items)
    total_fiber = sum(_to_float(item.get("Fiber"), 0.0) for item in meal_items)
    categories = {str(item.get("Food category", "")).strip().lower() for item in meal_items if item.get("Food category")}

    diabetes_score = 10.0
    if avg_gi >= 70:
        diabetes_score -= 4.0
    elif avg_gi >= 55:
        diabetes_score -= 2.0

    if total_carbs >= 110:
        diabetes_score -= 4.0
    elif total_carbs >= 70:
        diabetes_score -= 2.0

    if total_fiber >= 10:
        diabetes_score += 1.0
    diabetes_score = max(1.0, min(10.0, diabetes_score))

    diversity_score = len(categories) * 2.0
    if len(meal_items) >= 3:
        diversity_score += 1.0
    diversity_score = max(1.0, min(10.0, diversity_score))

    # Weighted blend, normalized to 0-1.
    return round(((0.75 * diabetes_score) + (0.25 * diversity_score)) / 10.0, 4)


def _load_rows(path: str) -> List[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _build_training_rows(dataset_rows: List[Dict[str, Any]], max_meals_per_group: int = 80) -> Tuple[List[List[float]], List[float]]:
    grouped: Dict[Tuple[str, str], List[Dict[str, Any]]] = defaultdict(list)
    for row in dataset_rows:
        county = str(row.get("County", "")).strip()
        season = str(row.get("Seasonal availability", "")).strip()
        food = str(row.get("Food", "")).strip().lower()
        if county and season and food:
            grouped[(county, season)].append(row)

    features: List[List[float]] = []
    targets: List[float] = []

    for _, rows in grouped.items():
        dedup: Dict[str, Dict[str, Any]] = {}
        for row in rows:
            food = str(row.get("Food", "")).strip().lower()
            if food and food not in dedup:
                dedup[food] = row

        unique_rows = list(dedup.values())
        if len(unique_rows) < 3:
            continue

        count = 0
        for row_a, row_b, row_c in combinations(unique_rows, 3):
            meal_rows = [row_a, row_b, row_c]
            meal_items = []
            for row in meal_rows:
                meal_items.append(
                    {
                        "gi": _to_float(row.get("GI"), 50.0),
                        "carbs": _to_float(row.get("Carbs"), 0.0),
                        "fiber": _to_float(row.get("Fiber"), 0.0),
                        "protein": _to_float(row.get("Protein"), 0.0),
                        "fat": _to_float(row.get("Fat"), 0.0),
                        "calories_per_100g": _to_float(row.get("Calories per 100g"), 0.0),
                        "category": str(row.get("Food category", "")).strip().lower(),
                        "indigenous_vegetable": str(row.get("Indigenous vegetable", "")).strip().lower(),
                    }
                )

            features.append(meal_items_to_features(meal_items))
            targets.append(_target_score(meal_rows))

            count += 1
            if count >= max_meals_per_group:
                break

    return features, targets


def train_model(dataset_path: str, output_path: str, max_meals_per_group: int = 80) -> Dict[str, float]:
    rows = _load_rows(dataset_path)
    x_data, y_data = _build_training_rows(rows, max_meals_per_group=max_meals_per_group)
    if not x_data:
        raise ValueError("No training rows generated. Check dataset contents.")

    x_train, x_test, y_train, y_test = train_test_split(x_data, y_data, test_size=0.2, random_state=42)

    model = RandomForestRegressor(
        n_estimators=250,
        max_depth=12,
        random_state=42,
        n_jobs=-1,
    )
    model.fit(x_train, y_train)

    y_pred = model.predict(x_test)
    mae = float(mean_absolute_error(y_test, y_pred))
    r2 = float(r2_score(y_test, y_pred))

    artifact = {
        "model": model,
        "feature_names": FEATURE_NAMES,
        "model_version": "local_food_dataset_v1",
        "training_rows": len(x_data),
    }
    joblib.dump(artifact, output_path)

    return {"mae": round(mae, 4), "r2": round(r2, 4), "training_rows": float(len(x_data))}


def main() -> None:
    parser = argparse.ArgumentParser(description="Train local nutrition evaluator model from kenya_food_dataset.json")
    parser.add_argument("--dataset", default="kenya_food_dataset.json", help="Path to food dataset JSON")
    parser.add_argument(
        "--output",
        default="models/fine_tuned/local_evaluator.joblib",
        help="Path to save trained model artifact",
    )
    parser.add_argument("--max-meals-per-group", type=int, default=80, help="Sampling cap per county-season group")
    args = parser.parse_args()

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    metrics = train_model(args.dataset, str(output_path), max_meals_per_group=args.max_meals_per_group)
    print(json.dumps({"model_path": str(output_path), "metrics": metrics}, indent=2))


if __name__ == "__main__":
    main()
