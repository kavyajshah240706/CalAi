"""
Conversational VLM Agent (FIXED)
Now correctly extracts calorie calculation context
"""

import os
import sys
import json
import base64
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

class ConversationalVLM:
    def __init__(self, session_folder):
        """Initialize conversational VLM with session context"""
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.session_folder = session_folder
        self.conversation_file = f"{session_folder}/conversation_history.json"
        self.calorie_outputs_folder = f"{session_folder}/calorie_outputs"
    
    def load_conversation_history(self):
        """Load conversation history from session"""
        if os.path.exists(self.conversation_file):
            with open(self.conversation_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"messages": []}
    
    def save_conversation_history(self, conversation_history):
        """Save updated conversation history back to file"""
        with open(self.conversation_file, 'w', encoding='utf-8') as f:
            json.dump(conversation_history, f, indent=2, ensure_ascii=False)
    
    def load_calorie_calculations(self):
        """Load all calorie calculation outputs from session"""
        calculations = []
        
        if not os.path.exists(self.calorie_outputs_folder):
            return calculations
        
        files = [f for f in os.listdir(self.calorie_outputs_folder) if f.endswith('.json')]
        
        for filename in files:
            filepath = os.path.join(self.calorie_outputs_folder, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    calculations.append({
                        "file": filename,
                        "data": data
                    })
            except Exception as e:
                continue
        
        return calculations
    
    def encode_image(self, image_path):
        """Encode image to base64 for GPT-4V"""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    
    def build_context_summary(self, conversation_history, calorie_calculations):
        """Build a summary of available context"""
        
        context_parts = []
        
        # Recent conversation (last 10 messages)
        recent_messages = conversation_history.get('messages', [])[-10:]
        if recent_messages:
            conv_summary = "RECENT CONVERSATION:\n"
            for msg in recent_messages:
                role = msg.get('role', 'unknown')
                content = msg.get('content', '')
                timestamp = msg.get('timestamp', '')
                content_preview = content[:300] + "..." if len(content) > 300 else content
                conv_summary += f"{role.upper()} [{timestamp}]: {content_preview}\n"
            context_parts.append(conv_summary)
        
        # FIXED: Better extraction of calorie calculations
        if calorie_calculations:
            calc_summary = "\n=== AVAILABLE CALORIE CALCULATIONS ===\n"
            
            for idx, calc in enumerate(calorie_calculations, 1):
                data = calc.get('data', {})
                filename = calc.get('file', 'Unknown')
                
                calc_summary += f"\n📊 CALCULATION {idx} (from {filename}):\n"
                
                # Handle Agent 3 output structure (nutritional_breakdown_per_segment)
                if 'nutritional_breakdown_per_segment' in data:
                    segments = data.get('nutritional_breakdown_per_segment', [])
                    total_summary = data.get('total_nutrition_summary', {})
                    
                    # Show each food item
                    for seg in segments:
                        food_name = seg.get('food_name', 'Unknown')
                        mass = seg.get('total_mass_grams', 0)
                        nutr = seg.get('calculated_nutrition', {})
                        
                        calc_summary += f"  • {food_name} ({mass}g)\n"
                        calc_summary += f"    - Calories: {nutr.get('calories_kcal', 0):.1f} kcal\n"
                        calc_summary += f"    - Protein: {nutr.get('protein_g', 0):.1f}g\n"
                        calc_summary += f"    - Carbs: {nutr.get('carbohydrates_g', 0):.1f}g\n"
                        calc_summary += f"    - Fat: {nutr.get('fat_g', 0):.1f}g\n"
                    
                    # Show totals
                    if total_summary:
                        calc_summary += f"\n  TOTAL MEAL:\n"
                        calc_summary += f"    - Total Calories: {total_summary.get('total_calories_kcal', 0):.1f} kcal\n"
                        calc_summary += f"    - Total Protein: {total_summary.get('total_protein_g', 0):.1f}g\n"
                        calc_summary += f"    - Total Carbs: {total_summary.get('total_carbohydrates_g', 0):.1f}g\n"
                        calc_summary += f"    - Total Fat: {total_summary.get('total_fat_g', 0):.1f}g\n"
                
                # Handle old format (food_masses from Agent 2)
                elif 'food_masses' in data:
                    for food in data.get('food_masses', []):
                        food_name = food.get('food_name', 'Unknown')
                        mass = food.get('total_mass_grams', 0)
                        calc_summary += f"  • {food_name}: {mass}g\n"
                
                # Generic fallback
                else:
                    calc_summary += f"  • Calculation data available (check file for details)\n"
                
                calc_summary += "\n"
            
            context_parts.append(calc_summary)
        
        final_context = "\n\n".join(context_parts) if context_parts else "No previous context available."
        
        return final_context
    
    def create_system_prompt(self, context_summary):
        """Create system prompt with context"""
        
        return f"""You are an intelligent food and nutrition assistant. You can:
- Answer general food and nutrition questions
- Analyze food images
- Provide meal recommendations
- Compare foods and meals
- Give dietary advice
- Access conversation history and past calorie calculations

CONTEXT AVAILABLE TO YOU:
{context_summary}

INSTRUCTIONS:
1. When user asks about "my meal", "the food I ate", "what I calculated" - refer to the calorie calculations above
2. You have access to DETAILED nutritional breakdowns - use them!
3. If comparing foods, use the exact values from calculations
4. Be specific with numbers when you have them
5. If you see an image, describe it and answer accordingly
6. Always be accurate with nutritional information
7. If you don't have specific data, say so clearly

IMPORTANT: The calorie calculations contain exact values for calories, protein, carbs, and fat. Use these precise numbers in your responses!

Respond naturally and conversationally."""
    
    def chat_with_image(self, user_query, image_path, context_summary):
        """Chat with both text and image"""
        
        # Encode image
        base64_image = self.encode_image(image_path)
        
        messages = [
            {
                "role": "system",
                "content": self.create_system_prompt(context_summary)
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": user_query
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }
        ]
        
        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            max_tokens=1500,
            temperature=0.7
        )
        
        return response.choices[0].message.content
    
    def chat_text_only(self, user_query, context_summary):
        """Chat with text only"""
        
        messages = [
            {
                "role": "system",
                "content": self.create_system_prompt(context_summary)
            },
            {
                "role": "user",
                "content": user_query
            }
        ]
        
        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            max_tokens=1500,
            temperature=0.7
        )
        
        return response.choices[0].message.content
    
    def process(self, user_query, image_path=None):
        """Main processing logic"""
        
        # Load context
        conversation_history = self.load_conversation_history()
        calorie_calculations = self.load_calorie_calculations()
        
        # Build context summary
        context_summary = self.build_context_summary(conversation_history, calorie_calculations)
        
        # Generate response
        if image_path and os.path.exists(image_path):
            response = self.chat_with_image(user_query, image_path, context_summary)
        else:
            response = self.chat_text_only(user_query, context_summary)
        
        # Save this interaction to conversation history
        conversation_history['messages'].append({
            "role": "user",
            "content": user_query,
            "timestamp": datetime.now().isoformat(),
            "had_image": bool(image_path)
        })
        
        conversation_history['messages'].append({
            "role": "assistant",
            "content": response,
            "timestamp": datetime.now().isoformat(),
            "agent": "CONVERSATIONAL_VLM"
        })
        
        self.save_conversation_history(conversation_history)
        
        return response


