from typing import Dict, Any, Optional
import logging

class PatientProfileAgent:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def create_patient_profile(self, 
                             age: int,
                             weight: float,
                             height: float,
                             blood_sugar: float,
                             blood_pressure: Dict[str, int],  # {"systolic": 120, "diastolic": 80}
                             diabetes_status: str,  # "none", "type1", "type2", "prediabetes"
                             location: str) -> Dict[str, Any]:
        """Create a comprehensive patient profile"""
        
        bmi = self.calculate_bmi(weight, height)
        health_category = self.categorize_health_status(
            age, bmi, blood_sugar, blood_pressure, diabetes_status
        )
        
        profile = {
            "age": age,
            "weight": weight,
            "height": height,
            "bmi": bmi,
            "blood_sugar": blood_sugar,
            "blood_pressure": blood_pressure,
            "diabetes_status": diabetes_status,
            "location": location,
            "health_category": health_category,
            "dietary_restrictions": self.get_dietary_restrictions(diabetes_status, health_category),
            "calorie_needs": self.calculate_calorie_needs(age, weight, height)
        }
        
        return profile
    
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
        """Calculate daily calorie needs using Mifflin-St Jeor equation (assuming moderate activity)"""
        # Simplified calculation - assumes average gender distribution
        bmr = (10 * weight) + (6.25 * height * 100) - (5 * age) + 5  # Male formula as baseline
        return int(bmr * 1.55)  # Moderate activity level
