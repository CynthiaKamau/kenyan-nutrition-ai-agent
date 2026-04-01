from typing import Dict, Any, TypedDict, List, Optional
import logging
import json
import os
from pathlib import Path
from copy import deepcopy
from sub_agents.patient_profiles.agent import PatientProfileAgent
from sub_agents.regions_for_food.agent import RegionalFoodAgent
from sub_agents.food_recommendations.agent import FoodRecommendationAgent

try:
    from langgraph.graph import StateGraph, END
except Exception:
    StateGraph = None
    END = None

try:
    from langchain_openai import ChatOpenAI
except Exception:
    ChatOpenAI = None


class RecommendationGraphState(TypedDict, total=False):
    patient_input: Dict[str, Any]
    patient_profile: Dict[str, Any]
    regional_foods: Dict[str, Any]
    recommendations: Dict[str, Any]
    evaluation: Dict[str, Any]
    summary: Dict[str, Any]
    iterations: int
    max_iterations: int
    target_score: float
    use_llm_evaluator: bool
    religion: str
    dietary_restrictions: Dict[str, bool]
    trace: List[Dict[str, Any]]

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

class KenyanNutritionAgent:
    """Main agent that coordinates all sub-agents for comprehensive nutrition recommendations"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Initialize sub-agents
        self.patient_agent = PatientProfileAgent()
        self.regional_agent = RegionalFoodAgent()
        self.recommendation_agent = FoodRecommendationAgent()
        self._llm = None
        self._recommendation_graph = self._build_recommendation_graph()
        
        self.logger.info("Kenyan Nutrition Agent initialized successfully")

    def _build_recommendation_graph(self):
        """Build a LangGraph workflow for iterative recommendation + evaluation."""
        if StateGraph is None or END is None:
            self.logger.warning("LangGraph not available; graph-based workflow will use fallback path.")
            return None

        graph_builder = StateGraph(RecommendationGraphState)
        graph_builder.add_node("build_profile", self._graph_build_profile)
        graph_builder.add_node("fetch_regional_foods", self._graph_fetch_regional_foods)
        graph_builder.add_node("generate_recommendations", self._graph_generate_recommendations)
        graph_builder.add_node("evaluate_recommendations", self._graph_evaluate_recommendations)
        graph_builder.add_node("improve_recommendations", self._graph_improve_recommendations)

        graph_builder.set_entry_point("build_profile")
        graph_builder.add_edge("build_profile", "fetch_regional_foods")
        graph_builder.add_edge("fetch_regional_foods", "generate_recommendations")
        graph_builder.add_edge("generate_recommendations", "evaluate_recommendations")
        graph_builder.add_conditional_edges(
            "evaluate_recommendations",
            self._graph_route_after_evaluate,
            {
                "improve": "improve_recommendations",
                "end": END,
            },
        )
        graph_builder.add_edge("improve_recommendations", "evaluate_recommendations")

        return graph_builder.compile()

    def _graph_build_profile(self, state: RecommendationGraphState) -> Dict[str, Any]:
        patient_input = state["patient_input"]
        patient_profile = self.patient_agent.create_patient_profile(
            age=patient_input["age"],
            weight=patient_input["weight"],
            height=patient_input["height"],
            blood_sugar=patient_input["blood_sugar"],
            blood_pressure=patient_input["blood_pressure"],
            diabetes_status=patient_input["diabetes_status"],
            location=patient_input["location"],
            religion=patient_input.get("religion"),
            dietary_restrictions=patient_input.get("dietary_restrictions"),
        )
        return {
            "patient_profile": patient_profile,
            "trace": state.get("trace", []) + [{"step": "build_profile", "health_category": patient_profile["health_category"]}],
        }

    def _graph_fetch_regional_foods(self, state: RecommendationGraphState) -> Dict[str, Any]:
        location = state["patient_input"]["location"]
        regional_foods = self.regional_agent.data_loader.get_regional_foods(location)
        available_foods_count = sum(len(foods) for foods in regional_foods.values())
        return {
            "regional_foods": regional_foods,
            "trace": state.get("trace", []) + [{"step": "fetch_regional_foods", "available_foods": available_foods_count}],
        }

    def _graph_generate_recommendations(self, state: RecommendationGraphState) -> Dict[str, Any]:
        recommendations = self.recommendation_agent.generate_recommendations(
            state["patient_profile"],
            state.get("regional_foods", {}),
        )
        return {
            "recommendations": recommendations,
            "trace": state.get("trace", []) + [{"step": "generate_recommendations"}],
        }

    def _graph_evaluate_recommendations(self, state: RecommendationGraphState) -> Dict[str, Any]:
        if state.get("use_llm_evaluator", False):
            evaluation = self._evaluate_recommendations_with_llm(
                profile=state["patient_profile"],
                recommendations=state["recommendations"],
            )
        else:
            evaluation = self._evaluate_recommendations_heuristic(
                profile=state["patient_profile"],
                recommendations=state["recommendations"],
            )

        return {
            "evaluation": evaluation,
            "trace": state.get("trace", []) + [{"step": "evaluate_recommendations", "score": evaluation["score"], "method": evaluation["method"]}],
        }

    def _graph_improve_recommendations(self, state: RecommendationGraphState) -> Dict[str, Any]:
        improved_recommendations = self._improve_recommendations(
            profile=state["patient_profile"],
            regional_foods=state["regional_foods"],
            recommendations=state["recommendations"],
            evaluation=state["evaluation"],
        )
        iterations = state.get("iterations", 0) + 1
        return {
            "recommendations": improved_recommendations,
            "iterations": iterations,
            "trace": state.get("trace", []) + [{"step": "improve_recommendations", "iteration": iterations}],
        }

    def _graph_route_after_evaluate(self, state: RecommendationGraphState) -> str:
        score = state.get("evaluation", {}).get("score", 0.0)
        target_score = state.get("target_score", 0.8)
        iterations = state.get("iterations", 0)
        max_iterations = state.get("max_iterations", 2)

        if score >= target_score or iterations >= max_iterations:
            return "end"
        return "improve"

    def _get_low_gi_foods(self, foods: List[str]) -> List[str]:
        low_gi_foods = []
        for food in foods:
            nutrition = self.regional_agent.get_nutritional_info(food)
            if nutrition.get("gi", 50) < 55:
                low_gi_foods.append(food)
        return low_gi_foods

    def _evaluate_recommendations_heuristic(self, profile: Dict[str, Any], recommendations: Dict[str, Any]) -> Dict[str, Any]:
        score = 1.0
        issues = []
        restrictions = profile.get("dietary_restrictions", {})
        meal_plan = recommendations.get("meal_plan", {})

        def flatten_meal_foods(section: Dict[str, Any]) -> List[str]:
            flattened = []
            for foods in section.values():
                if isinstance(foods, list):
                    flattened.extend(foods)
            return flattened

        breakfast_foods = flatten_meal_foods(meal_plan.get("breakfast", {}))
        lunch_foods = flatten_meal_foods(meal_plan.get("lunch", {}))
        dinner_foods = flatten_meal_foods(meal_plan.get("dinner", {}))
        snack_foods = flatten_meal_foods(meal_plan.get("snacks", {}))
        all_meal_foods = breakfast_foods + lunch_foods + dinner_foods + snack_foods

        if restrictions.get("limit_sugar", False):
            high_gi_found = []
            for food in all_meal_foods:
                nutrition = self.regional_agent.get_nutritional_info(food)
                if nutrition.get("gi", 50) >= 55:
                    high_gi_found.append(food)
            if high_gi_found:
                score -= 0.35
                issues.append(f"high_gi_meal_plan: {', '.join(sorted(set(high_gi_found)))}")

        preferred_foods = recommendations.get("preferred_foods", {})
        if not preferred_foods.get("lean_proteins"):
            score -= 0.2
            issues.append("missing_lean_proteins")

        portion_guidelines = recommendations.get("portion_guidelines", {})
        if restrictions.get("portion_control", False):
            if not all(str(value).lower().startswith(("small", "moderate")) for value in portion_guidelines.values()):
                score -= 0.15
                issues.append("portion_control_not_reflected")

        final_score = max(0.0, min(1.0, round(score, 3)))
        return {
            "score": final_score,
            "passes": final_score >= 0.8,
            "issues": issues,
            "method": "heuristic",
        }

    def _evaluate_recommendations_with_llm(self, profile: Dict[str, Any], recommendations: Dict[str, Any]) -> Dict[str, Any]:
        if ChatOpenAI is None:
            self.logger.warning("langchain_openai not available. Falling back to heuristic evaluator.")
            return self._evaluate_recommendations_heuristic(profile, recommendations)

        if not os.getenv("OPENAI_API_KEY"):
            self.logger.warning("OPENAI_API_KEY not set. Falling back to heuristic evaluator.")
            return self._evaluate_recommendations_heuristic(profile, recommendations)

        try:
            if self._llm is None:
                self._llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

            prompt = (
                "You are a strict nutrition recommendation evaluator. "
                "Evaluate quality for diabetes/portion-control safety and practical meal diversity. "
                "Respond with strict JSON only in this format: "
                "{\"score\": <0.0-1.0>, \"passes\": <true/false>, \"issues\": [<strings>]}.\n\n"
                f"Patient profile: {json.dumps(profile)}\n"
                f"Recommendations: {json.dumps(recommendations)}"
            )
            response = self._llm.invoke(prompt)
            content = response.content if isinstance(response.content, str) else json.dumps(response.content)

            start_index = content.find("{")
            end_index = content.rfind("}")
            json_content = content[start_index:end_index + 1] if start_index != -1 and end_index != -1 else content
            parsed = json.loads(json_content)

            score = float(parsed.get("score", 0.0))
            issues = parsed.get("issues", [])
            passes = bool(parsed.get("passes", score >= 0.8))

            return {
                "score": max(0.0, min(1.0, round(score, 3))),
                "passes": passes,
                "issues": issues if isinstance(issues, list) else [str(issues)],
                "method": "llm",
            }
        except Exception as error:
            self.logger.warning(f"LLM evaluation failed ({error}). Falling back to heuristic evaluator.")
            return self._evaluate_recommendations_heuristic(profile, recommendations)

    def _improve_recommendations(
        self,
        profile: Dict[str, Any],
        regional_foods: Dict[str, List[str]],
        recommendations: Dict[str, Any],
        evaluation: Dict[str, Any],
    ) -> Dict[str, Any]:
        improved = deepcopy(recommendations)
        issues = [str(item) for item in evaluation.get("issues", [])]
        meal_plan = improved.get("meal_plan", {})
        restrictions = profile.get("dietary_restrictions", {})

        if restrictions.get("limit_sugar", False) and any("high_gi" in issue for issue in issues):
            breakfast = meal_plan.get("breakfast", {})
            lunch = meal_plan.get("lunch", {})
            dinner = meal_plan.get("dinner", {})
            snacks = meal_plan.get("snacks", {})

            low_gi_grains = self._get_low_gi_foods(regional_foods.get("grains", []))
            low_gi_fruits = self._get_low_gi_foods(regional_foods.get("fruits", []))

            if low_gi_grains:
                breakfast["grains"] = low_gi_grains[:2]
                lunch["grains"] = low_gi_grains[:1]
                dinner["grains"] = low_gi_grains[:1]
            if low_gi_fruits:
                breakfast["fruits"] = low_gi_fruits[:2]
                snacks["fruits"] = low_gi_fruits[:2]

        if any("missing_lean_proteins" in issue for issue in issues):
            lean_candidates = [protein for protein in regional_foods.get("proteins", []) if protein in ["fish", "chicken", "eggs"]]
            if lean_candidates:
                improved.setdefault("preferred_foods", {})["lean_proteins"] = lean_candidates[:2]

        if restrictions.get("portion_control", False) and any("portion_control" in issue for issue in issues):
            adjusted_portions = {}
            for category, guideline in improved.get("portion_guidelines", {}).items():
                lower = str(guideline).lower()
                if not lower.startswith("small") and not lower.startswith("moderate"):
                    adjusted_portions[category] = f"Moderate {guideline}"
                else:
                    adjusted_portions[category] = guideline
            improved["portion_guidelines"] = adjusted_portions

        return improved

    def get_nutrition_recommendations_graph(
        self,
        age: int,
        weight: float,
        height: float,
        blood_sugar: float,
        blood_pressure: Dict[str, int],
        diabetes_status: str,
        location: str,
        religion: Optional[str] = None,
        dietary_restrictions: Optional[Dict[str, bool]] = None,
        use_llm_evaluator: bool = False,
        max_iterations: int = 2,
        target_score: float = 0.8,
    ) -> Dict[str, Any]:
        """Get recommendations via LangGraph with evaluate-improve loop and fallback support."""
        patient_input = {
            "age": age,
            "weight": weight,
            "height": height,
            "blood_sugar": blood_sugar,
            "blood_pressure": blood_pressure,
            "diabetes_status": diabetes_status,
            "location": location,
            "religion": religion,
            "dietary_restrictions": dietary_restrictions,
        }

        if self._recommendation_graph is None:
            self.logger.info("Graph workflow unavailable. Using deterministic workflow fallback.")
            base_report = self.get_nutrition_recommendations(**patient_input)
            evaluation = self._evaluate_recommendations_heuristic(
                profile=base_report["patient_profile"],
                recommendations=base_report["recommendations"],
            )
            base_report["evaluation"] = evaluation
            base_report["graph_metadata"] = {
                "graph_enabled": False,
                "iterations": 0,
                "target_score": target_score,
                "max_iterations": max_iterations,
                "evaluator": "heuristic",
                "trace": [{"step": "fallback_workflow"}],
            }
            return base_report

        final_state = self._recommendation_graph.invoke(
            {
                "patient_input": patient_input,
                "iterations": 0,
                "max_iterations": max_iterations,
                "target_score": target_score,
                "use_llm_evaluator": use_llm_evaluator,
                "trace": [],
            }
        )

        patient_profile = final_state["patient_profile"]
        recommendations = final_state["recommendations"]

        return {
            "patient_profile": patient_profile,
            "regional_foods": final_state["regional_foods"],
            "recommendations": recommendations,
            "summary": self._generate_summary(patient_profile, recommendations),
            "evaluation": final_state.get("evaluation", {}),
            "graph_metadata": {
                "graph_enabled": True,
                "iterations": final_state.get("iterations", 0),
                "target_score": target_score,
                "max_iterations": max_iterations,
                "evaluator": final_state.get("evaluation", {}).get("method", "heuristic"),
                "trace": final_state.get("trace", []),
            },
        }
    
    def get_nutrition_recommendations(self, 
                                    age: int,
                                    weight: float,
                                    height: float,
                                    blood_sugar: float,
                                    blood_pressure: Dict[str, int],
                                    diabetes_status: str,
                                    location: str,
                                    religion: Optional[str] = None,
                                    dietary_restrictions: Optional[Dict[str, bool]] = None) -> Dict[str, Any]:
        """
        Complete workflow to get personalized nutrition recommendations
        
        Args:
            age: Patient age in years
            weight: Patient weight in kg
            height: Patient height in meters
            blood_sugar: Blood sugar level in mg/dL
            blood_pressure: Dict with 'systolic' and 'diastolic' values
            diabetes_status: 'none', 'type1', 'type2', or 'prediabetes'
            location: Patient's geographical location in Kenya
            religion: Optional religion/cultural context to keep in profile metadata
            dietary_restrictions: Optional overrides for computed restrictions
        
        Returns:
            Complete nutrition recommendation report
        """
        
        self.logger.info("Starting nutrition recommendation workflow")
        
        # Step 1: Create patient profile using PatientProfileAgent
        self.logger.info("Step 1: Creating patient profile...")
        patient_profile = self.patient_agent.create_patient_profile(
            age=age,
            weight=weight,
            height=height,
            blood_sugar=blood_sugar,
            blood_pressure=blood_pressure,
            diabetes_status=diabetes_status,
            location=location,
            religion=religion,
            dietary_restrictions=dietary_restrictions,
        )
        self.logger.info(f"Patient profile created - Health category: {patient_profile['health_category']}")
        
        # Step 2: Get regional foods using data loader
        self.logger.info("Step 2: Identifying regional foods...")
        regional_foods = self.regional_agent.data_loader.get_regional_foods(location)
        available_foods_count = sum(len(foods) for foods in regional_foods.values())
        self.logger.info(f"Found {available_foods_count} foods available in {location} region")
        
        # Step 3: Generate recommendations using FoodRecommendationAgent
        self.logger.info("Step 3: Generating personalized food recommendations...")
        recommendations = self.recommendation_agent.generate_recommendations(
            patient_profile,
            regional_foods,
        )
        self.logger.info("Food recommendations generated successfully")
        
        # Compile complete report
        complete_report = {
            "patient_profile": patient_profile,
            "regional_foods": regional_foods,
            "recommendations": recommendations,
            "summary": self._generate_summary(patient_profile, recommendations)
        }
        
        self.logger.info("Nutrition recommendation workflow completed")
        return complete_report
    
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
        """Print a formatted version of the recommendations"""
        print("\n" + "="*60)
        print("KENYAN NUTRITION AI - PERSONALIZED RECOMMENDATIONS")
        print("="*60)
        
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

            print("\nReligion options:")
            religions = [
                "christianity",
                "islam",
                "hinduism",
                "buddhism",
                "judaism",
                "polytheism",
            ]
            for i, value in enumerate(religions, 1):
                print(f"  {i}. {value.title()}")
            print("  7. Prefer not to say")

            religion_choice = input("Select religion (1-7): ").strip()
            if religion_choice.isdigit() and 1 <= int(religion_choice) <= 6:
                religion = religions[int(religion_choice) - 1]
            else:
                religion = None

            custom_restrictions = None
            use_custom_restrictions = input("Set custom dietary restrictions? (y/n): ").strip().lower()
            if use_custom_restrictions == "y":
                custom_restrictions = {
                    "limit_sugar": input("  Limit sugar? (y/n): ").strip().lower() == "y",
                    "portion_control": input("  Portion control? (y/n): ").strip().lower() == "y",
                    "limit_sodium": input("  Limit sodium? (y/n): ").strip().lower() == "y",
                    "increase_fiber": input("  Increase fiber? (y/n): ").strip().lower() == "y",
                    "limit_saturated_fat": input("  Limit saturated fat? (y/n): ").strip().lower() == "y",
                }
            
            # Compile patient data
            patient_data = {
                "age": age,
                "weight": weight,
                "height": height,
                "blood_sugar": blood_sugar,
                "blood_pressure": blood_pressure,
                "diabetes_status": diabetes_status,
                "location": location,
                "religion": religion,
                "dietary_restrictions": custom_restrictions,
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
            print(f"   Religion: {(religion or 'Not specified').title()}")
            print(f"   Dietary Restriction Override: {'Yes' if custom_restrictions else 'No'}")
            
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
            # Generate recommendations
            recommendations = self.get_nutrition_recommendations(**patient_data)
            
            # Display results
            self.print_recommendations(recommendations)
            
            # Ask if user wants to save report
            save_report = input("\n💾 Would you like to save the full report to a file? (y/n): ").lower()
            if save_report == 'y':
                filename = f"nutrition_report_{patient_data['location']}_{patient_data['age']}y.json"
                output_dir = Path.cwd() / "outputs"
                output_dir.mkdir(parents=True, exist_ok=True)
                filepath = output_dir / filename
                
                with open(filepath, 'w') as f:
                    json.dump(recommendations, f, indent=2)
                print(f"✅ Report saved to: {filepath}")
            
            print("\n🎉 Thank you for using Kenyan Nutrition AI!")
            print("Stay healthy and follow your personalized recommendations!")
            
        except Exception as e:
            logging.error(f"Error generating recommendations: {str(e)}")
            print(f"❌ Error: {str(e)}")

def main():
    """Main function with options for demo or interactive mode"""
    # Initialize the main agent
    nutrition_agent = KenyanNutritionAgent()
    
    print("🏥 KENYAN NUTRITION AI AGENT")
    print("Choose your preferred mode:")
    print("  1. Interactive mode (Enter your own details)")
    print("  2. Demo mode (Use sample patient data)")
    
    try:
        mode = input("Select mode (1 or 2): ").strip()
        
        if mode == "1":
            # Interactive mode
            nutrition_agent.run_interactive_session()
            
        elif mode == "2":
            # Demo mode with sample data
            print("\n🔄 Running demo with sample patient data...")
            
            # Sample patient data
            patient_data = {
                "age": 45,
                "weight": 78.0,  # kg
                "height": 1.68,  # meters
                "blood_sugar": 135,  # mg/dL
                "blood_pressure": {"systolic": 140, "diastolic": 85},
                "diabetes_status": "prediabetes",
                "location": "nairobi"
            }
            
            # Get comprehensive recommendations
            recommendations = nutrition_agent.get_nutrition_recommendations(**patient_data)
            
            # Print formatted recommendations
            nutrition_agent.print_recommendations(recommendations)
            
            # Save demo report
            output_dir = Path.cwd() / "outputs"
            output_dir.mkdir(parents=True, exist_ok=True)
            demo_report_path = output_dir / "nutrition_report_demo.json"
            with open(demo_report_path, 'w') as f:
                json.dump(recommendations, f, indent=2)
            print(f"\n💾 Demo report saved to: {demo_report_path}")
            
        else:
            print("❌ Invalid selection. Please run the program again.")
            
    except KeyboardInterrupt:
        print(f"\n❌ Program cancelled by user.")
    except Exception as e:
        logging.error(f"Error in main: {str(e)}")
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    main()
