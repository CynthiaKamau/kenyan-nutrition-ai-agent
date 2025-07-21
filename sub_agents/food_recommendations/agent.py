from typing import Dict, List, Any, Tuple
import logging
from ..patient_profiles.agent import PatientProfileAgent
from ..regions_for_food.agent import RegionalFoodAgent

class FoodRecommendationAgent:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.patient_agent = PatientProfileAgent()
        self.regional_agent = RegionalFoodAgent()
    
    def generate_recommendations(self, patient_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Generate personalized food recommendations based on patient profile and regional availability"""
        
        regional_foods = self.regional_agent.get_regional_foods(patient_profile["location"])
        dietary_restrictions = patient_profile["dietary_restrictions"]
        health_category = patient_profile["health_category"]
        diabetes_status = patient_profile["diabetes_status"]
        
        recommendations = {
            "meal_plan": self._create_meal_plan(regional_foods, dietary_restrictions, patient_profile),
            "preferred_foods": self._get_preferred_foods(regional_foods, dietary_restrictions),
            "foods_to_limit": self._get_foods_to_limit(regional_foods, dietary_restrictions),
            "portion_guidelines": self._get_portion_guidelines(patient_profile),
            "meal_timing": self._get_meal_timing_advice(diabetes_status)
        }
        
        return recommendations
    
    def _create_meal_plan(self, regional_foods: Dict[str, List[str]], 
                         restrictions: Dict[str, bool], 
                         profile: Dict[str, Any]) -> Dict[str, Dict[str, List[str]]]:
        """Create a balanced meal plan for the day"""
        
        meal_plan = {
            "breakfast": {
                "grains": [],
                "proteins": [],
                "vegetables": [],
                "fruits": []
            },
            "lunch": {
                "grains": [],
                "proteins": [],
                "vegetables": [],
                "legumes": []
            },
            "dinner": {
                "grains": [],
                "proteins": [],
                "vegetables": []
            },
            "snacks": {
                "fruits": [],
                "nuts": []
            }
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
