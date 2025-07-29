from typing import Dict, Any
import logging
import json
import uuid
from sub_agents.patient_profiles.agent import PatientProfileAgent
from sub_agents.regions_for_food.agent import RegionalFoodAgent
from sub_agents.food_recommendations.agent import FoodRecommendationAgent
from utils.feedback import FeedbackCollector

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

class KenyanNutritionAgent:
    """Main agent that coordinates all ADK sub-agents for comprehensive nutrition recommendations"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Initialize ADK sub-agents
        self.patient_agent = PatientProfileAgent()
        self.regional_agent = RegionalFoodAgent()
        self.recommendation_agent = FoodRecommendationAgent()
        self.feedback_collector = FeedbackCollector()
        
        self.logger.info("Kenyan Nutrition Agent initialized with Google ADK")
    
    def get_nutrition_recommendations(self, 
                                    age: int,
                                    weight: float,
                                    height: float,
                                    blood_sugar: float,
                                    blood_pressure: Dict[str, int],
                                    diabetes_status: str,
                                    location: str,
                                    collect_feedback: bool = False) -> Dict[str, Any]:
        """
        Complete workflow using ADK agents for personalized nutrition recommendations
        
        Args:
            age: Patient age in years
            weight: Patient weight in kg
            height: Patient height in meters
            blood_sugar: Blood sugar level in mg/dL
            blood_pressure: Dict with 'systolic' and 'diastolic' values
            diabetes_status: 'none', 'type1', 'type2', or 'prediabetes'
            location: Patient's geographical location in Kenya
            collect_feedback: Whether to collect feedback for model improvement (default: False)
        
        Returns:
            Complete nutrition recommendation report
        """
        
        # Generate unique session ID for feedback tracking
        session_id = str(uuid.uuid4()) if collect_feedback else None
        
        self.logger.info(f"Starting ADK nutrition recommendation workflow - Session: {session_id}")
        
        # Step 1: Create patient profile using ADK PatientProfileAgent
        self.logger.info("Step 1: Creating patient profile with ADK...")
        patient_profile = self.patient_agent.create_patient_profile(
            age=age,
            weight=weight,
            height=height,
            blood_sugar=blood_sugar,
            blood_pressure=blood_pressure,
            diabetes_status=diabetes_status,
            location=location,
            session_id=session_id
        )
        self.logger.info(f"Patient profile created - Health category: {patient_profile['health_category']}")
        
        # Step 2: Get regional foods using ADK RegionalFoodAgent
        self.logger.info("Step 2: Identifying regional foods with ADK...")
        regional_foods = self.regional_agent.get_regional_foods(
            location, 
            session_id=session_id
        )
        available_foods_count = sum(len(foods) for foods in regional_foods.values())
        self.logger.info(f"Found {available_foods_count} foods available in {location} region")
        
        # Step 3: Generate recommendations using ADK FoodRecommendationAgent
        self.logger.info("Step 3: Generating personalized food recommendations with ADK...")
        recommendations = self.recommendation_agent.generate_recommendations(
            patient_profile,
            session_id=session_id
        )
        self.logger.info("Food recommendations generated successfully")
        
        # Compile complete report with session tracking
        complete_report = {
            "patient_profile": patient_profile,
            "regional_foods": regional_foods,
            "recommendations": recommendations,
            "summary": self._generate_summary(patient_profile, recommendations)
        }
        
        # Add session tracking and metrics if feedback is enabled
        if collect_feedback:
            complete_report["session_id"] = session_id
            complete_report["model_metrics"] = self._get_model_performance_metrics()
        
        self.logger.info("ADK nutrition recommendation workflow completed")
        return complete_report
    
    def _get_model_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for all agents"""
        metrics = {}
        
        for agent_name in ["patient-profile-agent", "regional-food-agent", "food-recommendation-agent"]:
            agent_metrics = self.feedback_collector.calculate_agent_metrics(agent_name)
            metrics[agent_name] = agent_metrics
        
        return metrics
    
    def _generate_summary(self, profile: Dict[str, Any], recommendations: Dict[str, Any]) -> Dict[str, str]:
        """Generate a summary of key findings and recommendations"""
        
        health_status = profile['health_category']
        diabetes_status = profile['diabetes_status']
        bmi_category = "Normal"
        
        if profile['bmi'] >= 30:
            bmi_category = "Obese"
        elif profile['bmi'] >= 25:
            bmi_category = "Overweight"
        elif profile['bmi'] < 18.5:
            bmi_category = "Underweight"
        
        summary = {
            "health_overview": f"Patient is {health_status} with {bmi_category} BMI ({profile['bmi']}) and {diabetes_status} diabetes status",
            "key_dietary_focus": self._get_key_dietary_focus(profile),
            "meal_frequency": recommendations['meal_timing']['frequency'],
            "primary_foods_to_include": ", ".join(recommendations['preferred_foods']['lean_proteins'][:3]),
            "foods_to_limit": ", ".join([food for foods in recommendations['foods_to_limit'].values() for food in foods][:3])
        }
        
        return summary
    
    def _get_key_dietary_focus(self, profile: Dict[str, Any]) -> str:
        """Determine the key dietary focus based on patient profile"""
        restrictions = profile['dietary_restrictions']
        
        focus_areas = []
        if restrictions['limit_sugar']:
            focus_areas.append("blood sugar control")
        if restrictions['portion_control']:
            focus_areas.append("portion management")
        if restrictions['limit_sodium']:
            focus_areas.append("sodium reduction")
        if restrictions['increase_fiber']:
            focus_areas.append("fiber intake")
        
        return ", ".join(focus_areas) if focus_areas else "general balanced nutrition"
    
    def print_recommendations(self, report: Dict[str, Any]):
        """Print a formatted version of the recommendations with model performance"""
        print("\n" + "="*60)
        print("KENYAN NUTRITION AI - ADK POWERED RECOMMENDATIONS")
        print("="*60)
        
        # Show session info
        if "session_id" in report:
            print(f"Session ID: {report['session_id']}")
        
        # Patient Summary
        profile = report['patient_profile']
        summary = report['summary']
        
        print(f"\n📊 PATIENT PROFILE:")
        print(f"   Age: {profile['age']} years")
        print(f"   BMI: {profile['bmi']} kg/m²")
        print(f"   Location: {profile['location'].title()}")
        print(f"   Health Status: {profile['health_category'].replace('_', ' ').title()}")
        print(f"   Daily Calorie Needs: {profile['calorie_needs']} kcal")
        
        print(f"\n🎯 HEALTH OVERVIEW:")
        print(f"   {summary['health_overview']}")
        print(f"   Key Focus: {summary['key_dietary_focus'].title()}")
        
        # Meal Plan
        meal_plan = report['recommendations']['meal_plan']
        print(f"\n🍽️ DAILY MEAL PLAN:")
        for meal, foods in meal_plan.items():
            print(f"\n   {meal.upper()}:")
            for food_type, food_list in foods.items():
                if food_list:
                    print(f"     {food_type.title()}: {', '.join(food_list)}")
        
        # Preferred Foods
        preferred = report['recommendations']['preferred_foods']
        print(f"\n✅ RECOMMENDED FOODS:")
        for category, foods in preferred.items():
            if foods:
                print(f"   {category.replace('_', ' ').title()}: {', '.join(foods)}")
        
        # Foods to Limit
        limit_foods = report['recommendations']['foods_to_limit']
        print(f"\n⚠️ FOODS TO LIMIT:")
        for category, foods in limit_foods.items():
            if foods:
                print(f"   {category.replace('_', ' ').title()}: {', '.join(foods)}")
        
        # Portion Guidelines
        portions = report['recommendations']['portion_guidelines']
        print(f"\n📏 PORTION GUIDELINES:")
        for food_type, guideline in portions.items():
            print(f"   {food_type.title()}: {guideline}")
        
        # Meal Timing
        timing = report['recommendations']['meal_timing']
        print(f"\n⏰ MEAL TIMING ADVICE:")
        for key, advice in timing.items():
            print(f"   {key.title()}: {advice}")
        
        # Show model performance metrics if available
        if "model_metrics" in report:
            print(f"\n📊 MODEL PERFORMANCE:")
            for agent_name, metrics in report["model_metrics"].items():
                if metrics.get("total_sessions", 0) > 0:
                    print(f"   {agent_name.replace('-', ' ').title()}:")
                    print(f"     Average Rating: {metrics['average_rating']:.1f}/5.0")
                    print(f"     Total Sessions: {metrics['total_sessions']}")
        
        print("\n" + "="*60)
    
    def get_user_input(self) -> Dict[str, Any]:
        """Interactively collect patient information from user"""
        print("\n" + "="*60)
        print("KENYAN NUTRITION AI - PATIENT INFORMATION COLLECTION")
        print("="*60)
        print("Please provide the following information about the patient:\n")
        
        try:
            # Basic demographics
            age = int(input("Enter patient's age (years): "))
            weight = float(input("Enter patient's weight (kg): "))
            height = float(input("Enter patient's height (meters, e.g., 1.68): "))
            
            # Health metrics
            blood_sugar = float(input("Enter blood sugar level (mg/dL): "))
            
            print("\nBlood pressure readings:")
            systolic = int(input("  Systolic pressure (mmHg): "))
            diastolic = int(input("  Diastolic pressure (mmHg): "))
            blood_pressure = {"systolic": systolic, "diastolic": diastolic}
            
            # Diabetes status
            print("\nDiabetes status options:")
            print("  1. None")
            print("  2. Type 1 Diabetes")
            print("  3. Type 2 Diabetes")
            print("  4. Prediabetes")
            
            diabetes_choice = input("Select diabetes status (1-4): ")
            diabetes_mapping = {
                "1": "none",
                "2": "type1", 
                "3": "type2",
                "4": "prediabetes"
            }
            diabetes_status = diabetes_mapping.get(diabetes_choice, "none")
            
            # Location
            print("\nAvailable regions in Kenya:")
            regions = [
                # Central Kenya
                "Nairobi", "Kiambu", "Murang'a", "Nyeri", "Kirinyaga", "Nyandarua", "Meru", "Tharaka-Nithi",
                
                # Coastal Region
                "Mombasa", "Kilifi", "Kwale", "Lamu", "Tana River", "Taita-Taveta",
                
                # Western Kenya
                "Kisumu", "Kakamega", "Bungoma", "Vihiga", "Siaya", "Busia", "Trans-Nzoia",
                
                # Eastern Kenya
                "Machakos", "Kitui", "Makueni", "Embu", "Isiolo", "Marsabit", "Moyale",
                
                # Northern Kenya
                "Garissa", "Mandera", "Wajir", "Turkana", "West Pokot", "Samburu",
                
                # Nyanza Region
                "Kisii", "Nyamira", "Homa Bay", "Migori", "Kericho", "Bomet",
                
                # Rift Valley
                "Nakuru", "Eldoret", "Narok", "Kajiado", "Laikipia", "Nandi", "Uasin Gishu", "Elgeyo-Marakwet", "Baringo"
            ]
            
            # Show representative locations from different regions
            representative_locations = [
                "Nairobi",      # Central
                "Mombasa",      # Coastal
                "Kisumu",       # Western
                "Machakos",     # Eastern
                "Garissa",      # Northern
                "Kisii",        # Nyanza
                "Nakuru",       # Rift Valley
                "Eldoret"       # Rift Valley (major town)
            ]
            
            print("Common locations (representing different regions):")
            for i, location in enumerate(representative_locations, 1):
                # Add region indicator
                region_indicators = {
                    "Nairobi": "(Central)", "Mombasa": "(Coastal)", "Kisumu": "(Western)",
                    "Machakos": "(Eastern)", "Garissa": "(Northern)", "Kisii": "(Nyanza)",
                    "Nakuru": "(Rift Valley)", "Eldoret": "(Rift Valley)"
                }
                print(f"  {i}. {location} {region_indicators.get(location, '')}")
            print("  9. Other (enter manually)")
            
            location_choice = input("Select location (1-9) or enter location name: ")
            
            if location_choice.isdigit() and 1 <= int(location_choice) <= 8:
                location = representative_locations[int(location_choice) - 1].lower()
            elif location_choice == "9":
                location = input("Enter your location: ").strip().lower()
            else:
                location = location_choice.strip().lower()
            
            # Compile patient data
            patient_data = {
                "age": age,
                "weight": weight,
                "height": height,
                "blood_sugar": blood_sugar,
                "blood_pressure": blood_pressure,
                "diabetes_status": diabetes_status,
                "location": location
            }
            
            # Confirmation
            print(f"\n📋 PATIENT DATA SUMMARY:")
            print(f"   Age: {age} years")
            print(f"   Weight: {weight} kg")
            print(f"   Height: {height} m")
            print(f"   Blood Sugar: {blood_sugar} mg/dL")
            print(f"   Blood Pressure: {systolic}/{diastolic} mmHg")
            print(f"   Diabetes Status: {diabetes_status.replace('_', ' ').title()}")
            print(f"   Location: {location.title()}")
            
            confirm = input("\nIs this information correct? (y/n): ").lower()
            if confirm != 'y':
                print("Please run the program again to re-enter the information.")
                return None
            
            return patient_data
            
        except ValueError as e:
            print(f"❌ Invalid input: Please enter numeric values where required.")
            return None
        except KeyboardInterrupt:
            print(f"\n❌ Input cancelled by user.")
            return None
        except Exception as e:
            print(f"❌ Error collecting input: {str(e)}")
            return None
    
    def run_interactive_session(self):
        """Run an interactive session with user input"""
        print("🏥 KENYAN NUTRITION AI AGENT")
        print("Welcome to your personalized nutrition assistant!")
        
        # Get user input
        patient_data = self.get_user_input()
        
        if patient_data is None:
            print("Session terminated.")
            return
        
        print("\n🔄 Processing your information...")
        print("This may take a moment...")
        
        try:
            # Generate recommendations without feedback collection
            recommendations = self.get_nutrition_recommendations(**patient_data, collect_feedback=False)
            
            # Display results
            self.print_recommendations(recommendations)
            
            # Ask if user wants to save report
            save_report = input("\n💾 Would you like to save the full report to a file? (y/n): ").lower()
            if save_report == 'y':
                filename = f"nutrition_report_{patient_data['location']}_{patient_data['age']}y.json"
                filepath = f"/Users/cynthiakamau/PycharmProjects/nutrition-ai-agent/{filename}"
                
                with open(filepath, 'w') as f:
                    json.dump(recommendations, f, indent=2)
                print(f"✅ Report saved to: {filename}")
            
            print("\n🎉 Thank you for using Kenyan Nutrition AI!")
            print("Stay healthy and follow your personalized recommendations!")
            
        except Exception as e:
            logging.error(f"Error generating recommendations: {str(e)}")
            print(f"❌ Error: {str(e)}")

    def run_interactive_session_with_feedback(self):
        """Run an interactive session with comprehensive feedback collection"""
        print("🏥 KENYAN NUTRITION AI AGENT (ADK Powered)")
        print("Welcome to your AI-powered nutrition assistant!")
        
        # Get user input
        patient_data = self.get_user_input()
        
        if patient_data is None:
            print("Session terminated.")
            return
        
        print("\n🔄 Processing with Google ADK agents...")
        print("This may take a moment...")
        
        try:
            # Generate recommendations with feedback
            recommendations = self.get_nutrition_recommendations(**patient_data, collect_feedback=True)
            
            # Display results
            self.print_recommendations(recommendations)
            
            # Overall session feedback
            print("\n📊 OVERALL SESSION FEEDBACK")
            try:
                overall_rating = int(input("Rate your overall experience (1-5): "))
                overall_comments = input("Any additional feedback: ").strip()
                
                session_feedback = {
                    "session_id": recommendations.get("session_id"),
                    "overall_rating": overall_rating,
                    "overall_comments": overall_comments if overall_comments else None,
                    "patient_data": patient_data
                }
                
                # Save session feedback
                import os
                os.makedirs("session_feedback", exist_ok=True)
                session_id = recommendations.get("session_id", "unknown")
                with open(f"session_feedback/session_{session_id}.json", 'w') as f:
                    json.dump(session_feedback, f, indent=2)
                
            except (ValueError, KeyboardInterrupt):
                print("Feedback collection skipped")
            
            # Ask if user wants to save report
            save_report = input("\n💾 Would you like to save the full report to a file? (y/n): ").lower()
            if save_report == 'y':
                filename = f"adk_nutrition_report_{patient_data['location']}_{patient_data['age']}y.json"
                filepath = f"/Users/cynthiakamau/PycharmProjects/nutrition-ai-agent/{filename}"
                
                with open(filepath, 'w') as f:
                    json.dump(recommendations, f, indent=2)
                print(f"✅ Report saved to: {filename}")
            
            print("\n🎉 Thank you for using Kenyan Nutrition AI!")
            print("Your feedback helps improve our AI recommendations!")
            
        except Exception as e:
            logging.error(f"Error generating recommendations: {str(e)}")
            print(f"❌ Error: {str(e)}")

