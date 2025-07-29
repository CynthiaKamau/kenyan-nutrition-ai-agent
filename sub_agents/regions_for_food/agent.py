from typing import List, Dict, Any
import logging
import json
from google.cloud import aiplatform
from vertexai.generative_models import GenerativeModel
from config import config
from utils.feedback import FeedbackCollector

class RegionalFoodAgent:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.agent_config = config.regional_food_agent_config
        self.feedback_collector = FeedbackCollector()
        self.regional_foods = self._initialize_regional_foods()
        
        # Initialize Vertex AI
        aiplatform.init(project=config.project_id, location=config.location)
        self.model = GenerativeModel(config.model_name)
        
        self.logger.info(f"Regional Food Agent initialized with model: {config.model_name}")
    
    def get_regional_foods(self, location: str, session_id: str = None) -> Dict[str, List[str]]:
        """Get foods available in a specific region using ADK"""
        
        prompt = f"""
        {self.agent_config['instructions']}
        
        Location: {location}
        
        Based on your knowledge of Kenyan geography and agriculture, identify foods available in this location.
        Consider the climate, traditional farming practices, and cultural preferences.
        
        Return a JSON object categorizing available foods:
        {{
            "grains": ["list of grains available"],
            "vegetables": ["list of vegetables available"],
            "fruits": ["list of fruits available"], 
            "legumes": ["list of legumes available"],
            "proteins": ["list of protein sources available"]
        }}
        
        Include traditional Kenyan foods and consider seasonal availability.
        """
        
        try:
            response = self.model.generate_content(prompt)
            
            # Parse response
            response_text = response.text.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:-3]
            elif response_text.startswith("```"):
                response_text = response_text[3:-3]
            
            ai_foods = json.loads(response_text)
            
            # Enhance with local database and validate
            enhanced_foods = self._enhance_with_local_data(location, ai_foods)
            
            # Collect feedback if session_id provided
            if session_id:
                self.feedback_collector.collect_user_feedback(
                    self.agent_config['name'],
                    session_id,
                    {"location": location},
                    enhanced_foods
                )
            
            return enhanced_foods
            
        except Exception as e:
            self.logger.error(f"Error getting regional foods: {e}")
            # Fallback to local database
            return self._get_regional_foods_fallback(location)
    
    def get_nutritional_info(self, food_item: str, session_id: str = None) -> Dict[str, Any]:
        """Get nutritional information using ADK with local data enhancement"""
        
        # Check local database first
        local_nutrition = self._get_local_nutrition_data(food_item)
        
        prompt = f"""
        {self.agent_config['instructions']}
        
        Food Item: {food_item}
        
        Provide detailed nutritional information for this Kenyan food item.
        Include cultural context and preparation methods if relevant.
        
        Return a JSON object with:
        {{
            "calories_per_100g": number,
            "carbs": grams_per_100g,
            "protein": grams_per_100g,
            "fat": grams_per_100g,
            "fiber": grams_per_100g,
            "gi": glycemic_index_value,
            "cultural_context": "how this food is traditionally used",
            "health_benefits": ["list of specific health benefits"],
            "preparation_notes": "traditional preparation methods"
        }}
        """
        
        try:
            response = self.model.generate_content(prompt)
            
            response_text = response.text.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:-3]
            elif response_text.startswith("```"):
                response_text = response_text[3:-3]
            
            ai_nutrition = json.loads(response_text)
            
            # Merge with local data (local data takes precedence for basic nutrients)
            enhanced_nutrition = {**ai_nutrition, **local_nutrition}
            
            return enhanced_nutrition
            
        except Exception as e:
            self.logger.error(f"Error getting nutritional info: {e}")
            return local_nutrition if local_nutrition else self._default_nutrition_fallback()
    
    def _enhance_with_local_data(self, location: str, ai_foods: Dict[str, List[str]]) -> Dict[str, List[str]]:
        """Enhance AI recommendations with local database"""
        fallback_foods = self._get_regional_foods_fallback(location)
        
        enhanced = {}
        for category in ["grains", "vegetables", "fruits", "legumes", "proteins"]:
            ai_category = ai_foods.get(category, [])
            local_category = fallback_foods.get(category, [])
            
            # Combine and deduplicate
            combined = list(set(ai_category + local_category))
            enhanced[category] = combined
        
        return enhanced
    
    def _get_regional_foods_fallback(self, location: str) -> Dict[str, List[str]]:
        """Fallback to local database"""
        location_lower = location.lower()
        
        region_mapping = {
            "nairobi": "central", "kiambu": "central", "murang'a": "central", "nyeri": "central",
            "kirinyaga": "central", "nyandarua": "central", "meru": "central", "tharaka-nithi": "central",
            "mombasa": "coastal", "kilifi": "coastal", "kwale": "coastal", "lamu": "coastal",
            "tana river": "coastal", "taita-taveta": "coastal",
            "kisumu": "western", "kakamega": "western", "bungoma": "western", "vihiga": "western",
            "siaya": "western", "busia": "western", "trans-nzoia": "western",
            "machakos": "eastern", "kitui": "eastern", "makueni": "eastern", "embu": "eastern",
            "isiolo": "eastern", "marsabit": "eastern", "moyale": "eastern",
            "garissa": "northern", "mandera": "northern", "wajir": "northern", "turkana": "northern",
            "west pokot": "northern", "samburu": "northern",
            "kisii": "nyanza", "nyamira": "nyanza", "homa bay": "nyanza", "migori": "nyanza",
            "kericho": "nyanza", "bomet": "nyanza",
            "nakuru": "rift_valley", "eldoret": "rift_valley", "narok": "rift_valley", 
            "kajiado": "rift_valley", "laikipia": "rift_valley", "nandi": "rift_valley",
            "uasin gishu": "rift_valley", "elgeyo-marakwet": "rift_valley", "baringo": "rift_valley"
        }
        
        region = region_mapping.get(location_lower, location_lower)
        
        if region in self.regional_foods:
            return self.regional_foods[region]
        else:
            self.logger.warning(f"Region '{location}' not found. Using central region as default.")
            return self.regional_foods["central"]
    
    def _get_local_nutrition_data(self, food_item: str) -> Dict[str, Any]:
        """Get nutrition data from local database"""
        nutrition_db = {
            "maize": {"calories_per_100g": 365, "carbs": 74, "protein": 9, "fat": 4.7, "fiber": 7.3, "gi": 60},
            "rice": {"calories_per_100g": 365, "carbs": 80, "protein": 7, "fat": 0.7, "fiber": 1.3, "gi": 73},
            "millet": {"calories_per_100g": 378, "carbs": 73, "protein": 11, "fat": 4.2, "fiber": 8.5, "gi": 71},
            "wheat": {"calories_per_100g": 340, "carbs": 72, "protein": 13, "fat": 2.5, "fiber": 12.2, "gi": 30},
            "barley": {"calories_per_100g": 354, "carbs": 73, "protein": 12, "fat": 2.3, "fiber": 17.3, "gi": 25},
            "sorghum": {"calories_per_100g": 339, "carbs": 75, "protein": 11, "fat": 3.3, "fiber": 6.3, "gi": 62},
            "finger_millet": {"calories_per_100g": 336, "carbs": 72, "protein": 7.3, "fat": 1.3, "fiber": 3.6, "gi": 104},
            "pearl_millet": {"calories_per_100g": 361, "carbs": 67, "protein": 11, "fat": 5, "fiber": 8.5, "gi": 67},
            "cassava": {"calories_per_100g": 160, "carbs": 38, "protein": 1.4, "fat": 0.3, "fiber": 1.8, "gi": 46},
            "oats": {"calories_per_100g": 389, "carbs": 66, "protein": 17, "fat": 7, "fiber": 10.6, "gi": 55},
            
            # Vegetables
            "kale": {"calories_per_100g": 35, "carbs": 4.4, "protein": 2.9, "fat": 0.4, "fiber": 4.1, "gi": 15},
            "spinach": {"calories_per_100g": 23, "carbs": 3.6, "protein": 2.9, "fat": 0.4, "fiber": 2.2, "gi": 15},
            "sweet_potatoes": {"calories_per_100g": 86, "carbs": 20, "protein": 1.6, "fat": 0.1, "fiber": 3, "gi": 70},
            "cabbage": {"calories_per_100g": 25, "carbs": 6, "protein": 1.3, "fat": 0.1, "fiber": 2.5, "gi": 10},
            "carrots": {"calories_per_100g": 41, "carbs": 10, "protein": 0.9, "fat": 0.2, "fiber": 2.8, "gi": 47},
            "onions": {"calories_per_100g": 40, "carbs": 9, "protein": 1.1, "fat": 0.1, "fiber": 1.7, "gi": 15},
            "tomatoes": {"calories_per_100g": 18, "carbs": 3.9, "protein": 0.9, "fat": 0.2, "fiber": 1.2, "gi": 15},
            "irish_potatoes": {"calories_per_100g": 77, "carbs": 17, "protein": 2, "fat": 0.1, "fiber": 2.2, "gi": 78},
            "potatoes": {"calories_per_100g": 77, "carbs": 17, "protein": 2, "fat": 0.1, "fiber": 2.2, "gi": 78},
            "beans_leaves": {"calories_per_100g": 45, "carbs": 9, "protein": 4.2, "fat": 0.5, "fiber": 4.8, "gi": 15},
            "okra": {"calories_per_100g": 33, "carbs": 7, "protein": 1.9, "fat": 0.2, "fiber": 3.2, "gi": 20},
            "eggplant": {"calories_per_100g": 25, "carbs": 6, "protein": 1, "fat": 0.2, "fiber": 3, "gi": 15},
            "amaranth": {"calories_per_100g": 23, "carbs": 4.6, "protein": 2.5, "fat": 0.3, "fiber": 2.1, "gi": 15},
            "cassava_leaves": {"calories_per_100g": 37, "carbs": 7, "protein": 3.7, "fat": 0.6, "fiber": 3.7, "gi": 15},
            "pumpkin_leaves": {"calories_per_100g": 19, "carbs": 3.9, "protein": 3, "fat": 0.2, "fiber": 2.2, "gi": 15},
            "pumpkin": {"calories_per_100g": 26, "carbs": 7, "protein": 1, "fat": 0.1, "fiber": 0.5, "gi": 75},
            "spider_plant": {"calories_per_100g": 30, "carbs": 5.5, "protein": 3.5, "fat": 0.4, "fiber": 3.2, "gi": 15},
            "nightshade": {"calories_per_100g": 28, "carbs": 5.8, "protein": 2.5, "fat": 0.3, "fiber": 2.8, "gi": 15},
            
            # Fruits
            "bananas": {"calories_per_100g": 89, "carbs": 23, "protein": 1.1, "fat": 0.3, "fiber": 2.6, "gi": 62},
            "mangoes": {"calories_per_100g": 60, "carbs": 15, "protein": 0.8, "fat": 0.4, "fiber": 1.6, "gi": 51},
            "avocados": {"calories_per_100g": 160, "carbs": 9, "protein": 2, "fat": 15, "fiber": 7, "gi": 15},
            "oranges": {"calories_per_100g": 47, "carbs": 12, "protein": 0.9, "fat": 0.1, "fiber": 2.4, "gi": 45},
            "passion_fruit": {"calories_per_100g": 97, "carbs": 23, "protein": 2.2, "fat": 0.7, "fiber": 10.4, "gi": 30},
            "tree_tomatoes": {"calories_per_100g": 31, "carbs": 6, "protein": 2, "fat": 0.4, "fiber": 3.3, "gi": 25},
            "macadamia": {"calories_per_100g": 718, "carbs": 14, "protein": 8, "fat": 76, "fiber": 8.6, "gi": 15},
            "coconut": {"calories_per_100g": 354, "carbs": 15, "protein": 3.3, "fat": 33, "fiber": 9, "gi": 45},
            "jackfruit": {"calories_per_100g": 95, "carbs": 23, "protein": 1.7, "fat": 0.6, "fiber": 1.5, "gi": 75},
            "baobab_fruit": {"calories_per_100g": 162, "carbs": 38, "protein": 2.3, "fat": 0.2, "fiber": 44.5, "gi": 35},
            "cashew_fruit": {"calories_per_100g": 46, "carbs": 10, "protein": 0.8, "fat": 0.5, "fiber": 1.7, "gi": 25},
            "tamarind": {"calories_per_100g": 239, "carbs": 63, "protein": 2.8, "fat": 0.6, "fiber": 5.1, "gi": 23},
            "sugarcane": {"calories_per_100g": 58, "carbs": 13, "protein": 0.4, "fat": 0.5, "fiber": 0.6, "gi": 43},
            "pineapples": {"calories_per_100g": 50, "carbs": 13, "protein": 0.5, "fat": 0.1, "fiber": 1.4, "gi": 66},
            "guavas": {"calories_per_100g": 68, "carbs": 14, "protein": 2.6, "fat": 1, "fiber": 5.4, "gi": 12},
            "dates": {"calories_per_100g": 282, "carbs": 75, "protein": 2.5, "fat": 0.4, "fiber": 8, "gi": 55},
            "watermelon": {"calories_per_100g": 30, "carbs": 8, "protein": 0.6, "fat": 0.2, "fiber": 0.4, "gi": 72},
            "doum_palm": {"calories_per_100g": 120, "carbs": 30, "protein": 1.5, "fat": 0.5, "fiber": 4.2, "gi": 45},
            "apples": {"calories_per_100g": 52, "carbs": 14, "protein": 0.3, "fat": 0.2, "fiber": 2.4, "gi": 36},
            "strawberries": {"calories_per_100g": 32, "carbs": 8, "protein": 0.7, "fat": 0.3, "fiber": 2, "gi": 40},
            
            # Legumes
            "beans": {"calories_per_100g": 245, "carbs": 45, "protein": 15, "fat": 1, "fiber": 15, "gi": 29},
            "groundnuts": {"calories_per_100g": 567, "carbs": 16, "protein": 26, "fat": 49, "fiber": 8.5, "gi": 14},
            "peas": {"calories_per_100g": 81, "carbs": 14, "protein": 5, "fat": 0.4, "fiber": 5.7, "gi": 22},
            "green_grams": {"calories_per_100g": 347, "carbs": 63, "protein": 24, "fat": 1.2, "fiber": 16.3, "gi": 25},
            "cowpeas": {"calories_per_100g": 336, "carbs": 60, "protein": 24, "fat": 1.3, "fiber": 10.6, "gi": 33},
            "pigeon_peas": {"calories_per_100g": 343, "carbs": 63, "protein": 22, "fat": 1.5, "fiber": 15, "gi": 22},
            "bambara_nuts": {"calories_per_100g": 367, "carbs": 57, "protein": 19, "fat": 6.5, "fiber": 5.6, "gi": 30},
            "soya_beans": {"calories_per_100g": 446, "carbs": 30, "protein": 36, "fat": 20, "fiber": 9.3, "gi": 25},
            "black_eyed_peas": {"calories_per_100g": 336, "carbs": 60, "protein": 24, "fat": 1.3, "fiber": 10.6, "gi": 33},
            
            # Proteins
            "chicken": {"calories_per_100g": 165, "carbs": 0, "protein": 31, "fat": 3.6, "fiber": 0, "gi": 0},
            "fish": {"calories_per_100g": 206, "carbs": 0, "protein": 22, "fat": 12, "fiber": 0, "gi": 0},
            "eggs": {"calories_per_100g": 155, "carbs": 1.1, "protein": 13, "fat": 11, "fiber": 0, "gi": 0},
            "beef": {"calories_per_100g": 250, "carbs": 0, "protein": 26, "fat": 17, "fiber": 0, "gi": 0},
            "goat_meat": {"calories_per_100g": 143, "carbs": 0, "protein": 27, "fat": 3, "fiber": 0, "gi": 0},
            "camel_meat": {"calories_per_100g": 217, "carbs": 0, "protein": 19, "fat": 16, "fiber": 0, "gi": 0},
            "lamb": {"calories_per_100g": 294, "carbs": 0, "protein": 25, "fat": 21, "fiber": 0, "gi": 0},
            "milk": {"calories_per_100g": 61, "carbs": 4.8, "protein": 3.2, "fat": 3.3, "fiber": 0, "gi": 15},
            "camel_milk": {"calories_per_100g": 46, "carbs": 4.4, "protein": 3, "fat": 2.4, "fiber": 0, "gi": 15},
            "coconut_milk": {"calories_per_100g": 230, "carbs": 6, "protein": 2.3, "fat": 24, "fiber": 2.2, "gi": 25},
            "dairy_products": {"calories_per_100g": 113, "carbs": 4.7, "protein": 3.4, "fat": 9, "fiber": 0, "gi": 15},
            "seafood": {"calories_per_100g": 85, "carbs": 0, "protein": 18, "fat": 1.2, "fiber": 0, "gi": 0},
            "prawns": {"calories_per_100g": 71, "carbs": 0.9, "protein": 13, "fat": 1.4, "fiber": 0, "gi": 0},
            "crabs": {"calories_per_100g": 97, "carbs": 0, "protein": 20, "fat": 1.5, "fiber": 0, "gi": 0},
            "tilapia": {"calories_per_100g": 129, "carbs": 0, "protein": 26, "fat": 2.6, "fiber": 0, "gi": 0}
        }
        
        return nutrition_db.get(food_item, {})
    
    def _default_nutrition_fallback(self) -> Dict[str, Any]:
        """Default nutrition values when all else fails"""
        return {"calories_per_100g": 0, "carbs": 0, "protein": 0, "fat": 0, "fiber": 0, "gi": 50}
    
    def _initialize_regional_foods(self) -> Dict[str, Dict[str, List[str]]]:
        """Initialize database of foods available in different Kenyan regions"""
        return {
            "central": {
                "grains": ["maize", "wheat", "barley", "millet", "rice"],
                "vegetables": ["kale", "spinach", "cabbage", "carrots", "onions", "tomatoes", "sweet_potatoes", "irish_potatoes", "potatoes", "beans_leaves"],
                "fruits": ["bananas", "oranges", "mangoes", "avocados", "passion_fruit", "tree_tomatoes", "macadamia"],
                "legumes": ["beans", "peas", "groundnuts", "green_grams"],
                "proteins": ["chicken", "beef", "goat_meat", "fish", "eggs", "milk", "dairy_products"]
            },
            "coastal": {
                "grains": ["rice", "maize", "cassava", "millet", "sorghum"],
                "vegetables": ["coconut", "okra", "eggplant", "amaranth", "sweet_potatoes", "cassava_leaves", "pumpkin_leaves", "spinach"],
                "fruits": ["coconut", "mangoes", "jackfruit", "baobab_fruit", "oranges", "bananas", "cashew_fruit", "tamarind"],
                "legumes": ["cowpeas", "pigeon_peas", "green_grams", "bambara_nuts"],
                "proteins": ["fish", "seafood", "prawns", "crabs", "chicken", "goat_meat", "coconut_milk"]
            },
            "western": {
                "grains": ["maize", "millet", "sorghum", "finger_millet", "rice"],
                "vegetables": ["kale", "spinach", "pumpkin", "sweet_potatoes", "irish_potatoes", "onions", "tomatoes", "cabbage"],
                "fruits": ["bananas", "sugarcane", "pineapples", "passion_fruit", "oranges", "mangoes", "guavas"],
                "legumes": ["beans", "groundnuts", "soya_beans", "cowpeas"],
                "proteins": ["fish", "chicken", "beef", "milk", "eggs", "tilapia"]
            },
            "northern": {
                "grains": ["sorghum", "millet", "maize", "pearl_millet"],
                "vegetables": ["kale", "onions", "tomatoes", "sweet_potatoes", "pumpkin", "amaranth"],
                "fruits": ["dates", "mangoes", "watermelon", "doum_palm"],
                "legumes": ["cowpeas", "pigeon_peas", "black_eyed_peas"],
                "proteins": ["goat_meat", "camel_meat", "beef", "milk", "camel_milk"]
            },
            "eastern": {
                "grains": ["maize", "millet", "sorghum", "finger_millet"],
                "vegetables": ["kale", "spinach", "pumpkin", "sweet_potatoes", "cassava", "onions", "tomatoes"],
                "fruits": ["mangoes", "oranges", "bananas", "watermelon", "baobab_fruit", "passion_fruit"],
                "legumes": ["cowpeas", "green_grams", "pigeon_peas", "beans"],
                "proteins": ["goat_meat", "beef", "chicken", "milk", "eggs"]
            },
            "nyanza": {
                "grains": ["maize", "millet", "sorghum", "finger_millet", "rice"],
                "vegetables": ["kale", "spinach", "sweet_potatoes", "pumpkin", "amaranth", "spider_plant", "nightshade"],
                "fruits": ["bananas", "oranges", "mangoes", "sugarcane", "passion_fruit", "guavas"],
                "legumes": ["beans", "groundnuts", "soya_beans", "cowpeas", "green_grams"],
                "proteins": ["fish", "tilapia", "chicken", "beef", "milk", "eggs"]
            },
            "rift_valley": {
                "grains": ["maize", "wheat", "barley", "millet", "oats"],
                "vegetables": ["kale", "cabbage", "carrots", "onions", "irish_potatoes", "sweet_potatoes", "spinach"],
                "fruits": ["bananas", "oranges", "mangoes", "apples", "passion_fruit", "strawberries"],
                "legumes": ["beans", "peas", "groundnuts", "green_grams"],
                "proteins": ["beef", "lamb", "chicken", "milk", "eggs", "dairy_products"]
            }
        }
    
    def filter_foods_by_availability(self, location: str, season: str = "all") -> Dict[str, List[str]]:
        """Filter foods by regional availability and season"""
        return self.get_regional_foods(location)
