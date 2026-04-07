from decision_engine.scorer import diabetes_score

class DiabetesAgent:
    def evaluate(self, meal):
        score = diabetes_score(meal)

        risks = []
        high_gi_foods = []
        for food in meal:
            if food["gi"] > 70:
                risks.append(f"{food['food']} is high GI")
                high_gi_foods.append(food["food"])

        if high_gi_foods:
            risks.append(f"high_gi_meal_plan: {', '.join(sorted(set(high_gi_foods)))}")

        return {
            "diabetes_score": score,
            "risks": risks
        }