# Kenyan Nutrition AI Agent

An intelligent nutrition recommendation system that provides personalized dietary advice based on patient health profiles and regional food availability in Kenya. The system features a multi-agent architecture for comprehensive patient profiling, regional food mapping, and tailored meal planning for diabetes management and general wellness.

## 🌟 Features

- **Patient Health Profiling**: Comprehensive analysis of age, weight, BMI, blood sugar levels, blood pressure, and diabetes status
- **Regional Food Mapping**: Database of foods available across different Kenyan regions (Central, Coastal, Western, Northern, Eastern)
- **Personalized Meal Planning**: Custom meal plans based on health conditions and local food availability
- **Diabetes Management**: Specialized recommendations for Type 1, Type 2, and pre-diabetes patients
- **Interactive Interface**: User-friendly command-line interface for data input
- **Comprehensive Reports**: Detailed nutrition reports with meal timing, portion guidelines, and dietary restrictions

## 🏗️ Architecture

The system uses a multi-agent architecture with three specialized agents:

1. **Patient Profiles Agent** (`sub_agents/patient_profiles/`): Analyzes patient health data and categorizes risk levels
2. **Regional Food Agent** (`sub_agents/regions_for_food/`): Maps regional food availability across Kenya
3. **Food Recommendations Agent** (`sub_agents/food_recommendations/`): Generates personalized meal plans and dietary advice

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
   git clone https://github.com/yourusername/kenyan-nutrition-ai-agent.git
   cd kenyan-nutrition-ai-agent
   ```

2. **Create a virtual environment** (recommended)

   ```bash
   python -m venv nutrition_env
   source nutrition_env/bin/activate  # On Windows: nutrition_env\Scripts\activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

   _Note: If requirements.txt doesn't exist, the project currently uses only Python standard libraries._

## 💻 Usage

### Interactive Mode (Recommended)

Run the main agent and follow the interactive prompts:

```bash
cd kenyan-nutrition-agent
python agent.py
```

Select option `1` for interactive mode and provide:

- Patient's age, weight, and height
- Blood sugar levels and blood pressure readings
- Diabetes status
- Geographical location in Kenya

### Demo Mode

Select option `2` to see the system in action with sample patient data:

```bash
python agent.py
# Choose option 2 for demo mode
```

### Example Usage

```python
from kenyan_nutrition_agent.agent import KenyanNutritionAgent

# Initialize the agent
agent = KenyanNutritionAgent()

# Get recommendations for a patient
recommendations = agent.get_nutrition_recommendations(
    age=45,
    weight=78.0,
    height=1.68,
    blood_sugar=135,
    blood_pressure={"systolic": 140, "diastolic": 85},
    diabetes_status="prediabetes",
    location="nairobi"
)

# Print formatted recommendations
agent.print_recommendations(recommendations)
```

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
kenyan-nutrition-agent/
├── agent.py                          # Main coordination agent
├── sub_agents/
│   ├── patient_profiles/
│   │   ├── __init__.py
│   │   └── agent.py                  # Patient profiling logic
│   ├── regions_for_food/
│   │   ├── __init__.py
│   │   └── agent.py                  # Regional food mapping
│   └── food_recommendations/
│       ├── __init__.py
│       └── agent.py                  # Recommendation engine
├── README.md
├── .gitignore
└── requirements.txt                  # (if needed)
```

## 🔧 Configuration

The system includes built-in configurations for:

- **Nutritional Database**: Caloric and nutritional information for common Kenyan foods
- **Regional Mapping**: Food availability across different Kenyan regions
- **Health Thresholds**: BMI categories, blood pressure ranges, diabetes classifications
- **Portion Guidelines**: Age and health-adjusted serving sizes

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

For support, please open an issue on GitHub or contact [your-email@example.com](mailto:your-email@example.com).

## 🙏 Acknowledgments

- Kenyan Ministry of Health for nutritional guidelines
- Regional food availability data sources
- Open source Python community
- Healthcare professionals who provided guidance
