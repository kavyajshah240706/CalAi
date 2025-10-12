"""
Agent 3: Nutritional Profiler (v2 with Query Generation)
Calculates final nutritional information based on mass from Agent 2.
- NEW: Uses an LLM to generate a simplified search query from a complex food name.
- Web searches for nutritional data of the entire dish.
- Intelligently handles serving sizes.
- Scales nutrition based on the calculated mass.
"""

import os
import json
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from tavily import TavilyClient
from datetime import datetime

load_dotenv()

class NutritionProfiler:
    def __init__(self):
        """Initialize Agent 3"""
        self.llm = ChatOpenAI(
            model="gpt-4o",
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            temperature=0.0
        )
        self.tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
        print("✅ Agent 3: Nutritional Profiler (v2) is ready.\n")

    def _generate_search_query(self, complex_food_name: str) -> str:
        """
        Uses an LLM to simplify a detailed food name into a concise, searchable term.
        """
        print(f"  🧠 Generating simplified query for: '{complex_food_name}'")
        prompt = f"""
You are a search query generator. Your task is to simplify a detailed food name into a concise, searchable term for finding nutritional information.
Remove specific preparations, brand names, additions, or descriptions. Keep the core dish name.

Here are some examples:
- Input: "Pav Bhaji with Generous Butter (50g Added)" -> Output: "Pav Bhaji"
- Input: "Butter-Enriched Pav (Dinner Roll) with 5-10 Grams of Butter" -> Output: "Pav (Dinner Roll)"
- Input: "chopped raw cut onions (no dressing)" -> Output: "raw onions"
- Input: "Plain Steamed Rice (No Oil)" -> Output: "Steamed White Rice"
- Input: "Dal (Lentil Soup)" -> Output: "Dal"

Now, simplify this food name: "{complex_food_name}"

OUTPUT (JSON only with a single key "simple_name"):
{{
  "simple_name": "your_simplified_name_here"
}}
"""
        try:
            response = self.llm.invoke(prompt)
            response_text = response.content.strip()
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            json_str = response_text[json_start:json_end]
            result = json.loads(json_str)
            simple_name = result.get("simple_name", complex_food_name)
            print(f"  ✅ Simplified query: '{simple_name}'")
            return simple_name
        except Exception as e:
            print(f"  ⚠️ Query generation failed for '{complex_food_name}', using original name. Error: {e}")
            return complex_food_name

    def search_nutrition_on_web(self, food_name: str):
        """
        Web searches for nutritional info using a generated query and uses an LLM to extract it.
        """
        # Step 1: Generate a better search query
        simple_query = self._generate_search_query(food_name)

        print(f"  🌐 Web searching for: '{simple_query}'")
        query = f"nutritional information for '{simple_query}' calories protein fat carbohydrates per 100g or per serving size"
        
        try:
            search_results = self.tavily.search(
                query=query, search_depth="basic", max_results=5, include_answer=True
            )
            
            content = search_results.get('answer', '')
            for result in search_results.get('results', []):
                content += f"\n---\nSource: {result.get('url')}\nContent: {result.get('content', '')}"
            
            if not content.strip():
                print(f"  ❌ No web results found for '{simple_query}'")
                return None
            
            prompt = f"""
You are an expert nutritional data analyst. From the provided web search results for "{simple_query}", extract the nutritional information.

SEARCH RESULTS:
{content}

CRITICAL INSTRUCTIONS:
1.  **DO NOT USE INGREDIENTS:** Analyze the nutritional information for the complete dish "{simple_query}", not its individual ingredients.
2.  **IDENTIFY SERVING SIZE:** This is your most important task. First, find the serving size (e.g., "100g", "1 cup", "250g serving").
3.  **CONVERT SERVING SIZE TO GRAMS:** If the serving size is not in grams (e.g., "1 cup"), you MUST find a gram equivalent in the text (e.g., "1 cup is approximately 245g"). If no conversion is available, you must make a reasonable estimation and state it in the reasoning.
4.  **EXTRACT NUTRITION FOR THAT SERVING SIZE:** Extract calories (kcal), protein (g), fat (g), and carbohydrates (g) for the exact serving size you identified.
5.  **HANDLE RANGES:** If a range is given (e.g., 20-25g protein), use the average value.
6.  **URL:** Provide the best source URL you used.

OUTPUT (JSON only, no other text):
{{
  "found": true/false,
  "serving_size_grams": <numeric_value_in_grams>,
  "calories_kcal": <numeric_value>,
  "protein_g": <numeric_value>,
  "fat_g": <numeric_value>,
  "carbohydrates_g": <numeric_value>,
  "source_url": "<best_source_url>",
  "reasoning": "Briefly explain how you determined the serving size and extracted the values."
}}

If no reliable data can be found, return {{"found": false}}.
"""
            response = self.llm.invoke(prompt)
            response_text = response.content.strip()
            
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            json_str = response_text[json_start:json_end]
            result = json.loads(json_str)

            if result.get("found"):
                print(f"  ✅ Found on web: {result['calories_kcal']} kcal per {result['serving_size_grams']}g")
                return result
            else:
                print(f"  ❌ Could not find reliable nutritional data for '{simple_query}'")
                return None

        except Exception as e:
            print(f"  ❌ Web search or extraction error for '{simple_query}': {e}")
            return None

    def process_agent2_output(self, agent2_output_path: str):
        """
        Loads the output from Agent 2 and processes each food item.
        """
        print(f"📁 Reading Agent 2 output: {agent2_output_path}\n")
        with open(agent2_output_path, 'r') as f:
            data = json.load(f)

        food_masses = data.get('food_masses', [])
        processed_segments = []

        for food_item in food_masses:
            food_name = food_item.get('food_name', 'Unknown')
            total_mass = food_item.get('total_mass_grams', 0)
            segment_id = food_item.get('segment_id')

            print(f"\n{'='*70}")
            print(f"Processing Segment {segment_id}: {food_name} ({total_mass}g)")
            print(f"{'='*70}")

            nutrition_per_serving = self.search_nutrition_on_web(food_name)
            
            final_nutrition = {"calories_kcal": 0, "protein_g": 0, "fat_g": 0, "carbohydrates_g": 0}

            if nutrition_per_serving and nutrition_per_serving.get("serving_size_grams") > 0:
                serving_size = nutrition_per_serving["serving_size_grams"]
                scaling_factor = total_mass / serving_size
                
                for key in final_nutrition:
                    # Handle cases where a nutrient might not be found (e.g., 'protein_g')
                    base_value = nutrition_per_serving.get(key, 0)
                    if base_value is not None:
                        final_nutrition[key] = round(base_value * scaling_factor, 2)
                
                print(f"  ⚖️ Scaled Nutrition: {final_nutrition}")
            else:
                print(f"  ⚠️ Could not calculate nutrition for this segment.")

            processed_segments.append({
                "segment_id": segment_id,
                "food_name": food_name,
                "total_mass_grams": total_mass,
                "calculated_nutrition": final_nutrition,
                "source_data": nutrition_per_serving
            })

        return processed_segments

    def calculate_totals(self, processed_segments):
        """Calculates the sum of nutritional information from all segments."""
        total_nutrition = {"total_calories_kcal": 0, "total_protein_g": 0, "total_fat_g": 0, "total_carbohydrates_g": 0}
        for segment in processed_segments:
            for key, value in segment['calculated_nutrition'].items():
                total_key = f"total_{key}"
                if total_key in total_nutrition and value is not None:
                    total_nutrition[total_key] += value
        
        for key in total_nutrition:
            total_nutrition[key] = round(total_nutrition[key], 2)
            
        return total_nutrition

    def save_output(self, segments, totals, output_path, session_folder=None):
        """Saves the final results to a JSON file."""
        
        output = {
            "agent": "Agent 3: Nutritional Profiler",
            "nutritional_breakdown_per_segment": segments,
            "total_nutrition_summary": totals
        }
        
        # ALWAYS save to root (backward compatibility)
        with open(output_path, 'w') as f:
            json.dump(output, f, indent=2)
        print(f"\n💾 Saved final nutritional analysis to: {output_path}")
        
        # ALSO save to session folder if provided
        if session_folder:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            session_path = f"{session_folder}/calorie_outputs/calc_{timestamp}.json"
            os.makedirs(f"{session_folder}/calorie_outputs", exist_ok=True)
            
            with open(session_path, 'w') as f:
                json.dump(output, f, indent=2)
            print(f"💾 ALSO saved to session: {session_path}")

def main():
    import sys
    if len(sys.argv) < 2:
        print("Usage: python agent3_nutritioncalculator.py <agent2_output.json> [session_folder]")
        sys.exit(1)

    agent2_output_file = sys.argv[1]
    session_folder = sys.argv[2] if len(sys.argv) > 2 else None

    output_file = "agent3_output.json"

    agent = NutritionProfiler()
    processed_results = agent.process_agent2_output(agent2_output_file)
    total_summary = agent.calculate_totals(processed_results)
    agent.save_output(processed_results, total_summary, output_file, session_folder=session_folder)

    print(f"\n{'='*70}")
    print("✅ Agent 3 Complete! Final nutritional analysis is ready.")
    print(f"Total Summary: {total_summary}")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()