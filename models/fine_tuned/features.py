from typing import Any, Dict, List

FEATURE_NAMES = [
    "avg_gi",
    "total_carbs",
    "total_fiber",
    "total_protein",
    "total_fat",
    "avg_calories",
    "category_diversity",
    "indigenous_ratio",
]


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def meal_items_to_features(meal_items: List[Dict[str, Any]]) -> List[float]:
    if not meal_items:
        return [50.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]

    total_items = float(len(meal_items))
    avg_gi = sum(_to_float(item.get("gi", item.get("GI", 50.0)), 50.0) for item in meal_items) / total_items
    total_carbs = sum(_to_float(item.get("carbs", item.get("Carbs", 0.0)), 0.0) for item in meal_items)
    total_fiber = sum(_to_float(item.get("fiber", item.get("Fiber", 0.0)), 0.0) for item in meal_items)
    total_protein = sum(_to_float(item.get("protein", item.get("Protein", 0.0)), 0.0) for item in meal_items)
    total_fat = sum(_to_float(item.get("fat", item.get("Fat", 0.0)), 0.0) for item in meal_items)
    avg_calories = (
        sum(_to_float(item.get("calories_per_100g", item.get("Calories per 100g", 0.0)), 0.0) for item in meal_items)
        / total_items
    )
    categories = {str(item.get("category", item.get("Food category", ""))).strip().lower() for item in meal_items}
    category_diversity = float(len([value for value in categories if value]))
    indigenous_count = sum(
        1
        for item in meal_items
        if str(item.get("indigenous_vegetable", item.get("Indigenous vegetable", ""))).strip().lower() == "yes"
    )
    indigenous_ratio = indigenous_count / total_items

    return [
        avg_gi,
        total_carbs,
        total_fiber,
        total_protein,
        total_fat,
        avg_calories,
        category_diversity,
        indigenous_ratio,
    ]
