class Aggregator:
    def combine(self, results):
        weights = {
            "diabetes": 0.4,
            "portion": 0.25,
            "diversity": 0.2,
            "cultural": 0.15,
        }

        weighted_sum = (
            weights["diabetes"] * results["diabetes"]["diabetes_score"]
            + weights["portion"] * results["portion"]["portion_score"]
            + weights["diversity"] * results["diversity"]["diversity_score"]
            + weights["cultural"] * results["cultural"]["cultural_score"]
        )

        return {
            "final_score": round(weighted_sum, 3),
            "weights": weights,
            "details": results
        }