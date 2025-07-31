from typing import Dict, Any, Optional
import logging
import json
from google.cloud import aiplatform
from vertexai.generative_models import GenerativeModel
from config import config
from utils.feedback import FeedbackCollector

class PatientProfileAgent:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.agent_config = config.patient_profile_agent_config
        self.feedback_collector = FeedbackCollector()
        
        # Initialize Vertex AI
        try:
            config.initialize_vertex_ai()
        except Exception:
            self.logger.error("Failed to initialize Vertex AI. Using fallback logic.")
        
        aiplatform.init(project=config.project_id, location=config.location)
        self.model = GenerativeModel(config.model_name)
        
        self.logger.info(f"Patient Profile Agent initialized with model: {config.model_name}")
    
    def create_patient_profile(self, 
                             age: int,
                             weight: float,
                             height: float,
                             blood_sugar: float,
                             blood_pressure: Dict[str, int],
                             diabetes_status: str,
                             location: str,
                             session_id: str = None) -> Dict[str, Any]:
        """Create a comprehensive patient profile using ADK"""
        
        # Prepare input for the model
        patient_data = {
            "age": age,
            "weight": weight,
            "height": height,
            "blood_sugar": blood_sugar,
            "blood_pressure": blood_pressure,
            "diabetes_status": diabetes_status,
            "location": location
        }
        
        prompt = f"""
        {self.agent_config['instructions']}
        
        Patient Data:
        {json.dumps(patient_data, indent=2)}
        
        Please analyze this patient data and create a comprehensive profile including:
        1. BMI calculation (weight in kg / height in meters squared)
        2. Health risk categorization (low_risk, moderate_risk, high_risk)
        3. Dietary restrictions based on health conditions
        4. Daily calorie needs calculation
        
        Return your analysis as a JSON object with the following structure:
        {{
            "age": {age},
            "weight": {weight},
            "height": {height},
            "bmi": calculated_bmi,
            "blood_sugar": {blood_sugar},
            "blood_pressure": {blood_pressure},
            "diabetes_status": "{diabetes_status}",
            "location": "{location}",
            "health_category": "risk_level",
            "dietary_restrictions": {{
                "limit_sugar": boolean,
                "limit_sodium": boolean,
                "portion_control": boolean,
                "increase_fiber": boolean,
                "limit_saturated_fat": boolean
            }},
            "calorie_needs": calculated_calories,
            "analysis_reasoning": "explanation of categorization"
        }}
        """
        
        try:
            response = self.model.generate_content(prompt)
            
            # Parse the JSON response
            response_text = response.text.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:-3]
            elif response_text.startswith("```"):
                response_text = response_text[3:-3]
            
            profile = json.loads(response_text)
            
            # Validate and add fallback calculations
            profile = self._validate_profile(profile, patient_data)
            
            # Collect feedback if session_id provided
            if session_id:
                self.feedback_collector.collect_user_feedback(
                    self.agent_config['name'],
                    session_id,
                    patient_data,
                    profile
                )
            
            return profile
            
        except Exception as e:
            self.logger.error(f"Error generating patient profile: {e}")
            # Fallback to rule-based approach
            return self._fallback_profile_creation(patient_data)
    
    def _validate_profile(self, profile: Dict[str, Any], original_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and correct profile data if needed"""
        
        # Ensure BMI is correctly calculated
        bmi = original_data['weight'] / (original_data['height'] ** 2)
        profile['bmi'] = round(bmi, 2)
        
        # Validate health category
        if profile.get('health_category') not in ['low_risk', 'moderate_risk', 'high_risk']:
            profile['health_category'] = self._categorize_health_status(
                original_data['age'], bmi, original_data['blood_sugar'],
                original_data['blood_pressure'], original_data['diabetes_status']
            )
        
        # Ensure calorie needs is reasonable (800-4000 range)
        if not isinstance(profile.get('calorie_needs'), int) or not 800 <= profile['calorie_needs'] <= 4000:
            profile['calorie_needs'] = self._calculate_calorie_needs(
                original_data['age'], original_data['weight'], original_data['height']
            )
        
        return profile
    
    def _fallback_profile_creation(self, patient_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback method using rule-based approach"""
        self.logger.info("Using fallback rule-based profile creation")
        
        bmi = self.calculate_bmi(patient_data['weight'], patient_data['height'])
        health_category = self.categorize_health_status(
            patient_data['age'], bmi, patient_data['blood_sugar'],
            patient_data['blood_pressure'], patient_data['diabetes_status']
        )
        
        return {
            "age": patient_data['age'],
            "weight": patient_data['weight'],
            "height": patient_data['height'],
            "bmi": bmi,
            "blood_sugar": patient_data['blood_sugar'],
            "blood_pressure": patient_data['blood_pressure'],
            "diabetes_status": patient_data['diabetes_status'],
            "location": patient_data['location'],
            "health_category": health_category,
            "dietary_restrictions": self.get_dietary_restrictions(patient_data['diabetes_status'], health_category),
            "calorie_needs": self.calculate_calorie_needs(patient_data['age'], patient_data['weight'], patient_data['height']),
            "analysis_reasoning": "Generated using rule-based fallback method"
        }
    
    # Keep existing helper methods as fallbacks
    def calculate_bmi(self, weight: float, height: float) -> float:
        """Calculate BMI from weight (kg) and height (m)"""
        return round(weight / (height ** 2), 2)
    
    def categorize_health_status(self, age: int, bmi: float, blood_sugar: float, 
                               blood_pressure: Dict[str, int], diabetes_status: str) -> str:
        """Categorize overall health status"""
        risk_factors = []
        
        if bmi >= 30:
            risk_factors.append("obesity")
        elif bmi >= 25:
            risk_factors.append("overweight")
            
        if blood_sugar > 126:
            risk_factors.append("high_blood_sugar")
        elif blood_sugar > 100:
            risk_factors.append("elevated_blood_sugar")
            
        if blood_pressure["systolic"] >= 140 or blood_pressure["diastolic"] >= 90:
            risk_factors.append("hypertension")
        elif blood_pressure["systolic"] >= 130 or blood_pressure["diastolic"] >= 80:
            risk_factors.append("elevated_bp")
            
        if diabetes_status in ["type1", "type2"]:
            risk_factors.append("diabetes")
        elif diabetes_status == "prediabetes":
            risk_factors.append("prediabetes")
            
        if len(risk_factors) >= 3:
            return "high_risk"
        elif len(risk_factors) >= 1:
            return "moderate_risk"
        else:
            return "low_risk"
    
    def get_dietary_restrictions(self, diabetes_status: str, health_category: str) -> Dict[str, Any]:
        """Define dietary restrictions based on health status"""
        restrictions = {
            "limit_sugar": diabetes_status in ["type1", "type2", "prediabetes"],
            "limit_sodium": health_category in ["high_risk", "moderate_risk"],
            "portion_control": health_category in ["high_risk", "moderate_risk"],
            "increase_fiber": diabetes_status in ["type2", "prediabetes"],
            "limit_saturated_fat": health_category in ["high_risk", "moderate_risk"]
        }
        return restrictions
    
    def calculate_calorie_needs(self, age: int, weight: float, height: float) -> int:
        """Calculate daily calorie needs using Mifflin-St Jeor equation"""
        bmr = (10 * weight) + (6.25 * height * 100) - (5 * age) + 5
        return int(bmr * 1.55)
    
    # Helper method aliases for backward compatibility
    _categorize_health_status = categorize_health_status
    _calculate_calorie_needs = calculate_calorie_needs
