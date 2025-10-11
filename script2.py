import json
from pathlib import Path
from openai import OpenAI
from PIL import Image
import sys
import requests
import os
import config 
from agents.dialogue_agent import DialogueAgent
import base64
import time

# PASTE THIS ENTIRE FUNCTION AT THE TOP OF YOUR SCRIPT2.PY FILE

def filter_metadata_file(filepath: str, min_volume: float = 0.1):
    """
    Opens the specified JSON file, removes segments with volume < min_volume,
    and saves the changes back to the same file.
    """
    print("-" * 60)
    print(f"CLEANUP: Filtering metadata file: {filepath}")
    
    if not os.path.exists(filepath):
        print(f"❌ ERROR: Cannot filter file. Not found at '{filepath}'")
        return False

    try:
        with open(filepath, 'r') as f:
            metadata = json.load(f)

        original_segments = metadata.get('segments', [])
        if not original_segments:
            print("No segments found in the file to filter.")
            return True

        print(f"Found {len(original_segments)} segments in file.")

        filtered_segments = [
            segment for segment in original_segments if segment.get('volume', 0) >= min_volume
        ]

        removed_count = len(original_segments) - len(filtered_segments)
        if removed_count > 0:
            print(f"Removing {removed_count} segment(s) with volume < {min_volume}L.")
        else:
            print("No segments needed to be removed.")

        metadata['segments'] = filtered_segments
        metadata['total_segments'] = len(filtered_segments)

        with open(filepath, 'w') as f:
            json.dump(metadata, f, indent=2)

        print(f"✅ Successfully cleaned and saved '{filepath}'.")
        print("-" * 60)
        return True

    except Exception as e:
        print(f"❌ ERROR during file filtering: {e}")
        print("-" * 60)
        return False

