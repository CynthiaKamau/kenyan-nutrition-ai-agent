import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import joblib

from models.fine_tuned.features import meal_items_to_features


class CustomModelInference:
	"""Inference wrapper for custom evaluator and architecture explanation tasks."""

	def __init__(
		self,
		model_name: Optional[str] = None,
		temperature: float = 0.0,
	):
		self.logger = logging.getLogger(__name__)
		self.model_name = model_name or os.getenv("CUSTOM_EVALUATOR_MODEL", "local")
		self.temperature = temperature
		self._local_model_artifact = None

		explicit_local_path = os.getenv("CUSTOM_EVALUATOR_LOCAL_MODEL_PATH")
		if explicit_local_path:
			self.local_model_path = explicit_local_path
		elif self.model_name.startswith("local:"):
			self.local_model_path = self.model_name.split(":", 1)[1]
		elif self.model_name == "local":
			self.local_model_path = str(Path(__file__).resolve().parent / "fine_tuned" / "local_evaluator.joblib")
		else:
			# Treat any non-local label as a local artifact path for fully offline usage.
			self.local_model_path = self.model_name

	def _get_local_model_artifact(self) -> Dict[str, Any]:
		if not self.local_model_path:
			raise RuntimeError("Local model path is not configured.")
		if self._local_model_artifact is None:
			model_path = Path(self.local_model_path)
			if not model_path.exists():
				raise RuntimeError(
					f"Local evaluator model not found at {model_path}. Train it first with models/fine_tuned/train_local_evaluator.py"
				)
			self._local_model_artifact = joblib.load(model_path)
		return self._local_model_artifact

	def _evaluate_with_local_model(self, meal_items: List[Dict[str, Any]]) -> Dict[str, Any]:
		artifact = self._get_local_model_artifact()
		model = artifact.get("model")
		features = meal_items_to_features(meal_items)
		score = float(model.predict([features])[0])
		bounded = max(0.0, min(1.0, round(score, 3)))

		issues: List[str] = []
		if bounded < 0.6:
			issues.append("high_glucose_risk_pattern")
		elif bounded < 0.8:
			issues.append("moderate_glucose_risk_pattern")

		return {
			"score": bounded,
			"passes": bounded >= 0.8,
			"issues": issues,
			"method": f"local_model:{artifact.get('model_version', 'unknown')}",
		}

	def evaluate_recommendations(
		self,
		profile: Dict[str, Any],
		recommendations: Dict[str, Any],
		meal_items: Optional[List[Dict[str, Any]]] = None,
	) -> Dict[str, Any]:
		if not meal_items:
			raise RuntimeError("Local model evaluation requires meal_items for feature extraction.")
		return self._evaluate_with_local_model(meal_items)

	@staticmethod
	def _fallback_architecture_change_breakdown() -> str:
		return """## Break Down the Changes

### 1. Architecture Evolution
The architecture evolved from a monolithic LLM-first setup to a layered design with a Data Layer, Agent Layer, Decision Engine, Application Layer, and Monitoring Layer. This improves separation of concerns, makes components independently testable, and aligns the implementation with robust AI system design principles.

### 2. Introduction of Multi-Agent System
The updated framework introduces a specialized multi-agent workflow where each agent evaluates a focused quality dimension of meal planning.

- Diabetes Safety Agent
- Portion Control Agent
- Diversity Agent
- Cultural/Seasonal Agent
- Aggregator

This is the central innovation because it decomposes complex nutrition reasoning into modular, auditable responsibilities.

### 3. Decision Engine (Very Important)
A formal decision engine now applies rule-based scoring functions and constraint logic grounded in nutritional guidelines. Core constraints include glycemic index thresholds, macronutrient composition limits, and dietary balance principles. This demonstrates that the system encodes domain knowledge explicitly rather than relying only on opaque model behavior.

### 4. Data Pipeline Contribution
A dedicated data pipeline transforms structured nutrition datasets into machine-readable features and supervised training samples. This creates labeled artifacts for both model training and systematic evaluation, improving reproducibility.

### 5. Transition to a Trainable Model
The system now supports fine-tuning domain-specific models on generated datasets, replacing a purely prompt-driven workflow. This enables consistent learning of diabetic meal-evaluation patterns tailored to the Kenyan context.

### 6. Explainability and Transparency
The redesigned stack produces structured outputs with explicit scores, risk factors, and recommendation rationales. This makes decisions interpretable for both users and healthcare practitioners.

### Before vs After
| Aspect | Before | After |
|---|---|---|
| Model | GPT-based | Multi-agent + fine-tunable |
| Reasoning | Implicit | Explicit + structured |
| Evaluation | None | Rule-based + learned |
| Data usage | Static | Pipeline-driven |
| Explainability | Low | High |
| Research contribution | Limited | Strong |
"""

	def generate_architecture_change_breakdown(self, use_model: bool = True) -> str:
		# Kept for backwards compatibility; architecture summary is now fully local/static.
		return self._fallback_architecture_change_breakdown()
