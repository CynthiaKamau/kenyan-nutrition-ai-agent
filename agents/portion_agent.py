from typing import Any, Dict, List

from decision_engine.rules import portion_prefix_score


class PortionAgent:
    def evaluate(self, context: Dict[str, Any]) -> Dict[str, Any]:
        profile = context.get("profile", {})
        recommendations = context.get("recommendations", {})
        restrictions = profile.get("dietary_restrictions", {})
        portion_guidelines = recommendations.get("portion_guidelines", {})

        score = 10.0
        risks: List[str] = []

        if restrictions.get("portion_control", False):
            prefix_score = portion_prefix_score(portion_guidelines)
            score -= (1.0 - prefix_score) * 4.0
            if prefix_score < 1.0:
                risks.append("portion_control_not_reflected")

        # Basic density guardrail: unusually large number of selected foods can imply oversized meals.
        meal_plan = recommendations.get("meal_plan", {})
        selected_foods = 0
        for section in meal_plan.values():
            for foods in section.values():
                if isinstance(foods, list):
                    selected_foods += len(foods)
        if selected_foods > 14:
            score -= 1.0
            risks.append("high_meal_density")

        return {
            "portion_score": max(1.0, min(10.0, round(score, 2))),
            "risks": risks,
        }
