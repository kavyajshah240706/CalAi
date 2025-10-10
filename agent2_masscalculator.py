"""
Agent 2: Mass & Density Analyst
Calculates total mass using: PDF RAG → Ingredient search → Web search → Estimation
FIXED: Uses OpenAI embeddings instead of Gemini
"""

import os
import json
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from tavily import TavilyClient

load_dotenv()

class MassCalculator:
    def __init__(self, pdf_path):
        """Initialize Agent 2 with PDF RAG database"""
        # Changed to OpenAI
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",  # or "gpt-4o"
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            temperature=0.1
        )
        self.tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
        
        print(f"📚 Loading PDF database: {pdf_path}")
        self.vectorstore = self._load_pdf_database(pdf_path)
        print(f"✅ PDF database ready!\n")
    
    def _load_pdf_database(self, pdf_path):
        """Load PDF and create RAG vector database"""
        # Load PDF
        loader = PyPDFLoader(pdf_path)
        documents = loader.load()
        
        # Split into chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        chunks = text_splitter.split_documents(documents)
        
        # Changed to OpenAI embeddings
        embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small",  # or "text-embedding-3-large"
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )
        vectorstore = FAISS.from_documents(chunks, embeddings)
        
        return vectorstore
    
    def search_density_in_pdf(self, ingredient_name):
        """Search for density in PDF using RAG"""
        print(f"  📖 Searching PDF for: {ingredient_name}")
        
        # Retrieve relevant chunks
        docs = self.vectorstore.similarity_search(ingredient_name, k=5)
        context = "\n\n".join([doc.page_content for doc in docs])
        
        if not context.strip():
            print(f"  ❌ No relevant content found in PDF")
            return None
        
        # Ask LLM to extract density from PDF content
        prompt = f"""Extract the density of "{ingredient_name}" from this PDF content.

PDF CONTENT:
{context}

CRITICAL RULES FOR MATCHING:
1. Look for EXACT matches first: If searching "bread", accept "bread density"
2. Accept SIMILAR items with same chemical properties:
   - "pav" = "bread" = "dinner roll" (all baked leavened dough)
   - "boiled potato" = "cooked potato" = "steamed potato" (all gelatinized starch)
   - "fried onion" = "sautéed onion" (both cooked, similar)
   
3. REJECT items with different chemical properties:
   - "chips" ≠ "potato" (fried vs raw - vastly different densities)
   - "fried potato" ≠ "boiled potato" (oil absorption changes density)
   - "mashed potato" can approximate "boiled potato" (similar density)

4. If multiple similar matches found, choose the closest one

TASK: Find density in kg/L or g/mL for "{ingredient_name}"

OUTPUT (JSON only):
{{
  "found": true/false,
  "density_kg_per_L": numeric_value or null,
  "matched_item": "what item in PDF was matched",
  "reasoning": "why this match is acceptable"
}}

If not found or no acceptable match, return: {{"found": false}}"""

        response = self.llm.invoke(prompt)
        
        try:
            response_text = response.content
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            json_str = response_text[json_start:json_end]
            result = json.loads(json_str)
            
            if result.get('found'):
                density = result['density_kg_per_L']
                
                # SANITY CHECK
                if density > 2.0 or density < 0.05:
                    print(f"  ⚠️ Unrealistic density {density} kg/L from PDF - likely error")
                    return None
                
                print(f"  ✅ Found in PDF: {density} kg/L (matched: {result['matched_item']})")
                return density
            else:
                print(f"  ❌ Not found in PDF")
                return None
        except:
            print(f"  ❌ PDF search failed")
            return None
    
    def search_density_on_web(self, ingredient_name):
        """Search for density on web"""
        print(f"  🌐 Web searching: {ingredient_name}")
        
        query = f"density of {ingredient_name} in kg/L or g/mL"
        
        try:
            search_results = self.tavily.search(
                query=query,
                search_depth="basic",
                max_results=3,
                include_answer=True
            )
            
            content = search_results.get('answer', '')
            for result in search_results.get('results', []):
                content += f"\n{result.get('content', '')}"
            
            if not content.strip():
                print(f"  ❌ No web results")
                return None
            
            # Ask LLM to extract density
            prompt = f"""Extract density of "{ingredient_name}" from web search results.

SEARCH RESULTS:
{content}

RULES:
1. Extract density value in kg/L
2. If given in g/mL, convert: 1 g/mL = 1 kg/L
3. If given in g/cm³, convert: 1 g/cm³ = 1 kg/L
4. If range given (e.g., 0.9-1.1), use middle value

OUTPUT (JSON only):
{{
  "found": true/false,
  "density_kg_per_L": numeric_value,
  "reasoning": "brief note on extraction"
}}

If not found: {{"found": false}}"""

            response = self.llm.invoke(prompt)
            
            response_text = response.content
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            json_str = response_text[json_start:json_end]
            result = json.loads(json_str)
            
            if result.get('found'):
                density = result['density_kg_per_L']
                
                # SANITY CHECK: Catch unrealistic densities
                if density > 2.0 or density < 0.05:
                    print(f"  ⚠️ Unrealistic density {density} kg/L - likely conversion error")
                    print(f"  🔄 Falling back to estimation")
                    return None
                
                print(f"  ✅ Found on web: {density} kg/L (from: {result.get('original_value', 'N/A')})")
                return density
            else:
                print(f"  ❌ Not found on web")
                return None
        except Exception as e:
            print(f"  ❌ Web search error: {e}")
            return None
    
    def estimate_density(self, ingredient_name):
        """LLM estimates density based on reasoning"""
        print(f"  🧠 LLM estimating density...")
        
        prompt = f"""Estimate the density of "{ingredient_name}" in kg/L using your knowledge.

REALISTIC DENSITY GUIDELINES:
- Water, broths, thin liquids: 0.98-1.05 kg/L
- Milk, dairy liquids: 1.03-1.05 kg/L
- Most vegetables (raw): 0.5-0.9 kg/L
- Most vegetables (cooked/boiled): 0.9-1.1 kg/L
- Leafy vegetables (raw): 0.1-0.3 kg/L
- Fruits (fresh): 0.5-1.1 kg/L (berries ~0.6-0.8, dense fruits ~0.9-1.1)
- Bread/pav/buns (airy): 0.25-0.4 kg/L
- Cooked rice: 0.7-0.8 kg/L
- Cooked lentils/dal: 0.9-1.1 kg/L
- Flour (loose): 0.5-0.6 kg/L
- Eggs (whole): 1.03-1.05 kg/L
- Sugar: 0.8-0.9 kg/L (granulated)
- Butter/ghee: 0.91-0.93 kg/L
- Oils (cooking): 0.88-0.92 kg/L
- Baking powder: 0.8-1.0 kg/L
- Fried foods: Similar to base + 10-15% less (oil reduces density slightly)

CRITICAL RULES:
1. Most food densities are between 0.2 and 1.5 kg/L
2. If ingredient has "cooked/boiled/steamed" → higher water content → closer to 1.0
3. If "fried" → lower than boiled version
4. If "airy/fluffy/bread" → much lower (0.3-0.5)
5. Think about: texture, water content, air pockets

YOUR TASK:
Analyze "{ingredient_name}" and estimate realistic density.

OUTPUT (JSON only):
{{
  "estimated_density_kg_per_L": numeric_value (between 0.1-1.5 for most foods),
  "confidence": "low/medium/high",
  "reasoning": "Explain: What is the base ingredient? Cooking method? Water/air content? Why this density?"
}}"""

        response = self.llm.invoke(prompt)
        
        try:
            response_text = response.content
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            json_str = response_text[json_start:json_end]
            result = json.loads(json_str)
            
            density = result['estimated_density_kg_per_L']
            print(f"  💭 Estimated: {density} kg/L (confidence: {result['confidence']})")
            return density, result
        except:
            print(f"  ❌ Estimation failed, using default 1.0 kg/L")
            return 1.0, {"confidence": "low", "reasoning": "Default fallback"}
    
    def get_density_with_fallback(self, ingredient_name, volume_litres):
        """
        Waterfall approach: PDF → Web → Estimate
        Returns: (density, mass, method, details)
        """
        print(f"\n🔍 Finding density for: {ingredient_name} ({volume_litres}L)")
        
        # Step 1: Try PDF
        density = self.search_density_in_pdf(ingredient_name)
        if density:
            mass = volume_litres * density * 1000  # Convert to grams
            return density, mass, "PDF_RAG", {"source": "PDF database"}
        
        # Step 2: Try Web
        density = self.search_density_on_web(ingredient_name)
        if density:
            mass = volume_litres * density * 1000
            return density, mass, "WEB_SEARCH", {"source": "Web search"}
        
        # Step 3: Estimate
        density, estimate_info = self.estimate_density(ingredient_name)
        mass = volume_litres * density * 1000
        return density, mass, "LLM_ESTIMATE", estimate_info
    
    def calculate_mass_for_food(self, food_item):
        """Calculate total mass for one food item"""
        
        food_name = food_item['original_food_name']
        is_basic = food_item.get('is_basic_ingredient', False)
        
        print(f"\n{'='*70}")
        print(f"Processing: {food_name}")
        print(f"Type: {'BASIC' if is_basic else 'COMPLEX'}")
        print(f"{'='*70}")
        
        ingredient_masses = []
        
        for ing in food_item['ingredient_volumes']:
            ing_name = ing['ingredient_name']
            volume = ing['volume_litres']
            
            # Get density and calculate mass
            density, mass, method, details = self.get_density_with_fallback(ing_name, volume)
            
            ingredient_masses.append({
                "ingredient_name": ing_name,
                "volume_litres": volume,
                "density_kg_per_L": density,
                "mass_grams": round(mass, 2),
                "method": method,
                "details": details
            })
        
        # Calculate total mass
        total_mass = sum(item['mass_grams'] for item in ingredient_masses)
        
        result = {
            "food_name": food_name,
            "segment_id": food_item.get('segment_id'),
            "is_basic_ingredient": is_basic,
            "total_mass_grams": round(total_mass, 2),
            "ingredient_masses": ingredient_masses
        }
        
        print(f"\n✅ Total Mass: {total_mass:.2f} grams")
        
        return result
    
    def process_agent1_output(self, agent1_output_path):
        """Process all foods from Agent 1 output"""
        
        print(f"📁 Reading Agent 1 output: {agent1_output_path}\n")
        
        with open(agent1_output_path, 'r') as f:
            data = json.load(f)
        
        foods = data.get('decomposed_foods', [])
        results = []
        
        for food in foods:
            result = self.calculate_mass_for_food(food)
            results.append(result)
        
        return results
    
    def save_output(self, results, output_path):
        """Save results to JSON"""
        output = {
            "agent": "Agent 2: Mass & Density Analyst",
            "food_masses": results
        }
        
        with open(output_path, 'w') as f:
            json.dump(output, f, indent=2)
        
        print(f"\n💾 Saved: {output_path}")


def main():
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python agent2_mass_calculator.py <pdf_database> <agent1_output.json>")
        print("Example: python agent2_mass_calculator.py food_density.pdf agent1_output.json")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    agent1_output = sys.argv[2]
    output_file = "agent2_output.json"
    
    # Initialize Agent 2
    agent = MassCalculator(pdf_path)
    
    # Process foods
    results = agent.process_agent1_output(agent1_output)
    
    # Save output
    agent.save_output(results, output_file)
    
    print(f"\n{'='*70}")
    print(f"✅ Agent 2 Complete! Processed {len(results)} items")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()