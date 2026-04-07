import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import joblib

from models.fine_tuned.features import meal_items_to_features

try:
	from langchain_openai import ChatOpenAI
except Exception:
	ChatOpenAI = None


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
		self.base_url = os.getenv("CUSTOM_EVALUATOR_BASE_URL")
		self.api_key = os.getenv("CUSTOM_EVALUATOR_API_KEY") or os.getenv("OPENAI_API_KEY")
		self._llm = None
		self._local_model_artifact = None

		explicit_local_path = os.getenv("CUSTOM_EVALUATOR_LOCAL_MODEL_PATH")
		if explicit_local_path:
			self.local_model_path = explicit_local_path
		elif self.model_name.startswith("local:"):
			self.local_model_path = self.model_name.split(":", 1)[1]
		elif self.model_name == "local":
			self.local_model_path = str(Path(__file__).resolve().parent / "fine_tuned" / "local_evaluator.joblib")
		else:
			self.local_model_path = None

	def _build_llm(self):
		if ChatOpenAI is None:
			return None
		if not self.api_key:
			return None

		kwargs = {
			"model": self.model_name,
			"temperature": self.temperature,
			"api_key": self.api_key,
		}
		if self.base_url:
			kwargs["base_url"] = self.base_url

		return ChatOpenAI(**kwargs)

	def _get_llm(self):
		if self._llm is None:
			self._llm = self._build_llm()
		return self._llm

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

	@staticmethod
	def _extract_json_object(content: str) -> Dict[str, Any]:
		start_index = content.find("{")
		end_index = content.rfind("}")
		json_content = content[start_index:end_index + 1] if start_index != -1 and end_index != -1 else content
		return json.loads(json_content)

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
		if self.local_model_path:
			if not meal_items:
				raise RuntimeError("Local model evaluation requires meal_items for feature extraction.")
			return self._evaluate_with_local_model(meal_items)

		llm = self._get_llm()
		if llm is None:
			raise RuntimeError(
				"Custom evaluator model is unavailable. Set CUSTOM_EVALUATOR_MODEL and API credentials before running evaluation."
			)

		try:
			prompt = (
				"You are a strict nutrition recommendation evaluator. "
				"Evaluate quality for diabetes/portion-control safety and practical meal diversity. "
				"Respond with strict JSON only in this format: "
				"{\"score\": <0.0-1.0>, \"passes\": <true/false>, \"issues\": [<strings>]}.\n\n"
				f"Patient profile: {json.dumps(profile)}\n"
				f"Recommendations: {json.dumps(recommendations)}"
			)
			response = llm.invoke(prompt)
			content = response.content if isinstance(response.content, str) else json.dumps(response.content)
			parsed = self._extract_json_object(content)

			score = float(parsed.get("score", 0.0))
			issues = parsed.get("issues", [])
			passes = bool(parsed.get("passes", score >= 0.8))

			return {
				"score": max(0.0, min(1.0, round(score, 3))),
				"passes": passes,
				"issues": issues if isinstance(issues, list) else [str(issues)],
				"method": f"custom_model:{self.model_name}",
			}
		except Exception as error:
			raise RuntimeError(f"Custom model evaluation failed: {error}") from error

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
		if not use_model:
			return self._fallback_architecture_change_breakdown()

		llm = self._get_llm()
		if llm is None:
			return self._fallback_architecture_change_breakdown()

		prompt = (
			"Write a concise technical summary of system evolution using these exact sections: "
			"1) Architecture Evolution, 2) Introduction of Multi-Agent System, 3) Decision Engine, "
			"4) Data Pipeline Contribution, 5) Transition to a Trainable Model, "
			"6) Explainability & Transparency. "
			"Include a short Before vs After markdown table with columns Aspect, Before, After. "
			"Keep emphasis on separation of concerns, explicit domain rules, and Kenyan diabetic meal planning context."
		)

		try:
			response = llm.invoke(prompt)
			if isinstance(response.content, str):
				return response.content
			return json.dumps(response.content)
		except Exception:
			return self._fallback_architecture_change_breakdown()
