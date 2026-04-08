# Kenyan Nutrition AI Agent

An intelligent nutrition recommendation system for Kenyan meal planning with a layered architecture: data layer, recommendation generation layer, multi-agent decision engine, and custom local-model evaluation. The system provides personalized dietary guidance using patient health profiles and regional food availability.

## Quick Start

1. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Train the local evaluator model:

   ```bash
   python models/fine_tuned/train_local_evaluator.py \
     --dataset kenya_food_dataset.json \
     --output models/fine_tuned/local_evaluator.joblib \
     --max-meals-per-group 200
   ```

3. Run stricter grouped accuracy testing:

   ```bash
   python evaluation/local_model_report.py \
     --dataset kenya_food_dataset.json \
     --model-path models/fine_tuned/local_evaluator.joblib \
     --max-meals-per-group 200 \
     --split-strategy group
   ```

4. Start the app:

   ```bash
   python agent.py
   ```

## 🌟 Features

- **Patient Health Profiling**: Comprehensive analysis of age, weight, BMI, blood sugar levels, blood pressure, and diabetes status
- **Dynamic Regional Food Mapping**: Real-time food availability lookup across 47+ Kenyan counties from Excel dataset
- **Personalized Meal Planning**: Custom meal plans based on health conditions and local food availability
- **Diabetes Management**: Specialized recommendations for Type 1, Type 2, and pre-diabetes patients
- **Multi-Agent Decision Engine**: Specialized diabetes, portion, diversity, and cultural agents with weighted aggregation
- **Custom Model Evaluation**: Local fine-tuned evaluator supported out-of-the-box (default mode)
- **Evaluation-Improve Loop**: LangGraph-based iterative refinement with explicit evaluation traces
- **Interactive Interface**: User-friendly command-line interface for data input and demo mode
- **Structured Religion Input**: Predefined religion options in interactive mode (Christianity, Islam, Hinduism, Buddhism, Judaism, Polytheism)
- **Optional Dietary Override Input**: Keep automatic restrictions or provide manual restriction overrides when needed
- **Comprehensive Reports**: Detailed nutrition reports with meal timing, portion guidelines, evaluation score, and issues

## 🏗️ Architecture

The system uses a **layered multi-agent architecture**:

### Generation Layer

1. **Patient Profiles Agent** (`agents/patient_profile_agent.py`): Analyzes patient health data and categorizes risk levels
2. **Regional Food Agent** (`agents/regional_food_agent.py`): Maps regional food availability by looking up live data from Excel
3. **Food Recommendations Agent** (`agents/food_recommendation_agent.py`): Generates personalized meal plans and dietary advice

### Evaluation Layer

1. **Diabetes Agent** (`agents/diabetes_agent.py`): GI/carbohydrate safety analysis
2. **Portion Agent** (`agents/portion_agent.py`): Portion-control checks
3. **Diversity Agent** (`agents/diversity_agent.py`): Meal diversity scoring
4. **Cultural Agent** (`agents/cultural_agent.py`): Cultural/religion-aware checks
5. **Aggregator** (`agents/aggregator.py`): Weighted score fusion

### Decision Engine

- `decision_engine/constraints.py`: Rule constants (GI/carb/fiber thresholds)
- `decision_engine/rules.py`: Reusable scoring helpers
- `decision_engine/scorer.py`: Diabetes scoring function

### Recommendation Paths

- **`get_nutrition_recommendations()`**: Deterministic generation pipeline with optional model evaluation output
  - Profile → Regional Foods → Recommendations → Evaluation (optional)
- **`get_nutrition_recommendations_graph()`**: LangGraph-based evaluation-improve loop (quality-focused)
  - Profile → Regional Foods → Recommendations → **Evaluate** → **Improve** → Re-evaluate
  - Custom-model-only evaluation mode supported
  - Iterates until target score achieved or max iterations reached
  - Returns evaluation score, improvement trace, and iteration count

### How `agent.py` and `agents` Work Together

- **`agent.py`** is the orchestrator. It coordinates profile creation, food lookup, recommendation generation, evaluation, and iterative improvement.
- **`agents/`** now contains both layers:
  - **Recommendation-building modules**: `patient_profile_agent.py`, `regional_food_agent.py`, `food_recommendation_agent.py`
  - **Evaluation modules**: `diabetes_agent.py`, `portion_agent.py`, `diversity_agent.py`, `cultural_agent.py`
  - **Fusion module**: `aggregator.py` for weighted score aggregation
