import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List, Tuple


def _to_float(value: Any, default: float = 0.0) -> float:
	try:
		return float(value)
	except (TypeError, ValueError):
		return default


def _canonical_input(sample_input: Dict[str, Any]) -> str:
	normalized = {
		"region": str(sample_input.get("region", "")).strip(),
		"season": str(sample_input.get("season", "")).strip(),
		"meal": sorted([str(item).strip().lower() for item in sample_input.get("meal", [])]),
	}
	return json.dumps(normalized, sort_keys=True)


def _build_food_index(dataset_rows: List[Dict[str, Any]]) -> Dict[Tuple[str, str, str], Dict[str, Any]]:
	index: Dict[Tuple[str, str, str], Dict[str, Any]] = {}
	for row in dataset_rows:
		county = str(row.get("County", "")).strip()
		season = str(row.get("Seasonal availability", "")).strip()
		food = str(row.get("Food", "")).strip().lower()
		if county and season and food:
			index[(county, season, food)] = row
	return index


def _rule_output_for_sample(
	sample_input: Dict[str, Any],
	food_index: Dict[Tuple[str, str, str], Dict[str, Any]],
) -> Dict[str, Any]:
	region = str(sample_input.get("region", "")).strip()
	season = str(sample_input.get("season", "")).strip()
	meal = [str(item).strip().lower() for item in sample_input.get("meal", [])]

	meal_rows: List[Dict[str, Any]] = []
	for food in meal:
		row = food_index.get((region, season, food))
		if row is not None:
			meal_rows.append(row)

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


def consistency_metric(samples: List[Dict[str, Any]]) -> Dict[str, Any]:
	grouped_outputs: Dict[str, List[str]] = defaultdict(list)

	for sample in samples:
		sample_input = sample.get("input", {})
		output = sample.get("output", {})
		grouped_outputs[_canonical_input(sample_input)].append(json.dumps(output, sort_keys=True))

	total_groups = len(grouped_outputs)
	consistent_groups = 0
	inconsistent_examples: List[Dict[str, Any]] = []

	for canonical_input, output_strings in grouped_outputs.items():
		unique_outputs = sorted(set(output_strings))
		if len(unique_outputs) == 1:
			consistent_groups += 1
		else:
			inconsistent_examples.append(
				{
					"input": json.loads(canonical_input),
					"unique_output_count": len(unique_outputs),
					"outputs_preview": [json.loads(value) for value in unique_outputs[:2]],
				}
			)

	ratio = (consistent_groups / total_groups) if total_groups else 0.0
	return {
		"total_unique_inputs": total_groups,
		"consistent_input_groups": consistent_groups,
		"consistency_ratio": round(ratio, 4),
		"inconsistent_examples": inconsistent_examples[:10],
	}


def agreement_with_rules_metric(
	samples: List[Dict[str, Any]],
	dataset_rows: List[Dict[str, Any]],
) -> Dict[str, Any]:
	food_index = _build_food_index(dataset_rows)

	total = len(samples)
	exact_match_count = 0
	diabetes_match = 0
	reasoning_match = 0
	portion_match = 0
	diversity_match = 0
	mismatches: List[Dict[str, Any]] = []

	for sample in samples:
		sample_input = sample.get("input", {})
		expected = _rule_output_for_sample(sample_input, food_index)
		actual = sample.get("output", {})

		d_match = actual.get("diabetes_score") == expected.get("diabetes_score")
		r_match = actual.get("reasoning") == expected.get("reasoning")
		p_match = actual.get("portion_advice") == expected.get("portion_advice")
		v_match = actual.get("diversity_score") == expected.get("diversity_score")

		diabetes_match += int(d_match)
		reasoning_match += int(r_match)
		portion_match += int(p_match)
		diversity_match += int(v_match)

		if d_match and r_match and p_match and v_match:
			exact_match_count += 1
		elif len(mismatches) < 15:
			mismatches.append(
				{
					"input": sample_input,
					"actual": actual,
					"expected": expected,
				}
			)

	if total == 0:
		return {
			"sample_count": 0,
			"exact_match_rate": 0.0,
			"field_accuracy": {
				"diabetes_score": 0.0,
				"reasoning": 0.0,
				"portion_advice": 0.0,
				"diversity_score": 0.0,
			},
			"mismatches_preview": [],
		}

	return {
		"sample_count": total,
		"exact_match_rate": round(exact_match_count / total, 4),
		"field_accuracy": {
			"diabetes_score": round(diabetes_match / total, 4),
			"reasoning": round(reasoning_match / total, 4),
			"portion_advice": round(portion_match / total, 4),
			"diversity_score": round(diversity_match / total, 4),
		},
		"mismatches_preview": mismatches,
	}


def diversity_score_distribution_metric(samples: List[Dict[str, Any]]) -> Dict[str, Any]:
	distribution_counter: Counter = Counter()

	for sample in samples:
		score = sample.get("output", {}).get("diversity_score")
		if isinstance(score, (int, float)):
			distribution_counter[int(score)] += 1

	total = sum(distribution_counter.values())
	distribution = {
		str(score): {
			"count": count,
			"ratio": round((count / total), 4) if total else 0.0,
		}
		for score, count in sorted(distribution_counter.items())
	}

	return {
		"sample_count": total,
		"distribution": distribution,
	}


def evaluate_training_samples(samples_path: str, dataset_path: str) -> Dict[str, Any]:
	with open(samples_path, "r", encoding="utf-8") as f:
		samples = json.load(f)

	with open(dataset_path, "r", encoding="utf-8") as f:
		dataset_rows = json.load(f)

	return {
		"consistency": consistency_metric(samples),
		"agreement_with_rules": agreement_with_rules_metric(samples, dataset_rows),
		"diversity_score_distribution": diversity_score_distribution_metric(samples),
	}


if __name__ == "__main__":
	root = Path(__file__).resolve().parents[1]
	samples_file = root / "training_samples.json"
	dataset_file = root / "kenya_food_dataset.json"

	metrics = evaluate_training_samples(str(samples_file), str(dataset_file))
	print(json.dumps(metrics, indent=2))
