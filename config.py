import os
from typing import Dict, Any

class Config:
    """Configuration for Google ADK agents"""
    
    def __init__(self):
        self.project_id = os.getenv("GOOGLE_CLOUD_PROJECT_ID", "your-project-id")
        self.location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
        self.model_name = os.getenv("MODEL_NAME", "gemini-1.5-flash")
        
        # Agent configurations
        self.patient_profile_agent_config = {
            "name": "patient-profile-agent",
            "description": "Analyzes patient health data to create comprehensive profiles",
            "instructions": """You are a medical data analyst specializing in Kenyan healthcare.
            Your role is to:
            1. Calculate BMI and assess health risks
            2. Categorize health status based on multiple factors
            3. Determine dietary restrictions based on medical conditions
            4. Provide accurate calorie needs calculations
            
            Always consider Kenyan health standards and local health challenges."""
        }
        
        self.regional_food_agent_config = {
            "name": "regional-food-agent", 
            "description": "Expert on Kenyan regional foods and nutritional information",
            "instructions": """You are a nutrition expert specializing in Kenyan regional foods.
            Your role is to:
            1. Identify foods available in different Kenyan regions
            2. Provide accurate nutritional information for local foods
            3. Consider seasonal availability and cultural preferences
            4. Map locations to appropriate regional food categories
            
            Use your knowledge of Kenyan geography, climate, and agricultural patterns."""
        }
        
        self.food_recommendation_agent_config = {
            "name": "food-recommendation-agent",
            "description": "Creates personalized nutrition recommendations for Kenyan patients", 
            "instructions": """You are a nutrition counselor specializing in Kenyan dietary patterns.
            Your role is to:
            1. Create balanced meal plans using locally available foods
            2. Consider health conditions like diabetes, hypertension
            3. Provide culturally appropriate food recommendations
            4. Balance nutritional needs with regional food availability
            5. Give practical portion and timing guidance
            
            Always prioritize patient health while respecting cultural food preferences."""
        }

config = Config()
