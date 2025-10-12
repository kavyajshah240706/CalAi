"""
Router Agent - Intelligent Workflow Orchestrator
Decides which agent to call based on user input
Usage: python router_agent.py "user query" [image_path]
"""

import os
import sys
import json
import subprocess
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

class RouterAgent:
    def __init__(self, session_folder):
        """Initialize router with OpenAI and session storage"""
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.session_folder = session_folder
        
        # Create session folder structure
        os.makedirs(session_folder, exist_ok=True)
        os.makedirs(f"{session_folder}/calorie_outputs", exist_ok=True)
        os.makedirs(f"{session_folder}/conversations", exist_ok=True)
        
        self.conversation_file = f"{session_folder}/conversation_history.json"
        self._init_conversation_history()
    
    def _init_conversation_history(self):
        """Initialize or load conversation history"""
        if not os.path.exists(self.conversation_file):
            with open(self.conversation_file, 'w') as f:
                json.dump({
                    "session_id": os.path.basename(self.session_folder),
                    "started_at": datetime.now().isoformat(),
                    "messages": []
                }, f, indent=2)
    
    def _load_conversation_history(self):
        """Load conversation history"""
        with open(self.conversation_file, 'r') as f:
            return json.load(f)
    
    def _save_message(self, role, content, metadata=None):
        """Save message to conversation history"""
        history = self._load_conversation_history()
        
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        }
        
        if metadata:
            message["metadata"] = metadata
        
        history["messages"].append(message)
        
        with open(self.conversation_file, 'w') as f:
            json.dump(history, f, indent=2)
    
    def decide_workflow(self, user_query, has_image):
        """Use GPT-4 to decide which agent to call"""
        
        # Get conversation context
        history = self._load_conversation_history()
        recent_messages = history["messages"][-5:]  # Last 5 messages for context
        
        context_str = "\n".join([
            f"{msg['role']}: {msg['content']}" 
            for msg in recent_messages
        ])
        
        decision_prompt = f"""You are a router agent for a food calorie estimation app. Analyze the user's query and decide which agent to call.

AVAILABLE AGENTS:
1. CALORIE_MODEL - Full 3-agent pipeline that calculates nutritional information from food images
   - Requires: Image (mandatory)
   - Returns: Complete nutrition breakdown (calories, protein, carbs, fat, ingredient masses)
   - Use when: User wants calorie/nutrition calculation

2. CONVERSATIONAL_VLM - Multimodal conversational AI for general food queries
   - Requires: Query (mandatory), Image (optional)
   - Returns: Natural language response
   - Use when: General questions, recommendations, comparisons, food identification
   - Can access: All past calorie calculations and conversation history

DECISION RULES:
- User uploads image + asks "calories/nutrition/how many calories" → CALORIE_MODEL
- User asks about food without needing calculation → CONVERSATIONAL_VLM
- User asks general questions (with or without image) → CONVERSATIONAL_VLM
- User asks about past meals/comparisons → CONVERSATIONAL_VLM (has access to history)
- NO IMAGE provided → ALWAYS CONVERSATIONAL_VLM
- Image provided but NO QUERY → CALORIE_MODEL (assume user wants calculation)

CURRENT USER INPUT:
Query: "{user_query}"
Has Image: {has_image}

CONVERSATION CONTEXT (last 5 messages):
{context_str}

Analyze the user's intent and decide which agent to call.

OUTPUT (JSON only):
{{
  "agent": "CALORIE_MODEL" or "CONVERSATIONAL_VLM",
  "reasoning": "Brief explanation of why this agent was chosen",
  "requires_image": true/false,
  "context_to_pass": "What context from history is relevant (if any)"
}}"""

        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an intelligent routing agent. Always respond with valid JSON."},
                {"role": "user", "content": decision_prompt}
            ],
            temperature=0.1
        )
        
        # Parse decision
        try:
            decision_text = response.choices[0].message.content
            json_start = decision_text.find('{')
            json_end = decision_text.rfind('}') + 1
            decision = json.loads(decision_text[json_start:json_end])
            
            return decision
        except Exception as e:
            print(f"❌ Error parsing decision: {e}")
            # Default fallback
            if has_image and not user_query:
                return {"agent": "CALORIE_MODEL", "reasoning": "Image without query - assume calculation needed"}
            else:
                return {"agent": "CONVERSATIONAL_VLM", "reasoning": "Default to conversational"}
    
    # In router_agent.py

    def call_calorie_model(self, image_path):
        """Call calorie estimation model via subprocess interactively."""
        print(f"\n🔧 Calling Calorie Estimation Model (Interactive Mode)...")
        print(f"📷 Image: {image_path}")
        print(f"💬 Please follow the prompts from the agent below.")
        print(f"{'-'*70}\n")
        
        try:
            # --- START OF CHANGES ---

            # 1. Define the KNOWN, FIXED path of the output file from the pipeline.
            hardcoded_output_path = "agent3_output.json"

            # 2. Build the command. It no longer needs the output path argument.
            #    NOTE: Replace "calai.py" with your actual pipeline script name.
            command = ["python", "calai.py", image_path, self.session_folder]

            # 3. Run the subprocess interactively (no output capture).
            result = subprocess.run(
                command,
                check=True,
                timeout=300  # 5 minute timeout
            )
            
            # --- END OF CHANGES ---
            
            print(f"\n{'-'*70}")
            print(f"✅ Interactive Calorie Model Success!")
            
            # 4. After success, find the hardcoded file, read it, and copy it to the session folder.
            if os.path.exists(hardcoded_output_path):
                with open(hardcoded_output_path, 'r', encoding='utf-8') as f:
                    calorie_data = json.load(f)

                # Create a unique name for the result inside the session folder
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                session_output_path = f"{self.session_folder}/calorie_outputs/calc_{timestamp}.json"
                
                # Save the copied data to the new session file
                with open(session_output_path, 'w', encoding='utf-8') as f:
                    json.dump(calorie_data, f, indent=2)

                # Clean up the original hardcoded file
                os.remove(hardcoded_output_path)
                
                return {
                    "success": True,
                    "data": calorie_data,
                    "saved_to": session_output_path
                }
            else:
                return {
                    "success": False,
                    "error": f"Pipeline finished but the output file '{hardcoded_output_path}' was not found."
                }
                
        except subprocess.TimeoutExpired:
            print(f"❌ Calorie Model Timeout!")
            return {"success": False, "error": "Process timed out after 5 minutes"}
        except subprocess.CalledProcessError as e:
            print(f"❌ Calorie Model Failed! See errors above.")
            return {"success": False, "error": f"The script failed with exit code {e.returncode}."}
        except Exception as e:
            print(f"❌ Error calling Calorie Model: {e}")
            return {"success": False, "error": str(e)}
    
    def call_conversational_vlm(self, query, image_path=None):
        """Call conversational VLM via subprocess"""
        print(f"\n💬 Calling Conversational VLM...")
        print(f"📝 Query: {query}")
        if image_path:
            print(f"📷 Image: {image_path}")
        
        try:
            # Build command
            cmd = ["python", "conversational_vlm.py", query]
            if image_path:
                cmd.append(image_path)
            
            # Pass session folder so VLM can access history
            cmd.extend(["--session", self.session_folder])
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                print(f"✅ Conversational VLM Success!")
                response_text = result.stdout.strip()
                
                return {
                    "success": True,
                    "response": response_text
                }
            else:
                print(f"❌ Conversational VLM Failed!")
                print(f"Error: {result.stderr}")
                return {
                    "success": False,
                    "error": result.stderr
                }
                
        except subprocess.TimeoutExpired:
            print(f"❌ Conversational VLM Timeout!")
            return {
                "success": False,
                "error": "Process timed out"
            }
        except Exception as e:
            print(f"❌ Error calling Conversational VLM: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def process_request(self, user_query, image_path=None):
        """Main router logic"""
        
        print(f"\n{'='*70}")
        print(f"🤖 ROUTER AGENT PROCESSING")
        print(f"{'='*70}")
        print(f"User Query: {user_query if user_query else '(No query - image only)'}")
        print(f"Image: {image_path if image_path else 'None'}")
        
        # Save user query
        self._save_message("user", user_query, {
            "has_image": bool(image_path),
            "image_path": image_path
        })
        
        # Decide workflow
        has_image = bool(image_path)
        
        # Special case: No query + has image = calorie calculation
        if not user_query and has_image:
            print(f"\n📊 Auto-routing: No query with image → Calorie Model")
            decision = {
                "agent": "CALORIE_MODEL",
                "reasoning": "Image provided without query - assuming calorie calculation request"
            }
        # Special case: No image = always conversational
        elif not has_image:
            print(f"\n💬 Auto-routing: No image → Conversational VLM")
            decision = {
                "agent": "CONVERSATIONAL_VLM",
                "reasoning": "No image provided - routing to conversational agent"
            }
        else:
            print(f"\n🤔 Analyzing intent with GPT-4...")
            decision = self.decide_workflow(user_query, has_image)
        
        print(f"\n✅ Decision: {decision['agent']}")
        print(f"💡 Reasoning: {decision['reasoning']}")
        
        # Call appropriate agent
        if decision['agent'] == 'CALORIE_MODEL':
            if not has_image:
                error_msg = "Calorie model requires an image, but none was provided."
                print(f"❌ {error_msg}")
                self._save_message("assistant", error_msg, {"error": True})
                return {"error": error_msg}
            
            result = self.call_calorie_model(image_path)
            
            if result['success']:
                # Format response for user
                response = f"✅ Calorie calculation complete!\n\nResults saved to: {result['saved_to']}"
                
                # Save to conversation
                self._save_message("assistant", response, {
                    "agent": "CALORIE_MODEL",
                    "data": result.get('data'),
                    "saved_to": result.get('saved_to')
                })
                
                return result
            else:
                error_msg = f"Calorie model failed: {result['error']}"
                self._save_message("assistant", error_msg, {"error": True})
                return result
        
        else:  # CONVERSATIONAL_VLM
            result = self.call_conversational_vlm(user_query, image_path)
            
            if result['success']:
                response = result['response']
                
                # Save to conversation
                self._save_message("assistant", response, {
                    "agent": "CONVERSATIONAL_VLM"
                })
                
                return result
            else:
                error_msg = f"Conversational VLM failed: {result['error']}"
                self._save_message("assistant", error_msg, {"error": True})
                return result


def main():
    """Main entry point for router agent"""
    
    if len(sys.argv) < 3:
        print("Usage: python router_agent.py <session_folder> <user_query> [image_path]")
        print("\nExamples:")
        print('  python router_agent.py ./session_001 "Calculate calories" food.jpg')
        print('  python router_agent.py ./session_001 "What should I eat for dinner?"')
        print('  python router_agent.py ./session_001 "" food.jpg  (auto-calculates)')
        sys.exit(1)
    
    session_folder = sys.argv[1]
    user_query = sys.argv[2] if sys.argv[2] else None
    image_path = sys.argv[3] if len(sys.argv) > 3 else None
    
    # Validate image path if provided
    if image_path and not os.path.exists(image_path):
        print(f"❌ Error: Image file not found: {image_path}")
        sys.exit(1)
    
    # Initialize router
    router = RouterAgent(session_folder)
    
    # Process request
    result = router.process_request(user_query, image_path)
    
    # Print final result
    print(f"\n{'='*70}")
    print(f"FINAL RESULT")
    print(f"{'='*70}")
    print(json.dumps(result, indent=2))
    print(f"{'='*70}\n")


if __name__ == "__main__":
    main()