def main():
    """Main entry point"""
    
    if len(sys.argv) < 2:
        print("Usage: python conversational_vlm.py <query> [image_path] --session <session_folder>")
        print("\nExamples:")
        print('  python conversational_vlm.py "What should I eat?" --session ./session_001')
        print('  python conversational_vlm.py "Is this healthy?" food.jpg --session ./session_001')
        sys.exit(1)
    
    # Parse arguments
    user_query = sys.argv[1]
    image_path = None
    session_folder = None
    
    # Find --session argument
    if '--session' in sys.argv:
        session_idx = sys.argv.index('--session')
        if session_idx + 1 < len(sys.argv):
            session_folder = sys.argv[session_idx + 1]
    
    # Check if there's an image path (between query and --session)
    if len(sys.argv) > 2 and sys.argv[2] != '--session':
        potential_image = sys.argv[2]
        if os.path.exists(potential_image):
            image_path = potential_image
    
    if not session_folder:
        print("❌ Error: --session <folder> is required")
        sys.exit(1)
    
    if not os.path.exists(session_folder):
        print(f"⚠️ Warning: Session folder doesn't exist, creating: {session_folder}")
        os.makedirs(session_folder, exist_ok=True)
    
    # Initialize VLM
    vlm = ConversationalVLM(session_folder)
    
    # Process request
    try:
        response = vlm.process(user_query, image_path)
        
        # Print response (router will capture this)
        print(response)
        
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()