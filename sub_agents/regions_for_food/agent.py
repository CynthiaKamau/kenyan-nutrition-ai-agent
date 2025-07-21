from typing import List, Dict, Any
import logging

class RegionalFoodAgent:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.regional_foods = self._initialize_regional_foods()
    
    def _initialize_regional_foods(self) -> Dict[str, Dict[str, List[str]]]:
        """Initialize database of foods available in different Kenyan regions"""
        return {
            "central": {
                "grains": ["maize", "wheat", "barley", "millet"],
                "vegetables": ["kale", "spinach", "cabbage", "carrots", "onions", "tomatoes", "sweet_potatoes"],
                "fruits": ["bananas", "oranges", "mangoes", "avocados", "passion_fruit"],
                "legumes": ["beans", "peas", "groundnuts"],
                "proteins": ["chicken", "beef", "goat_meat", "fish", "eggs", "milk"]
            },
            "coastal": {
                "grains": ["rice", "maize", "cassava", "millet"],
                "vegetables": ["coconut", "okra", "eggplant", "amaranth", "sweet_potatoes", "cassava_leaves"],
                "fruits": ["coconut", "mangoes", "jackfruit", "baobab_fruit", "oranges", "bananas"],
                "legumes": ["cowpeas", "pigeon_peas", "green_grams"],
                "proteins": ["fish", "seafood", "chicken", "goat_meat", "coconut_milk"]
            },
            "western": {
                "grains": ["maize", "millet", "sorghum", "finger_millet"],
                "vegetables": ["kale", "spinach", "pumpkin", "sweet_potatoes", "irish_potatoes"],
                "fruits": ["bananas", "sugarcane", "pineapples", "passion_fruit"],
                "legumes": ["beans", "groundnuts", "soya_beans"],
                "proteins": ["fish", "chicken", "beef", "milk", "eggs"]
            },
            "northern": {
                "grains": ["sorghum", "millet", "maize"],
                "vegetables": ["kale", "onions", "tomatoes", "sweet_potatoes"],
                "fruits": ["dates", "mangoes", "watermelon"],
                "legumes": ["cowpeas", "pigeon_peas"],
                "proteins": ["goat_meat", "camel_meat", "beef", "milk"]
            },
            "eastern": {
                "grains": ["maize", "millet", "sorghum"],
                "vegetables": ["kale", "spinach", "pumpkin", "sweet_potatoes", "cassava"],
                "fruits": ["mangoes", "oranges", "bananas", "watermelon"],
                "legumes": ["cowpeas", "green_grams", "pigeon_peas"],
                "proteins": ["goat_meat", "beef", "chicken", "milk"]
            }
        }
    
    def get_regional_foods(self, location: str) -> Dict[str, List[str]]:
        """Get foods available in a specific region"""
        location_lower = location.lower()
        
        # Map common location names to regions
        region_mapping = {
            "nairobi": "central", "kiambu": "central", "murang'a": "central", "nyeri": "central",
            "mombasa": "coastal", "kilifi": "coastal", "kwale": "coastal", "lamu": "coastal",
            "kisumu": "western", "kakamega": "western", "bungoma": "western", "vihiga": "western",
            "garissa": "northern", "mandera": "northern", "wajir": "northern", "turkana": "northern",
            "machakos": "eastern", "kitui": "eastern", "makueni": "eastern", "embu": "eastern"
        }
        
        region = region_mapping.get(location_lower, location_lower)
        
        if region in self.regional_foods:
            return self.regional_foods[region]
        else:
            self.logger.warning(f"Region '{location}' not found. Using central region as default.")
            return self.regional_foods["central"]
    
    def get_nutritional_info(self, food_item: str) -> Dict[str, Any]:
        """Get basic nutritional information for food items"""
        nutrition_db = {
            # Grains
            "maize": {"calories_per_100g": 365, "carbs": 74, "protein": 9, "fat": 4.7, "fiber": 7.3, "gi": 60},
            "rice": {"calories_per_100g": 365, "carbs": 80, "protein": 7, "fat": 0.7, "fiber": 1.3, "gi": 73},
            "millet": {"calories_per_100g": 378, "carbs": 73, "protein": 11, "fat": 4.2, "fiber": 8.5, "gi": 71},
            
            # Vegetables
            "kale": {"calories_per_100g": 35, "carbs": 4.4, "protein": 2.9, "fat": 0.4, "fiber": 4.1, "gi": 15},
            "spinach": {"calories_per_100g": 23, "carbs": 3.6, "protein": 2.9, "fat": 0.4, "fiber": 2.2, "gi": 15},
            "sweet_potatoes": {"calories_per_100g": 86, "carbs": 20, "protein": 1.6, "fat": 0.1, "fiber": 3, "gi": 70},
            
            # Fruits
            "bananas": {"calories_per_100g": 89, "carbs": 23, "protein": 1.1, "fat": 0.3, "fiber": 2.6, "gi": 62},
            "mangoes": {"calories_per_100g": 60, "carbs": 15, "protein": 0.8, "fat": 0.4, "fiber": 1.6, "gi": 51},
            "avocados": {"calories_per_100g": 160, "carbs": 9, "protein": 2, "fat": 15, "fiber": 7, "gi": 15},
            
            # Legumes
            "beans": {"calories_per_100g": 245, "carbs": 45, "protein": 15, "fat": 1, "fiber": 15, "gi": 29},
            "groundnuts": {"calories_per_100g": 567, "carbs": 16, "protein": 26, "fat": 49, "fiber": 8.5, "gi": 14},
            
            # Proteins
            "chicken": {"calories_per_100g": 165, "carbs": 0, "protein": 31, "fat": 3.6, "fiber": 0, "gi": 0},
            "fish": {"calories_per_100g": 206, "carbs": 0, "protein": 22, "fat": 12, "fiber": 0, "gi": 0},
            "eggs": {"calories_per_100g": 155, "carbs": 1.1, "protein": 13, "fat": 11, "fiber": 0, "gi": 0}
        }
        
        return nutrition_db.get(food_item, {"calories_per_100g": 0, "carbs": 0, "protein": 0, "fat": 0, "fiber": 0, "gi": 50})
    
    def filter_foods_by_availability(self, location: str, season: str = "all") -> Dict[str, List[str]]:
        """Filter foods by regional availability and season"""
        regional_foods = self.get_regional_foods(location)
        
        # For now, return all regional foods - can be extended to include seasonal filtering
        return regional_foods
