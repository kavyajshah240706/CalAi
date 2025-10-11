import json
import base64
from PIL import Image
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv
import os
import sys
import io

# Load .env
load_dotenv()

# Initialize the OpenAI VLM with JSON Mode enabled
vlm = ChatOpenAI(
    model="gpt-4o", 
    temperature=0.2, 
    openai_api_key=os.getenv("OPENAI_API_KEY"),
    model_kwargs={"response_format": {"type": "json_object"}}
)

def verify_and_correct_volume(json_data: dict, image_path: str):
    """
    Asks OpenAI VLM to visually verify and correct volume estimates.
    """
    print("  👁️  Asking OpenAI VLM to verify volume estimates...")

    try:
        # (Image resizing logic remains the same)
        print(f"  Resizing image for faster processing: {image_path}")
        with Image.open(image_path) as img:
            img.thumbnail((1024, 1024))
            buffer = io.BytesIO()
            if img.mode in ('RGBA', 'LA'):
                img = img.convert('RGB')
            img.save(buffer, format="JPEG")
            img_bytes = buffer.getvalue()
            img_b64 = base64.b64encode(img_bytes).decode("utf-8")
        image_data_url = f"data:image/jpeg;base64,{img_b64}"
    except Exception as e:
        print(f"  ❌ Error processing image: {e}")
        return json_data

    # Extract the list of segments to be verified
    prompt_data_list = json_data.get("confirmed_results")
    if not isinstance(prompt_data_list, list):
        print("  ❌ Error: 'confirmed_results' in the input JSON is not a list.")
        return json_data

    query = f"""
    You are a precise volume estimation assistant. Your task is to analyze the provided image and JSON data.
    The JSON data is a LIST of food items.

    Visually inspect the image and verify if the 'volume_litres' in the following JSON list seems reasonable for each food item.

    JSON LIST TO VERIFY:
    {json.dumps(prompt_data_list, indent=2)}

    RULES:
    1. If a volume is clearly wrong, correct it.
    2. If a volume seems reasonable, DO NOT change it.
    3. Your response MUST be a valid JSON list with the exact same number of items as the input.
    4. Do not change any keys; only update 'volume_litres' values if necessary.

    Your entire response must be a single, valid JSON list.
    """

    try:
        print("  ...Sending request to OpenAI API...")
        response = vlm.invoke([
            HumanMessage(content=[
                {"type": "text", "text": query},
                {"type": "image_url", "image_url": {"url": image_data_url}}
            ])
        ])
        print("  ...Received response from OpenAI API.")

        if not response or not response.content:
            print("  ❌ CRITICAL ERROR: VLM returned an EMPTY response.")
            return json_data

        # The AI will return a corrected LIST of segments
        corrected_segment_list = json.loads(response.content)
        
        if not isinstance(corrected_segment_list, list) or len(corrected_segment_list) != len(prompt_data_list):
            print("  ❌ ERROR: VLM response was not a list or had a different number of items. Discarding corrections.")
            return json_data

        print("  ✅ VLM verification complete and response parsed correctly.")
        
        # Create a copy of the original full JSON data
        final_corrected_data = json_data.copy()
        
        # Replace the original list with the new, corrected list
        final_corrected_data["confirmed_results"] = corrected_segment_list
        
        return final_corrected_data

    except Exception as e:
        print(f"  ❌ A CRITICAL ERROR occurred during the VLM API call: {e}")
        return json_data

# --- THIS IS THE MISSING MAIN FUNCTION THAT HAS BEEN RESTORED ---
def main():
    """Main function to run the script from the command line."""
    if len(sys.argv) < 3:
        print("Usage: python volume_verify.py <input_json> <input_image>")
        sys.exit(1)

    input_json_file = sys.argv[1]
    image_file = sys.argv[2]
    output_json_file = "final_confirmed_output_corrected.json"

    print(f"Reading data from: {input_json_file}")
    try:
        with open(input_json_file, "r") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"❌ ERROR: Input JSON file not found: {input_json_file}")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"❌ ERROR: Could not decode JSON from {input_json_file}")
        sys.exit(1)

    corrected_data = verify_and_correct_volume(data, image_file)

    with open(output_json_file, "w") as f:
        json.dump(corrected_data, f, indent=2)

    print(f"Processing complete. Data saved to: {output_json_file}")


if __name__ == "__main__":
    main()