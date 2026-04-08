from typing import Any, Dict
import logging

from data_loader import get_data_loader


class RegionalFoodAgent:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.data_loader = get_data_loader()
        self.regional_foods = self.data_loader.regional_foods
        self.logger.info("Regional foods loaded from Excel file")

    def get_nutritional_info(self, food_item: str) -> Dict[str, Any]:
        """Get nutritional information for food items from Excel data."""
        nutrition = self.data_loader.get_nutrition_info(food_item)
        if nutrition.get("calories_per_100g", 0) != 0:
            return nutrition

        return {
            "calories_per_100g": 0,
            "carbs": 0,
            "protein": 0,
            "fat": 0,
            "fiber": 0,
            "gi": 50,
        }
