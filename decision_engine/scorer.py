from decision_engine.constraints import HIGH_CARB_RISK, HIGH_FIBER_BONUS, HIGH_GI_RISK


def diabetes_score(food_items):
    score = 10

    for food in food_items:
        if food["gi"] > HIGH_GI_RISK:
            score -= 2
        if food["carbs"] > HIGH_CARB_RISK:
            score -= 2
        if food["fiber"] > HIGH_FIBER_BONUS:
            score += 1

    return max(1, min(score, 10))