from typing import Any, Dict, List


class DiversityAgent:
    def evaluate(self, context: Dict[str, Any]) -> Dict[str, Any]:
        recommendations = context.get("recommendations", {})
        meal_plan = recommendations.get("meal_plan", {})

        unique_foods = set()
        used_categories = set()
        for section in meal_plan.values():
            for category, foods in section.items():
                if isinstance(foods, list) and foods:
                    used_categories.add(category)
                    for food in foods:
                        unique_foods.add(str(food).lower())

        score = 10.0
        risks: List[str] = []

        if len(unique_foods) < 8:
            score -= 2.0
            risks.append("low_food_diversity")
        if len(used_categories) < 5:
            score -= 1.5
            risks.append("low_category_diversity")

        return {
            "diversity_score": max(1.0, min(10.0, round(score, 2))),
            "risks": risks,
            "unique_food_count": len(unique_foods),
            "category_count": len(used_categories),
        }