def main():
    """Main function with ADK agent options"""
    # Initialize the ADK-powered main agent
    nutrition_agent = KenyanNutritionAgent()
    
    print("🏥 KENYAN NUTRITION AI AGENT (Google ADK Powered)")
    print("Choose your preferred mode:")
    print("  1. Interactive mode with feedback (Enter your own details)")
    print("  2. Demo mode (Use sample patient data)")
    print("  3. View model performance metrics")
    
    try:
        mode = input("Select mode (1, 2, or 3): ").strip()
        
        if mode == "1":
            # Interactive mode with feedback
            nutrition_agent.run_interactive_session_with_feedback()
            
        elif mode == "2":
            # Demo mode with sample data
            print("\n🔄 Running ADK demo with sample patient data...")
            
            patient_data = {
                "age": 45,
                "weight": 78.0,
                "height": 1.68,
                "blood_sugar": 135,
                "blood_pressure": {"systolic": 140, "diastolic": 85},
                "diabetes_status": "prediabetes",
                "location": "nairobi"
            }
            
            # Get comprehensive recommendations
            recommendations = nutrition_agent.get_nutrition_recommendations(**patient_data, collect_feedback=False)
            
            # Print formatted recommendations
            nutrition_agent.print_recommendations(recommendations)
            
            # Save demo report
            with open('/Users/cynthiakamau/PycharmProjects/nutrition-ai-agent/adk_nutrition_report_demo.json', 'w') as f:
                json.dump(recommendations, f, indent=2)
            print(f"\n💾 ADK demo report saved to: adk_nutrition_report_demo.json")
            
        elif mode == "3":
            # View performance metrics
            print("\n📊 MODEL PERFORMANCE METRICS:")
            metrics = nutrition_agent._get_model_performance_metrics()
            
            if not any(m.get("total_sessions", 0) > 0 for m in metrics.values()):
                print("No feedback data available yet. Run some sessions first!")
            else:
                for agent_name, agent_metrics in metrics.items():
                    if agent_metrics.get("total_sessions", 0) > 0:
                        print(f"\n{agent_name.replace('-', ' ').title()}:")
                        print(f"  Average Rating: {agent_metrics['average_rating']:.1f}/5.0")
                        print(f"  Total Sessions: {agent_metrics['total_sessions']}")
                        if "rating_distribution" in agent_metrics:
                            print(f"  Rating Distribution: {agent_metrics['rating_distribution']}")
            
        else:
            print("❌ Invalid selection. Please run the program again.")
            
    except KeyboardInterrupt:
        print(f"\n❌ Program cancelled by user.")
    except Exception as e:
        logging.error(f"Error in main: {str(e)}")
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    main()