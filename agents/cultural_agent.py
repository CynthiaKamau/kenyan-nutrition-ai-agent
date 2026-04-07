from typing import Any, Dict, List


class CulturalAgent:
    _religious_restrictions = {
        "islam": {"pork", "ham", "bacon"},
        "hinduism": {"beef"},
    }

    def evaluate(self, context: Dict[str, Any]) -> Dict[str, Any]:
        profile = context.get("profile", {})
        meal_items = context.get("meal_items", [])

        religion = str(profile.get("religion") or "").lower().strip()
        restricted_foods = self._religious_restrictions.get(religion, set())

        score = 10.0
        risks: List[str] = []
        suggestions: List[str] = []

        selected_foods = {str(item.get("food", "")).lower() for item in meal_items}
        blocked = sorted(food for food in selected_foods if food in restricted_foods)
        if blocked:
            score -= 4.0
            risks.append(f"religious_restriction_conflict: {', '.join(blocked)}")

        indigenous_count = sum(1 for item in meal_items if str(item.get("indigenous_vegetable", "")).lower() == "yes")
        if meal_items and indigenous_count == 0:
            score -= 1.0
            suggestions.append("consider_indigenous_vegetables")

        local_source_count = sum(1 for item in meal_items if str(item.get("source_type", "")).lower() in {"local", "indigenous"})
        if meal_items and local_source_count / max(1, len(meal_items)) < 0.3:
            score -= 0.75
            suggestions.append("increase_local_seasonal_foods")

        return {
            "cultural_score": max(1.0, min(10.0, round(score, 2))),
            "risks": risks,
            "suggestions": suggestions,
        }
