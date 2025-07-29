from typing import Dict, List, Any, Tuple
import logging
import json
from google.cloud import aiplatform
from vertexai.generative_models import GenerativeModel
from config import config
from utils.feedback import FeedbackCollector
from ..patient_profiles.agent import PatientProfileAgent
from ..regions_for_food.agent import RegionalFoodAgent

class FoodRecommendationAgent:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.agent_config = config.food_recommendation_agent_config
        self.feedback_collector = FeedbackCollector()
        
        # Initialize Vertex AI
        aiplatform.init(project=config.project_id, location=config.location)
        self.model = GenerativeModel(config.model_name)
        
        # Keep fallback agents for data retrieval
        self.patient_agent = PatientProfileAgent()
        self.regional_agent = RegionalFoodAgent()
        
        self.logger.info(f"Food Recommendation Agent initialized with model: {config.model_name}")
    
    def generate_recommendations(self, patient_profile: Dict[str, Any], session_id: str = None) -> Dict[str, Any]:
        """Generate personalized food recommendations using ADK"""
        
        regional_foods = self.regional_agent.get_regional_foods(patient_profile["location"])
        
        prompt = f"""
        {self.agent_config['instructions']}
        
        Patient Profile:
        {json.dumps(patient_profile, indent=2)}
        
        Regional Foods Available:
        {json.dumps(regional_foods, indent=2)}
        
        Create comprehensive nutrition recommendations including:
        1. Daily meal plan (breakfast, lunch, dinner, snacks)
        2. Preferred foods for health conditions
        3. Foods to limit or avoid
        4. Portion guidelines
        5. Meal timing advice
        
        Consider the patient's health conditions, cultural preferences, and local food availability.
        
        Return a JSON object with this structure:
        {{
            "meal_plan": {{
                "breakfast": {{"grains": [], "proteins": [], "vegetables": [], "fruits": []}},
                "lunch": {{"grains": [], "proteins": [], "vegetables": [], "legumes": []}},
                "dinner": {{"grains": [], "proteins": [], "vegetables": []}},
                "snacks": {{"fruits": [], "nuts": []}}
            }},
            "preferred_foods": {{
                "high_fiber": [],
                "low_sodium": [],
                "lean_proteins": [],
                "complex_carbs": []
            }},
            "foods_to_limit": {{
                "high_gi_foods": [],
                "high_sodium_foods": [],
                "high_fat_foods": []
            }},
            "portion_guidelines": {{
                "grains": "portion description",
                "vegetables": "portion description",
                "fruits": "portion description",
                "proteins": "portion description",
                "legumes": "portion description"
            }},
            "meal_timing": {{
                "frequency": "meal frequency advice",
                "timing": "timing recommendations",
                "breakfast": "breakfast timing",
                "dinner": "dinner timing"
            }},
            "cultural_adaptations": "how recommendations fit Kenyan food culture",
            "health_rationale": "explanation of recommendations based on health conditions"
        }}
        """
        
        try:
            response = self.model.generate_content(prompt)
            
            response_text = response.text.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:-3]
            elif response_text.startswith("```"):
                response_text = response_text[3:-3]
            
            ai_recommendations = json.loads(response_text)
            
            # Validate and enhance recommendations
            enhanced_recommendations = self._validate_recommendations(ai_recommendations, patient_profile, regional_foods)
            
            # Collect feedback if session_id provided
            if session_id:
                self.feedback_collector.collect_user_feedback(
                    self.agent_config['name'],
                    session_id,
                    {"patient_profile": patient_profile},
                    enhanced_recommendations
                )
            
            return enhanced_recommendations
            
        except Exception as e:
            self.logger.error(f"Error generating recommendations: {e}")
            # Fallback to rule-based recommendations
            return self._generate_fallback_recommendations(patient_profile, regional_foods)
    
    def _validate_recommendations(self, recommendations: Dict[str, Any], 
                                 patient_profile: Dict[str, Any], 
                                 regional_foods: Dict[str, List[str]]) -> Dict[str, Any]:
        """Validate and enhance AI recommendations"""
        
        # Ensure all required sections exist
        required_sections = ["meal_plan", "preferred_foods", "foods_to_limit", "portion_guidelines", "meal_timing"]
        for section in required_sections:
            if section not in recommendations:
                recommendations[section] = self._get_fallback_section(section, patient_profile, regional_foods)
        
        # Validate meal plan has proper structure
        meal_plan = recommendations.get("meal_plan", {})
        required_meals = ["breakfast", "lunch", "dinner", "snacks"]
        for meal in required_meals:
            if meal not in meal_plan:
                meal_plan[meal] = self._get_fallback_meal(meal, regional_foods, patient_profile)
        
        # Ensure foods are actually available in the region
        recommendations["meal_plan"] = self._filter_meal_plan_by_availability(meal_plan, regional_foods)
        
        return recommendations
    
    def _generate_fallback_recommendations(self, patient_profile: Dict[str, Any], 
                                         regional_foods: Dict[str, List[str]]) -> Dict[str, Any]:
        """Generate recommendations using rule-based fallback"""
        self.logger.info("Using fallback rule-based recommendations")
        
        dietary_restrictions = patient_profile["dietary_restrictions"]
        health_category = patient_profile["health_category"]
        diabetes_status = patient_profile["diabetes_status"]
        
        recommendations = {
            "meal_plan": self._create_meal_plan(regional_foods, dietary_restrictions, patient_profile),
            "preferred_foods": self._get_preferred_foods(regional_foods, dietary_restrictions),
            "foods_to_limit": self._get_foods_to_limit(regional_foods, dietary_restrictions),
            "portion_guidelines": self._get_portion_guidelines(patient_profile),
            "meal_timing": self._get_meal_timing_advice(diabetes_status),
            "cultural_adaptations": "Recommendations adapted for traditional Kenyan dietary patterns",
            "health_rationale": f"Recommendations tailored for {health_category} health status with {diabetes_status} diabetes condition"
        }
        
        return recommendations
    
    def _create_meal_plan(self, regional_foods: Dict[str, List[str]], 
                         restrictions: Dict[str, bool], 
                         profile: Dict[str, Any]) -> Dict[str, Dict[str, List[str]]]:
        """Create a balanced meal plan for the day"""
        
        meal_plan = {
            "breakfast": {"grains": [], "proteins": [], "vegetables": [], "fruits": []},
            "lunch": {"grains": [], "proteins": [], "vegetables": [], "legumes": []},
            "dinner": {"grains": [], "proteins": [], "vegetables": []},
            "snacks": {"fruits": [], "nuts": []}
        }
        
        # Breakfast recommendations
        breakfast_grains = self._filter_by_gi(regional_foods["grains"], restrictions["limit_sugar"])
        meal_plan["breakfast"]["grains"] = breakfast_grains[:2]
        meal_plan["breakfast"]["proteins"] = [food for food in regional_foods["proteins"] if food in ["eggs", "milk"]][:1]
        meal_plan["breakfast"]["fruits"] = self._filter_by_gi(regional_foods["fruits"], restrictions["limit_sugar"])[:2]
        
        # Lunch recommendations
        meal_plan["lunch"]["grains"] = regional_foods["grains"][:1]
        meal_plan["lunch"]["proteins"] = regional_foods["proteins"][:1]
        meal_plan["lunch"]["vegetables"] = regional_foods["vegetables"][:3]
        meal_plan["lunch"]["legumes"] = regional_foods["legumes"][:1]
        
        # Dinner recommendations
        meal_plan["dinner"]["grains"] = regional_foods["grains"][:1]
        meal_plan["dinner"]["proteins"] = regional_foods["proteins"][:1]
        meal_plan["dinner"]["vegetables"] = regional_foods["vegetables"][:2]
        
        # Snack recommendations
        meal_plan["snacks"]["fruits"] = self._filter_by_gi(regional_foods["fruits"], restrictions["limit_sugar"])[:2]
        meal_plan["snacks"]["nuts"] = [food for food in regional_foods["legumes"] if "nuts" in food or "groundnuts" in food][:1]
        
        return meal_plan
    
    def _filter_by_gi(self, foods: List[str], limit_sugar: bool) -> List[str]:
        """Filter foods by glycemic index if sugar limitation is needed"""
        if not limit_sugar:
            return foods
        
        low_gi_foods = []
        for food in foods:
            nutrition = self.regional_agent.get_nutritional_info(food)
            if nutrition.get("gi", 50) < 55:  # Low GI foods
                low_gi_foods.append(food)
        
        return low_gi_foods if low_gi_foods else foods[:2]  # Fallback to first 2 if no low GI found
    
    def _get_preferred_foods(self, regional_foods: Dict[str, List[str]], 
                           restrictions: Dict[str, bool]) -> Dict[str, List[str]]:
        """Get foods that are particularly beneficial for the patient"""
        preferred = {
            "high_fiber": [],
            "low_sodium": [],
            "lean_proteins": [],
            "complex_carbs": []
        }
        
        # High fiber foods (good for diabetes and weight management)
        if restrictions["increase_fiber"]:
            high_fiber_foods = ["kale", "spinach", "beans", "sweet_potatoes", "avocados"]
            preferred["high_fiber"] = [food for food in high_fiber_foods 
                                     if any(food in category for category in regional_foods.values())]
        
        # Lean proteins
        lean_proteins = ["fish", "chicken", "eggs"]
        preferred["lean_proteins"] = [food for food in lean_proteins if food in regional_foods.get("proteins", [])]
        
        # Complex carbs
        complex_carbs = ["millet", "sorghum", "sweet_potatoes"]
        preferred["complex_carbs"] = [food for food in complex_carbs 
                                    if any(food in category for category in regional_foods.values())]
        
        return preferred
    
    def _get_foods_to_limit(self, regional_foods: Dict[str, List[str]], 
                          restrictions: Dict[str, bool]) -> Dict[str, List[str]]:
        """Get foods that should be limited based on health conditions"""
        limit = {
            "high_gi_foods": [],
            "high_sodium_foods": [],
            "high_fat_foods": []
        }
        
        if restrictions["limit_sugar"]:
            high_gi_foods = ["rice", "watermelon", "dates"]
            limit["high_gi_foods"] = [food for food in high_gi_foods 
                                    if any(food in category for category in regional_foods.values())]
        
        if restrictions["limit_saturated_fat"]:
            high_fat_foods = ["coconut_milk", "groundnuts"]
            limit["high_fat_foods"] = [food for food in high_fat_foods 
                                     if any(food in category for category in regional_foods.values())]
        
        return limit
    
    def _get_portion_guidelines(self, profile: Dict[str, Any]) -> Dict[str, str]:
        """Get portion size guidelines based on patient profile"""
        guidelines = {
            "grains": "1/2 cup cooked",
            "vegetables": "1 cup raw or 1/2 cup cooked",
            "fruits": "1 medium fruit or 1/2 cup",
            "proteins": "palm-sized portion (3-4 oz)",
            "legumes": "1/2 cup cooked"
        }
        
        if profile["health_category"] == "high_risk":
            guidelines = {k: f"Small {v}" for k, v in guidelines.items()}
        elif profile["bmi"] >= 30:
            guidelines = {k: f"Moderate {v}" for k, v in guidelines.items()}
        
        return guidelines
    
    def _get_meal_timing_advice(self, diabetes_status: str) -> Dict[str, str]:
        """Get meal timing advice based on diabetes status"""
        if diabetes_status in ["type1", "type2"]:
            return {
                "frequency": "Eat 3 main meals and 2-3 small snacks",
                "timing": "Eat every 3-4 hours to maintain stable blood sugar",
                "breakfast": "Within 1 hour of waking up",
                "dinner": "At least 2-3 hours before bedtime"
            }
        else:
            return {
                "frequency": "3 main meals with optional healthy snacks",
                "timing": "Regular meal times help maintain energy levels",
                "breakfast": "Start your day with a balanced meal",
                "dinner": "Light dinner 2-3 hours before bedtime"
            }
    
    def _get_fallback_section(self, section: str, patient_profile: Dict[str, Any], 
                             regional_foods: Dict[str, List[str]]) -> Dict[str, Any]:
        """Get fallback data for missing sections"""
        if section == "meal_plan":
            return self._create_meal_plan(regional_foods, patient_profile["dietary_restrictions"], patient_profile)
        elif section == "preferred_foods":
            return self._get_preferred_foods(regional_foods, patient_profile["dietary_restrictions"])
        elif section == "foods_to_limit":
            return self._get_foods_to_limit(regional_foods, patient_profile["dietary_restrictions"])
        elif section == "portion_guidelines":
            return self._get_portion_guidelines(patient_profile)
        elif section == "meal_timing":
            return self._get_meal_timing_advice(patient_profile["diabetes_status"])
        else:
            return {}
    
    def _filter_meal_plan_by_availability(self, meal_plan: Dict[str, Any], 
                                        regional_foods: Dict[str, List[str]]) -> Dict[str, Any]:
        """Filter meal plan foods by regional availability"""
        all_available_foods = [food for foods in regional_foods.values() for food in foods]
        
        for meal, categories in meal_plan.items():
            for category, foods in categories.items():
                if isinstance(foods, list):
                    meal_plan[meal][category] = [food for food in foods if food in all_available_foods]
        
        return meal_plan
