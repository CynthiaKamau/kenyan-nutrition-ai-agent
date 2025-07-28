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
    
    def get_regional_foods(self, location: str) -> Dict[str, List[str]]:
        """Get foods available in a specific region"""
        location_lower = location.lower()
        
        # Map common location names to regions
        region_mapping = {
            # Central Kenya
            "nairobi": "central", "kiambu": "central", "murang'a": "central", "nyeri": "central",
            "kirinyaga": "central", "nyandarua": "central", "meru": "central", "tharaka-nithi": "central",
            
            # Coastal Region
            "mombasa": "coastal", "kilifi": "coastal", "kwale": "coastal", "lamu": "coastal",
            "tana river": "coastal", "taita-taveta": "coastal",
            
            # Western Kenya
            "kisumu": "western", "kakamega": "western", "bungoma": "western", "vihiga": "western",
            "siaya": "western", "busia": "western", "trans-nzoia": "western",
            
            # Eastern Kenya
            "machakos": "eastern", "kitui": "eastern", "makueni": "eastern", "embu": "eastern",
            "isiolo": "eastern", "marsabit": "eastern", "moyale": "eastern",
            
            # Northern Kenya
            "garissa": "northern", "mandera": "northern", "wajir": "northern", "turkana": "northern",
            "west pokot": "northern", "samburu": "northern",
            
            # Nyanza Region
            "kisii": "nyanza", "nyamira": "nyanza", "homa bay": "nyanza", "migori": "nyanza",
            "kericho": "nyanza", "bomet": "nyanza",
            
            # Rift Valley
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
    
    def get_nutritional_info(self, food_item: str) -> Dict[str, Any]:
        """Get basic nutritional information for food items"""
        nutrition_db = {
            # Grains
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
        
        return nutrition_db.get(food_item, {"calories_per_100g": 0, "carbs": 0, "protein": 0, "fat": 0, "fiber": 0, "gi": 50})
    
    def filter_foods_by_availability(self, location: str, season: str = "all") -> Dict[str, List[str]]:
        """Filter foods by regional availability and season"""
        regional_foods = self.get_regional_foods(location)
        
        # For now, return all regional foods - can be extended to include seasonal filtering
        return regional_foods
