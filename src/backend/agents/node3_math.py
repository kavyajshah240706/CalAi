from src.backend.agents.schema import GraphState

def node3_math_engine(state: GraphState) -> GraphState:
    """
    Node 3: Deterministic Math Engine (Strictly Python)
    Calculates total grams and scales all macronutrients linearly.
    """
    if not state.parsed_query or not state.profile:
        return state
        
    vol_conv = {
        "liter": 1000.0, 
        "l": 1000.0,
        "ml": 1.0, 
        "cup": 236.59, 
        "tbsp": 14.79, 
        "tsp": 4.93,
        "piece": 1.0, # Handled differently if weight based, but fallback
        "gram": 1.0,
        "g": 1.0
    }
    
    pq = state.parsed_query
    prof = state.profile
    
    unit_lower = pq["unit"].lower()
    
    # 1. Calculate mass in grams
    if unit_lower in ["gram", "g"]:
        mass_g = float(pq["quantity"])
    else:
        # Volume to ML -> to Grams
        total_ml = float(pq["quantity"]) * vol_conv.get(unit_lower, 1.0)
        mass_g = total_ml * float(prof.get("density_g_ml", 1.0))
        
    multiplier = mass_g / 100.0
    
    # 2. Scale Calories and Nutrient Decomposition
    state.calculated_nutrition = {
        "food": pq["food_name"],
        "weight_g": round(mass_g, 1),
        "calories": round(float(prof.get("kcal_per_100g", 0)) * multiplier, 0),
        "protein": round(float(prof.get("protein_per_100g", 0)) * multiplier, 1),
        "carbs": round(float(prof.get("carbs_per_100g", 0)) * multiplier, 1),
        "fats": round(float(prof.get("fats_per_100g", 0)) * multiplier, 1),
        "source": prof.get("source", "Database")
    }
    
    return state
