import json
from collections import defaultdict
from itertools import combinations
from pathlib import Path
from typing import Any, Dict, List


def build_training_sample(region: str, season: str, meal: List[str], output: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "input": {
            "region": region,
            "season": season,
            "meal": meal,
        },
        "output": output,
    }


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _evaluate_meal(meal_rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not meal_rows:
        return {
            "diabetes_score": 1,
            "reasoning": "No meal items provided",
            "portion_advice": "use balanced portions",
            "diversity_score": 1,
        }

    avg_gi = sum(_to_float(item.get("GI"), 50.0) for item in meal_rows) / len(meal_rows)
    total_carbs = sum(_to_float(item.get("Carbs"), 0.0) for item in meal_rows)
    total_fiber = sum(_to_float(item.get("Fiber"), 0.0) for item in meal_rows)
    meal_categories = {str(item.get("Food category", "")).lower() for item in meal_rows}

    diabetes_score = 10
    if avg_gi >= 70:
        diabetes_score -= 4
    elif avg_gi >= 55:
        diabetes_score -= 2

    if total_carbs >= 110:
        diabetes_score -= 4
    elif total_carbs >= 70:
        diabetes_score -= 2

    if total_fiber >= 10:
        diabetes_score += 1

    diabetes_score = max(1, min(10, diabetes_score))

    if avg_gi >= 70 and total_carbs >= 70:
        reasoning = "High carbohydrate and glycemic load"
    elif avg_gi >= 55:
        reasoning = "Moderate glycemic load; monitor carb portions"
    elif total_fiber >= 10:
        reasoning = "High fiber meal supports steadier glucose response"
    else:
        reasoning = "Relatively balanced glycemic profile"

    if total_carbs >= 90:
        portion_advice = "reduce starch combination"
    elif total_carbs >= 60:
        portion_advice = "moderate starch portions and pair with vegetables"
    else:
        portion_advice = "maintain current portions"

    diversity_score = len(meal_categories) * 2
    if len(meal_rows) >= 3:
        diversity_score += 1
    diversity_score = max(1, min(10, diversity_score))

    return {
        "diabetes_score": diabetes_score,
        "reasoning": reasoning,
        "portion_advice": portion_advice,
        "diversity_score": diversity_score,
    }


def generate_training_samples(dataset_path: str, max_meals_per_group: int = 40) -> List[Dict[str, Any]]:
    with open(dataset_path, "r", encoding="utf-8") as f:
        rows = json.load(f)

    grouped: Dict[tuple, List[Dict[str, Any]]] = defaultdict(list)
    for row in rows:
        county = str(row.get("County", "")).strip()
        season = str(row.get("Seasonal availability", "")).strip()
        food = str(row.get("Food", "")).strip()
        if not county or not season or not food:
            continue
        grouped[(county, season)].append(row)

    samples: List[Dict[str, Any]] = []
    for (county, season), group_rows in grouped.items():
        # Deduplicate by food name within each county-season bucket.
        by_food: Dict[str, Dict[str, Any]] = {}
        for row in group_rows:
            food = str(row.get("Food", "")).strip().lower()
            if food and food not in by_food:
                by_food[food] = row

        unique_rows = list(by_food.values())
        if len(unique_rows) < 3:
            continue

        group_count = 0
        for row_a, row_b, row_c in combinations(unique_rows, 3):
            meal_rows = [row_a, row_b, row_c]
            meal = [
                str(row_a.get("Food", "")).strip().lower(),
                str(row_b.get("Food", "")).strip().lower(),
                str(row_c.get("Food", "")).strip().lower(),
            ]
            output = _evaluate_meal(meal_rows)
            samples.append(build_training_sample(county, season, meal, output))

            group_count += 1
            if group_count >= max_meals_per_group:
                break

    return samples


def write_training_samples(dataset_path: str, output_path: str, max_meals_per_group: int = 40) -> int:
    samples = generate_training_samples(dataset_path, max_meals_per_group=max_meals_per_group)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(samples, f, indent=2)
    return len(samples)


if __name__ == "__main__":
    project_root = Path(__file__).resolve().parents[1]
    dataset_file = project_root / "kenya_food_dataset.json"
    output_file = project_root / "training_samples.json"
    count = write_training_samples(str(dataset_file), str(output_file))
    print(f"Generated {count} training samples at {output_file}")