import pandas as pd

def load_food_data(path):
    df = pd.read_csv(path)

    foods = []
    for _, row in df.iterrows():
        foods.append({
            "food": row["Food"],
            "category": row["Food category"],
            "carbs": row["Carbs"],
            "protein": row["Protein"],
            "fat": row["Fat"],
            "fiber": row["Fiber"],
            "gi": row["GI"],
            "region": row["County"],
            "season": row["Seasonal availability"]
        })

    return foods