- **`models/inference.py`** evaluates the final recommendation using the trained local model artifact (`.joblib`).

### Tech Stack

- **Python 3.10+**: Main runtime language
- **LangGraph**: Evaluate-improve workflow orchestration
- **Scikit-learn**: Local evaluator training, hyperparameter tuning, and inference
- **Joblib**: Model artifact persistence (`.joblib`)
- **Pandas + OpenPyXL**: Dataset ingestion and Excel-backed food data processing
- **Rule-based Decision Engine**: Domain constraints and scoring in `decision_engine/`

## 📋 Health Parameters Supported

- **Demographics**: Age, weight, height, BMI calculation
- **Blood Metrics**: Blood sugar levels, systolic/diastolic blood pressure
- **Diabetes Status**: None, Type 1, Type 2, Pre-diabetes
- **Geographical Location**: Major Kenyan counties and regions
- **Risk Assessment**: Low, moderate, and high-risk categorization

## 🌍 Kenyan Regions Covered

### Central Region

- Counties: Nairobi, Kiambu, Murang'a, Nyeri, Kirinyaga, Nyandarua, Meru, Tharaka-Nithi
- Foods: Maize, wheat, barley, kale, spinach, cabbage, carrots, potatoes, beans, chicken, milk, avocados, tree tomatoes, macadamia

### Coastal Region

- Counties: Mombasa, Kilifi, Kwale, Lamu, Tana River, Taita-Taveta
- Foods: Rice, cassava, coconut, fish, seafood, prawns, mangoes, jackfruit, baobab fruit, cashew fruit, tamarind

### Western Region

- Counties: Kisumu, Kakamega, Bungoma, Vihiga, Siaya, Busia, Trans-Nzoia
- Foods: Millet, sorghum, finger millet, fish, tilapia, pineapples, sugarcane, groundnuts, soya beans

### Northern Region

- Counties: Garissa, Mandera, Wajir, Turkana, West Pokot, Samburu
- Foods: Sorghum, pearl millet, dates, goat meat, camel meat, camel milk, doum palm, watermelon

### Eastern Region

- Counties: Machakos, Kitui, Makueni, Embu, Isiolo, Marsabit, Moyale
- Foods: Maize, millet, sweet potatoes, cassava, watermelon, baobab fruit, cowpeas, green grams

### Nyanza Region

- Counties: Kisii, Nyamira, Homa Bay, Migori, Kericho, Bomet
- Foods: Maize, finger millet, rice, fish, tilapia, spider plant, nightshade, sugarcane, bananas

### Rift Valley Region

- Counties: Nakuru, Eldoret, Narok, Kajiado, Laikipia, Nandi, Uasin Gishu, Elgeyo-Marakwet, Baringo
- Foods: Wheat, barley, oats, beef, lamb, dairy products, irish potatoes, apples, strawberries

_Total Coverage: 47+ counties across 7 major regions with over 70 different food varieties_

## 🚀 Installation

### Prerequisites

- Python 3.7 or higher
- pip (Python package installer)

### Setup

1. **Clone the repository**

   ```bash
   git clone https://github.com/CynthiaKamau/kenyan-nutrition-ai-agent
   cd kenyan-nutrition-ai-agent
   ```

2. **Create a virtual environment** (recommended)

   ```bash
   python -m venv nutrition_env
   source nutrition_env/bin/activate  # On Windows: nutrition_env\Scripts\activate
   ```

3. **Install dependencies**

   ```bash
   pip install langgraph openpyxl pandas scikit-learn joblib
   ```

   Or install all at once:

   ```bash
   pip install -r requirements.txt
   ```

## 💻 Usage

### Train Your Local Evaluator Model (Recommended)

```bash
/home/cynthia/Work/kenyan-nutrition-ai-agent/.venv/bin/python models/fine_tuned/train_local_evaluator.py \
   --dataset kenya_food_dataset.json \
   --output models/fine_tuned/local_evaluator.joblib \
   --max-meals-per-group 200
```

This produces `models/fine_tuned/local_evaluator.joblib`.

By default, the app now uses this local model (`CUSTOM_EVALUATOR_MODEL=local`).

### Interactive Mode (Recommended)

Run the main agent and follow the interactive prompts:

```bash
cd kenyan-nutrition-ai-agent
python agent.py
```

Select option `1` for interactive mode and provide:

- Patient's age, weight, and height
- Blood sugar levels and blood pressure readings
- Diabetes status
- Geographical location in Kenya
- Religion from a predefined list (or prefer not to say)
- Optional manual dietary restriction overrides

