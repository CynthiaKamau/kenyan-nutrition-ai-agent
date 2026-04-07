from typing import Any, Dict, List


def flatten_meal_foods(meal_plan: Dict[str, Dict[str, List[str]]]) -> List[str]:
	foods: List[str] = []
	for section in meal_plan.values():
		for values in section.values():
			if isinstance(values, list):
				foods.extend(values)
	return foods


def portion_prefix_score(portion_guidelines: Dict[str, Any]) -> float:
	if not portion_guidelines:
		return 0.0

	valid = 0
	total = 0
	for value in portion_guidelines.values():
		total += 1
		if str(value).lower().startswith(("small", "moderate")):
			valid += 1

	if total == 0:
		return 0.0
	return valid / total
