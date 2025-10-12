"""
Agent 1: Culinary Decomposer (IMPROVED)
Better recipe search and ingredient reasoning
"""

import os
import json
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from tavily import TavilyClient

load_dotenv()

class CulinaryDecomposer:
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4o",
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            temperature=0.1
        )
        self.tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
    
    def analyze_food_complexity(self, food_name):
        """Ask LLM to analyze if decomposition is needed and generate search query"""
        
        prompt = f"""Analyze this food item: "{food_name}"

CRITICAL RULE: A food is SIMPLE only if >90% of its composition is ONE ingredient.

Examples:
- "Pav Bhaji" → COMPLEX (potato + vegetables + butter + tomato = multiple major ingredients)
- "Plain Pav/Bread" → SIMPLE (>90% is bread)
- "Pancakes" → COMPLEX (flour + milk + eggs = multiple major ingredients)
- "Plain Rice" → SIMPLE (>90% is rice)
- "Butter" → SIMPLE (>90% is milk fat)
- "Blueberries" → SIMPLE (100% blueberries)

TASK:
1. Is >90% of this food ONE ingredient?
2. If COMPLEX: Create a search query to find the RECIPE with ingredient quantities

OUTPUT (JSON only):
{{
  "food_name": "{food_name}",
  "is_simple": true/false,
  "reasoning": "Brief explanation",
  "search_query": "food_name recipe ingredients proportions" (only if complex)
}}"""

        response = self.llm.invoke(prompt)
        
        try:
            response_text = response.content
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            json_str = response_text[json_start:json_end]
            return json.loads(json_str)
        except:
            return {"is_simple": True, "reasoning": "Parse error", "search_query": None}
    
    def search_web(self, query):
        """Execute web search for recipes"""
        print(f"🔍 Searching: {query}")
        
        try:
            search_results = self.tavily.search(
                query=query,
                search_depth="advanced",
                max_results=5,
                include_answer=True
            )
            
            content = search_results.get('answer', '')
            for result in search_results.get('results', []):
                content += f"\n\n{result.get('title', '')}\n{result.get('content', '')}"
                
            return content, search_results.get('results', [])
        except Exception as e:
            print(f"❌ Search error: {e}")
            return "", []
    
    def decompose_complex_food(self, food_name, volume_litres, search_content, clarifications):
        """LLM decomposes food with better reasoning"""
        
        clarification_text = ""
        if clarifications:
            clarification_text = f"\n\nUSER CLARIFICATIONS: {json.dumps(clarifications, indent=2)}"
        
        prompt = f"""You are a food scientist analyzing "{food_name}" with total volume {volume_litres} liters.{clarification_text}

RECIPE/WEB DATA:
{search_content if search_content else "No recipe found - use your knowledge"}

YOUR TASK - THINK STEP BY STEP:

STEP 1: IDENTIFY RAW INGREDIENTS FROM RECIPE
Look at the recipe and list what goes INTO making this dish.
Example for Pancakes:
- Flour (dry ingredient, forms structure)
- Milk (liquid, provides moisture)
- Eggs (binding, protein)
- Sugar (sweetening)
- Baking powder (leavening, creates air)
- Butter (fat, richness)

STEP 2: UNDERSTAND COOKING TRANSFORMATIONS
What happens during cooking?
- Does water evaporate? (reduces volume)
- Does it absorb water? (increases volume)
- Does air get incorporated? (increases volume, reduces density)
- Does frying add oil? (increases mass, changes density)

Example for Pancakes:
- Batter gets COOKED → water partially evaporates
- Baking powder creates AIR POCKETS → fluffy texture
- Result: Cooked pancake is lighter than raw batter

STEP 3: ESTIMATE REALISTIC PROPORTIONS IN FINAL COOKED STATE
Based on typical recipes, what % of the FINAL COOKED product is each ingredient?

For Pancakes (after cooking):
- Flour-based structure: ~45% (main bulk after cooking)
- Milk (some evaporated): ~30% (liquid content)
- Eggs (cooked, distributed): ~15% (protein structure)
- Sugar: ~5% (dissolved throughout)
- Baking powder: ~3% (created air, trace amount left)
- Butter: ~2% (fat incorporated)

STEP 4: CALCULATE VOLUMES
Total volume: {volume_litres}L
For each ingredient: volume = (percentage/100) × {volume_litres}

CRITICAL RULES:
1. List ingredients in their FINAL COOKED STATE:
   ✅ "Flour (cooked in pancake batter)"
   ✅ "Milk (incorporated in cooked batter)"
   ❌ Don't say "Cooked Pancake Batter (Flour-based)" - that's confusing!

2. Think about CHEMICAL CHANGES:
   - Fried foods: Add "oil absorbed during frying" as separate ingredient
   - Baked goods: Consider air incorporation
   - Boiled foods: Consider water content

3. Percentages MUST add to 100%

4. Only include ingredients >2% of volume

5. Use REALISTIC proportions based on actual recipes

OUTPUT FORMAT (JSON only):
{{
  "original_food_name": "{food_name}",
  "total_volume_litres": {volume_litres},
  "reasoning": "Explain: (1) What cooking process happened? (2) How did it transform ingredients? (3) Why these proportions?",
  "ingredient_volumes": [
    {{
      "ingredient_name": "Flour (main structure)",
      "percentage": 45,
      "volume_litres": calculated_value,
      "notes": "Forms the bulk of the cooked pancake structure after baking powder creates air pockets"
    }},
    {{
      "ingredient_name": "Milk (moisture content)",
      "percentage": 30,
      "volume_litres": calculated_value,
      "notes": "Provides liquid; some evaporates during cooking"
    }}
  ],
  "modifications_applied": "How user clarifications affected the analysis"
}}

EXAMPLES OF GOOD DECOMPOSITION:

Example 1: Fried Potato
{{
  "reasoning": "Potatoes are sliced and deep fried. Frying causes: (1) Water loss from potato, (2) Oil absorption into potato. Final product is denser than raw potato.",
  "ingredient_volumes": [
    {{"ingredient_name": "Potato (fried, water reduced)", "percentage": 75, "notes": "Main ingredient, water partially evaporated"}},
    {{"ingredient_name": "Absorbed frying oil", "percentage": 20, "notes": "Oil penetrates potato during frying"}},
    {{"ingredient_name": "Salt and seasonings", "percentage": 5, "notes": "External coating"}}
  ]
}}

Example 2: Boiled Rice
{{
  "reasoning": "Raw rice absorbs water during boiling. Rice grains expand 3x. Final product is rice grains + absorbed water.",
  "ingredient_volumes": [
    {{"ingredient_name": "Rice grains (cooked, expanded)", "percentage": 35, "notes": "Original rice after water absorption and expansion"}},
    {{"ingredient_name": "Water (absorbed into rice)", "percentage": 65, "notes": "Water absorbed during boiling, now part of rice structure"}}
  ]
}}

NOW ANALYZE "{food_name}":"""

        print(f"🧠 LLM reasoning about ingredients and cooking process...")
        response = self.llm.invoke(prompt)
        
        try:
            response_text = response.content
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            json_str = response_text[json_start:json_end]
            
            result = json.loads(json_str)
            result['is_basic_ingredient'] = False
            
            # Validate percentages
            total_pct = sum(ing['percentage'] for ing in result['ingredient_volumes'])
            if abs(total_pct - 100) > 1:
                print(f"⚠️  Warning: Percentages sum to {total_pct}%, adjusting...")
                # Normalize percentages
                for ing in result['ingredient_volumes']:
                    ing['percentage'] = (ing['percentage'] / total_pct) * 100
                    ing['volume_litres'] = (ing['percentage'] / 100) * volume_litres
            
            return result
            
        except Exception as e:
            print(f"❌ Error parsing decomposition: {e}")
            print(f"Response: {response.content[:500]}")
            return None
    
    def decompose_food(self, food_name, volume_litres, clarifications=None):
        """Main decomposition logic"""
        
        print(f"🤔 LLM analyzing food complexity...")
        analysis = self.analyze_food_complexity(food_name)
        
        print(f"📊 Analysis: {analysis['reasoning']}")
        
        if analysis.get('is_simple'):
            print(f"✓ SIMPLE ingredient - no decomposition")
            return {
                "original_food_name": food_name,
                "total_volume_litres": volume_litres,
                "is_basic_ingredient": True,
                "reasoning": analysis['reasoning'],
                "ingredient_volumes": [
                    {
                        "ingredient_name": food_name,
                        "percentage": 100,
                        "volume_litres": volume_litres,
                        "notes": "Simple ingredient"
                    }
                ],
                "sources": []
            }
        
        print(f"✓ COMPLEX dish - needs decomposition")
        search_query = analysis.get('search_query', f"{food_name} recipe ingredients proportions")
        search_content, sources = self.search_web(search_query)
        
        if not search_content:
            print(f"⚠️  No search results, using LLM general knowledge")
        
        result = self.decompose_complex_food(food_name, volume_litres, search_content, clarifications)
        
        if result:
            result['sources'] = [s.get('url', '') for s in sources[:3]]
            return result
        
        return None
    
    def process_json_file(self, filepath):
        """Process all food items from JSON"""
        print(f"\n📂 Reading: {filepath}")
        
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        results = []
        
        # Handle both verified_volumes.json and final_confirmed_output.json formats
        if 'verified_volumes' in data:
            # New format from volume_verify.py
            print("✓ Detected verified_volumes.json format")
            verified_items = data.get('verified_volumes', [])
            items = []
            for item in verified_items:
                items.append({
                    'segment_id': item.get('segment_id'),
                    'final_food_name': item.get('food_name'),
                    'volume_litres': item.get('suggested_volume_litres'),  # Use VERIFIED volume!
                    'clarifications': {},
                    'volume_adjusted': item.get('adjustment_made', False),
                    'original_volume': item.get('original_volume_litres'),
                    'verification_confidence': item.get('confidence', 0.0),
                    'verification_reasoning': item.get('reasoning', '')
                })
        elif 'confirmed_results' in data:
            # Old format (fallback compatibility)
            print("✓ Detected final_confirmed_output.json format")
            items = data.get('confirmed_results', [])
        else:
            print("❌ Error: Unrecognized input format")
            return []
        
        print(f"\n🍽️  Processing {len(items)} items...\n")
        
        for idx, item in enumerate(items):
            print(f"\n{'='*70}")
            print(f"Item {idx + 1}/{len(items)}: {item['final_food_name']}")
            
            # Show if volume was adjusted
            if item.get('volume_adjusted'):
                print(f"⚠️  Volume ADJUSTED: {item.get('original_volume', 0):.3f}L → {item['volume_litres']:.3f}L")
                print(f"   Reason: {item.get('verification_reasoning', 'N/A')}")
            else:
                print(f"✓ Volume VERIFIED: {item['volume_litres']:.3f}L")
            
            print(f"{'='*70}")
            
            result = self.decompose_food(
                item['final_food_name'],
                item['volume_litres'],
                item.get('clarifications', {})
            )
            
            if result:
                result['segment_id'] = item['segment_id']
                
                # Add volume verification metadata
                if item.get('volume_adjusted'):
                    result['volume_verification'] = {
                        'was_adjusted': True,
                        'original_volume': item.get('original_volume'),
                        'adjusted_volume': item['volume_litres'],
                        'confidence': item.get('verification_confidence'),
                        'reasoning': item.get('verification_reasoning')
                    }
                
                results.append(result)
                print(f"✅ Complete!\n")
            else:
                print(f"❌ Failed\n")
        
        return results
    
    def save_output(self, results, output_path):
        """Save to JSON"""
        output = {
            "agent": "Agent 1: Culinary Decomposer",
            "decomposed_foods": results
        }
        
        with open(output_path, 'w') as f:
            json.dump(output, f, indent=2)
        
        print(f"\n💾 Saved: {output_path}")


def main():
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python agent1_decomposer.py <input_json>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = "agent1_output.json"
    
    agent = CulinaryDecomposer()
    results = agent.process_json_file(input_file)
    agent.save_output(results, output_file)
    
    print(f"\n{'='*70}")
    print(f"✅ Agent 1 Complete! Processed {len(results)} items")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()