### Demo Mode

Select option `2` to see the system in action with sample patient data:

```bash
python agent.py
# Choose option 2 for demo mode
```

### Example: Graph-Based Evaluation

```python
from agent import KenyanNutritionAgent

agent = KenyanNutritionAgent()

# High-quality recommendations with evaluation feedback
result = agent.get_nutrition_recommendations_graph(
    age=45,
    weight=78.0,
    height=1.68,
    blood_sugar=135,
    blood_pressure={"systolic": 140, "diastolic": 85},
    diabetes_status="prediabetes",
    location="nairobi",
    religion="christianity",  # optional
    dietary_restrictions={      # optional overrides
      "limit_sugar": True,
      "portion_control": True,
      "limit_sodium": True,
      "increase_fiber": True,
      "limit_saturated_fat": True,
   },
   use_llm_evaluator=True,   # Enables strict custom-model evaluation
    max_iterations=3,
    target_score=0.8  # Quality threshold
)

print(f"Evaluation Score: {result['evaluation']['score']}")  # e.g., 0.85
print(f"Iterations: {result['graph_metadata']['iterations']}")  # Number of improvement cycles
print(f"Evaluator: {result['graph_metadata']['evaluator']}")
print(f"Trace: {result['graph_metadata']['trace']}")  # Full iteration history

# Access improved recommendations
print(f"Recommendations: {result['recommendations']}")
```

### Model Accuracy Testing and Improvement

Use these commands after training to test model quality:

```bash
# Tuned training (randomized search + CV)
python models/fine_tuned/train_local_evaluator.py \
   --dataset kenya_food_dataset.json \
   --output models/fine_tuned/local_evaluator.joblib \
   --max-meals-per-group 200 \
   --enable-search --cv-folds 5 --search-iterations 20

# Random split report (baseline)
python evaluation/local_model_report.py \
   --dataset kenya_food_dataset.json \
   --model-path models/fine_tuned/local_evaluator.joblib \
   --max-meals-per-group 200 \
   --split-strategy random

# Group split report (stricter, lower leakage risk)
python evaluation/local_model_report.py \
   --dataset kenya_food_dataset.json \
   --model-path models/fine_tuned/local_evaluator.joblib \
   --max-meals-per-group 200 \
   --split-strategy group --importance-top-k 8
```

The report includes:

- MAE, RMSE, R2 metrics
- score-distribution comparison (actual vs predicted)
- worst-prediction examples
- permutation feature importance (top contributing features)

## 📊 Sample Output

```
============================================================
KENYAN NUTRITION AI - PERSONALIZED RECOMMENDATIONS
============================================================

📊 PATIENT PROFILE:
   Age: 45 years
   BMI: 27.64 kg/m²
   Location: Nairobi
   Health Status: High Risk
   Daily Calorie Needs: 2495 kcal

🎯 HEALTH OVERVIEW:
   Patient is high_risk with Overweight BMI (27.64) and prediabetes diabetes status
   Key Focus: Blood Sugar Control, Portion Management, Sodium Reduction, Fiber Intake

🍽️ DAILY MEAL PLAN:

   BREAKFAST:
     Grains: wheat, barley
     Proteins: eggs
     Fruits: oranges, mangoes

   LUNCH:
     Grains: maize
     Proteins: chicken
     Vegetables: kale, spinach, cabbage
     Legumes: beans
```

## 📁 Project Structure

```
kenyan-nutrition-ai-agent/
├── agent.py                               # Main orchestration layer
├── commands.py                            # Quick command reference
├── data_loader.py                         # Excel data ingestion & region mapping
├── kenya_food_dataset.json                # JSON food dataset
├── kenya_food_dataset_with_aez_subcounty.xlsx
├── agents/
│   ├── __init__.py                       # Unified package exports for agent modules
│   ├── patient_profile_agent.py           # Patient profiling logic
│   ├── regional_food_agent.py             # Regional food availability + nutrition lookup
│   ├── food_recommendation_agent.py       # Personalized recommendation generation
│   ├── diabetes_agent.py                  # Diabetes safety evaluator
│   ├── portion_agent.py                   # Portion evaluator
│   ├── diversity_agent.py                 # Diversity evaluator
│   ├── cultural_agent.py                  # Cultural evaluator
│   └── aggregator.py                      # Weighted score fusion
├── decision_engine/
│   ├── constraints.py                     # Rule thresholds
│   ├── rules.py                           # Rule helpers
│   └── scorer.py                          # Diabetes scoring function
├── models/
│   ├── inference.py                       # Custom model inference wrapper
│   └── fine_tuned/
│       ├── features.py                    # Feature engineering for local model
│       ├── train_local_evaluator.py       # Local model trainer
│       └── local_evaluator.joblib         # Trained artifact (generated)
├── pipelines/
│   ├── data_transform.py
│   └── dataset_builder.py                 # Training sample generation
├── evaluation/
│   ├── metrics.py                         # Consistency/rule/diversity metrics
│   └── local_model_report.py              # Local model accuracy diagnostics
├── README.md
├── .gitignore
└── requirements.txt
```