def call_volume_estimation_api(image_path, api_url='http://localhost:5000/estimate-volume'):
    print(f"Calling volume estimation API for image: {image_path}")
    if not Path(image_path).exists():
        print(f"Error: Input image not found at {image_path}")
        return None
    try:
        with open(image_path, 'rb') as f:
            files = {'image': (os.path.basename(image_path), f)}
            response = requests.post(api_url, files=files, timeout=150)
        if response.status_code == 200:
            data = response.json()
            print("API call successful.")
            return data.get('metadata_file')
        else:
            print(f"Error calling API: Status code {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"An error occurred while calling the API: {e}")
        return None

def analyze_food_image(client: OpenAI, image_path: str, volume_l: float) -> dict:
    """Analyze a single food segment image using Gemini VLM"""
    
    image = Image.open(image_path)
    
    prompt = f"""CRITICAL: This image shows a plate. You must identify ONLY the ONE specific food item that is segmented/highlighted in this image. IGNORE everything else on the plate.

CONTEXT:
- Volume of THIS ITEM: {volume_l:.3f} litres
- Focus on the highlighted/segmented food only

YOUR TASK:
1. Identify this specific food item. Focus on uncertainties that SIGNIFICANTLY affect calorie count.
2. Based on the most significant uncertainty, formulate ONLY ONE critical question to ask the user. This question should aim to resolve the biggest potential calorie difference.

ASK YOURSELF:
1. Can I clearly identify what this food IS?
   - If it's white liquid: Is it milk, yogurt, or cream?
   - If it's protein: Chicken, paneer, tofu, or egg?

2. What is the single biggest point of confusion that impacts calories?
   - Could this be paneer OR tofu? (This is a huge calorie difference, a great question to ask).
   - Could this be a sugar-free dessert OR a full-sugar dessert? (Also a great question).

DO NOT worry about:
- Cooking oil type
- Spices or garnishes
- Type of grains (e.g., basmati vs. sona masoori rice)
- Minor brand differences

RESPONSE FORMAT (JSON):
{{
  "food_name": "best guess for THIS ITEM only",
  "confidence": 0.0-1.0,
  "major_uncertainties": [
    "A list of reasons for the uncertainty, focusing on high-calorie differences."
  ],
  "most_important_question": "The single most critical question to resolve calorie ambiguity. Should be an empty string if confidence is > 0.94.",
  "ambiguity_flag": true/false
}}

CONFIDENCE LEVELS:
- 0.95-1.0: I know exactly what this is. No question needed.
- 0.85-0.94: I know the food but there's a minor variety uncertainty. A question might be useful but not critical.
- 0.70-0.84: Could be 2-3 different foods. A question is necessary.
- <0.70: Very unclear. A question is necessary.

Set ambiguity_flag TRUE if:
- You cannot clearly identify the food.
- This could be 2+ foods with a 50+ calorie difference per 100g.

EXAMPLES of how to generate the single question:

Uncertainty: "This could be paneer (high protein, high cal) or tofu (lower cal)"
Resulting JSON field: `"most_important_question": "Is this paneer or tofu?"`

Uncertainty: "I cannot tell if this is ketchup (high sugar) or tomato chutney (lower sugar)"
Resulting JSON field: `"most_important_question": "Is this ketchup or a homemade tomato chutney?"`

Uncertainty: "Cannot tell if this is a fried pakora (high cal) or a steamed idli (low cal)"
Resulting JSON field: `"most_important_question": "Is this item fried or steamed?"`

Respond ONLY with the JSON object."""

    try:
    # Encode image to base64
        with open(image_path, 'rb') as img_file:
            image_data = base64.b64encode(img_file.read()).decode('utf-8')
        
        response = client.chat.completions.create(
            model="gpt-5-mini",  # or "gpt-4o-mini" for cheaper
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_data}"
                            }
                        }
                    ]
                }
            ],
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
            
        # Validate we got a specific food, not a meal description
        food_name = result.get('food_name', 'Unknown')
        if any(word in food_name.lower() for word in ['meal', 'plate', 'dish with', 'and', 'rice meal', 'with dal']):
            print(f"  WARNING: VLM returned meal description instead of specific item: {food_name}")
            print(f"  Attempting to extract specific food...")
            # Try to force it to be more specific
            result['ambiguity_flag'] = True
            result['confidence'] = min(result.get('confidence', 0.5), 0.7)
        
        # Ensure required fields
        if 'food_name' not in result:
            result['food_name'] = 'Unknown food'
        if 'confidence' not in result:
            result['confidence'] = 0.5
        if 'ambiguity_flag' not in result:
            result['ambiguity_flag'] = True
        if 'what_i_cannot_determine' not in result:
            result['what_i_cannot_determine'] = []
        if 'assumptions_i_am_making' not in result:
            result['assumptions_i_am_making'] = []
            
        return result
        
    except json.JSONDecodeError as e:
        print(f"Warning: VLM returned invalid JSON: {e}")
        return {
            "food_name": "Unknown food",
            "confidence": 0.0,
            "ambiguity_flag": True,
            "what_i_see": "Error parsing response",
            "what_i_cannot_determine": [],
            "assumptions_i_am_making": [],
            "error": str(e)
        }
    except Exception as e:
        print(f"Error during Gemini API call: {e}")
        return {
            "food_name": "Unknown food",
            "confidence": 0.0,
            "ambiguity_flag": True,
            "what_i_cannot_determine": [],
            "assumptions_i_am_making": [],
            "error": str(e)
        }