## 🔧 Configuration

The system includes:

- **Live Nutritional Database**: Excel-based food data with calories, macros, fiber, and GI values
- **Regional Mapping**: County-to-region lookup with fallback to central region
- **Health Thresholds**: BMI categories, blood pressure ranges, diabetes classifications
- **Evaluation Rules**: Decision-engine constraints and scoring logic
- **Local Custom Model** (default): `models/fine_tuned/local_evaluator.joblib`

### Local Model Selection

Default behavior (no env var required):

```bash
export CUSTOM_EVALUATOR_MODEL=local
```

Explicit artifact path:

```bash
export CUSTOM_EVALUATOR_MODEL=local:models/fine_tuned/local_evaluator.joblib
```

Alternative explicit variable:

```bash
export CUSTOM_EVALUATOR_LOCAL_MODEL_PATH=models/fine_tuned/local_evaluator.joblib
```

### Evaluation Mode

The system is local-model only. Keep `use_llm_evaluator=True` in graph mode to run strict custom-model evaluation:

```python
agent.get_nutrition_recommendations_graph(
   ...,
   use_llm_evaluator=True
)
```

## 📈 Health Risk Assessment

The system categorizes patients into risk levels:

- **Low Risk**: Normal BMI, good blood pressure, no diabetes
- **Moderate Risk**: 1-2 risk factors (overweight, elevated BP, pre-diabetes)
- **High Risk**: 3+ risk factors (obesity, hypertension, diabetes)

## 🍎 Dietary Recommendations

### For Diabetes Management

- Low glycemic index foods
- High fiber options
- Portion control guidelines
- Meal timing advice

### For Weight Management

- Calorie-controlled portions
- Lean protein emphasis
- Vegetable-heavy meals

### For Hypertension

- Low sodium options
- Heart-healthy foods
- Balanced meal planning

## 📝 Generated Reports

The system generates comprehensive JSON reports containing:

- Complete patient profile
- Regional food availability
- Personalized meal plans
- Dietary restrictions and preferences
- Portion guidelines and meal timing

Reports are saved as: `nutrition_report_[location]_[age]y.json`

By default reports are written to the local `outputs/` directory in the project root:

- Interactive mode: `outputs/nutrition_report_[location]_[age]y.json`
- Demo mode: `outputs/nutrition_report_demo.json`

## 🧪 Troubleshooting

- If evaluation fails at runtime, confirm the model artifact exists at `models/fine_tuned/local_evaluator.joblib`.
- If you retrain to a different path, set `CUSTOM_EVALUATOR_MODEL=local:<path-to-joblib>`.
- If metrics are unrealistically perfect, prefer grouped split testing (`--split-strategy group`) and expand data variety.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Areas for Contribution

- Additional Kenyan regions and local foods
- Seasonal food availability
- Integration with external nutrition APIs
- Mobile/web interface development
- Multi-language support (Swahili, local languages)

## 📋 Roadmap

- [ ] Web-based interface
- [ ] Mobile application
- [ ] Integration with wearable devices
- [ ] Seasonal food recommendations
- [ ] Recipe suggestions
- [ ] Healthcare provider dashboard
- [ ] Multi-language support
- [ ] Database integration for patient records

## ⚠️ Important Notes

- This system provides nutritional guidance and should not replace professional medical advice
- Always consult healthcare providers for serious health conditions
- Regional food data is based on general availability and may vary by specific location and season
- Blood sugar and blood pressure readings should be taken by qualified personnel

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Support

For support, please open an issue on GitHub or contact [cynthiakamau54@gmail.com](mailto:cynthiakamau54@gmail.com).

## 🙏 Acknowledgments

- Kenyan Ministry of Health for nutritional guidelines
- Regional food availability data sources
- Open source Python community
- Healthcare professionals who provided guidance