def run_vlm_analysis(metadata_path, api_key):
    """Analyze all food segments using VLM"""
    print("\n" + "="*60)
    print("PART 1: VLM FOOD IDENTIFICATION")
    print("="*60)
    
    client = OpenAI(api_key=api_key)
    
    # Load metadata
    with open(metadata_path, 'r') as f:
        metadata = json.load(f)
    
    print(f"\nFound {len(metadata['segments'])} food segments to analyze\n")
    
    results = []
    for i, segment in enumerate(metadata['segments'], 1):
        segment_id = segment['segment_id']
        volume_litres = segment['volume']
        image_path = segment['image_path']
        
        print(f"[{i}/{len(metadata['segments'])}] Analyzing Segment {segment_id}...")
        print(f"  Volume: {volume_litres:.3f} litres")
        print(f"  Image: {segment['image_filename']}")
        
        # Analyze with VLM
        analysis = analyze_food_image(client, image_path, volume_litres)
        
        print(f"  Identified: {analysis.get('food_name', 'Unknown')}")
        print(f"  Confidence: {analysis.get('confidence', 0):.2f}")
        print(f"  Ambiguous: {analysis.get('ambiguity_flag', True)}")
        print()
        
        # Store results with volume
        analysis['original_volume_litres'] = volume_litres
        analysis['segment_id'] = segment_id
        analysis['image_path'] = image_path
        
        results.append(analysis)
    
    output = {"analysis_results": results}
    
    print("="*60)
    print("VLM Analysis Complete")
    print("="*60 + "\n")
    
    return output


def main():
    if len(sys.argv) < 2:
        print("Usage: python script2.py \"<path_to_your_image>\"")
        sys.exit(1)
        
    input_image_path = sys.argv[1]
    
    print("\n" + "="*60)
    print("FOOD ANALYSIS PIPELINE")
    print("="*60 + "\n")
    
    # Step 1: Call Volume Estimation API
    # Step 1: Call Volume Estimation API
    print("STEP 1: Volume Estimation")
    print("-" * 60)
    
    volume_start_time = time.time()
    metadata_file_path = call_volume_estimation_api(input_image_path)
    volume_end_time = time.time()
    print(f"Volume Estimation API call took: {volume_end_time - volume_start_time:.2f} seconds")
    
    # --- THIS IS THE FIX ---
    # If the API call fails, now it will stop the entire pipeline.
    if not metadata_file_path:
        print("Critical Error: Volume estimation failed. Halting pipeline.")
        sys.exit(1) # Changed from 'return' to 'sys.exit(1)'
    # --- END OF FIX ---
    
    print(f"Metadata received: {metadata_file_path}\n")
    if not filter_metadata_file(metadata_file_path):
        print("Critical Error: Failed to filter metadata file. Halting pipeline.")
        sys.exit(1)
    
    # Step 2: Run VLM Analysis
    # Step 2: Run VLM Analysis
    api_key = config.OPENAI_API_KEY
    if not api_key:
        print("Error: OpenAI API key not found in config.py")
        sys.exit(1) # Changed from 'return' to 'sys.exit(1)'
    
    vlm_start_time = time.time()
    vlm_results = run_vlm_analysis(metadata_file_path, api_key)
    vlm_end_time = time.time()
    print(f"VLM analysis took: {vlm_end_time - vlm_start_time:.2f} seconds")
    
    with open("vlm_analysis_output.json", 'w') as f:
        json.dump(vlm_results, f, indent=2)
    print(f"VLM results saved: vlm_analysis_output.json\n")
    
    # Step 3: Run Dialogue Agent for Confirmation
    # Step 3: Run Dialogue Agent for Confirmation
    print("STEP 2: User Confirmation")
    print("-" * 60)
    
    dialogue_start_time = time.time()
    dialogue_agent = DialogueAgent(api_key=api_key)
    confirmed_results = dialogue_agent.confirm_analysis(vlm_results)
    dialogue_end_time = time.time()
    print(f"Dialogue Agent (including user input time) took: {dialogue_end_time - dialogue_start_time:.2f} seconds")
    
    # Step 4: Save Final Output
    FINAL_OUTPUT_FILE = "final_confirmed_output.json"
    with open(FINAL_OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(confirmed_results, f, indent=2, ensure_ascii=False)
    
    print("\n" + "="*60)
    print("PIPELINE COMPLETE!")
    print("="*60)
    print(f"Final output: {FINAL_OUTPUT_FILE}")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()