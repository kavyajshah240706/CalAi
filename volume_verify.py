"""
Volume Verification Agent
Verifies and refines volume estimates using VLM analysis
Takes final_confirmed_output.json + original image → outputs verified_volumes.json

Usage: python volume_verify.py <final_confirmed_output.json> <original_image_path>
"""

import sys
import json
import base64
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


class VolumeVerifyAgent:
    def __init__(self, api_key):
        """Initialize the volume verification agent"""
        self.client = OpenAI(api_key=api_key)
    
    def encode_image(self, image_path):
        """Encode image to base64 for GPT-4V"""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    
    def verify_volumes_with_vlm(self, confirmed_foods, image_path):
        """
        Use VLM to verify volume estimates for each food item
        
        Args:
            confirmed_foods: List of confirmed food items with volumes
            image_path: Path to original food image
        
        Returns:
            List of foods with verified volumes
        """
        
        print("\n" + "="*70)
        print("VOLUME VERIFICATION WITH VLM")
        print("="*70 + "\n")
        
        # Encode image
        base64_image = self.encode_image(image_path)
        
        # Build food summary for VLM
        foods_summary = []
        for food in confirmed_foods:
            seg_id = food.get('segment_id')
            name = food.get('final_food_name')
            volume_litres = food.get('volume_litres')
            
            foods_summary.append({
                'segment_id': seg_id,
                'food_name': name,
                'estimated_volume_litres': volume_litres
            })
        
        # Create VLM prompt
        prompt = f"""You are a food volume verification expert. Analyze this food image and verify the volume estimates.

FOOD ITEMS WITH ESTIMATED VOLUMES:
{json.dumps(foods_summary, indent=2)}

YOUR TASK:
1. Look at the image and identify each food item
2. Assess if the volume estimates seem reasonable
3. For each item, provide:
   - Is the volume estimate reasonable? (yes/no/uncertain)
   - If NO: What would be a better estimate?
   - Confidence in your assessment (0.0-1.0)
   - Brief reasoning

VOLUME REFERENCE GUIDE:
- 1 litre = 1000 cm³ = 1000 ml
- Average plate: 20-25cm diameter
- Average bowl: 300-500ml
- Rice serving: 150-200ml (0.15-0.2L)
- Dal/curry: 200-300ml (0.2-0.3L)
- Roti/chapati: ~50-75ml volume (0.05-0.075L)

ASSESSMENT CRITERIA:
- Does the item look proportional to its estimated volume?
- Compare relative sizes of items on the plate
- Consider food density and packing
- Account for irregular shapes

OUTPUT FORMAT (JSON):
{{
  "verified_volumes": [
    {{
      "segment_id": 1,
      "food_name": "Rice",
      "original_volume_litres": 0.250,
      "volume_reasonable": true,
      "suggested_volume_litres": 0.250,
      "confidence": 0.85,
      "reasoning": "Volume looks appropriate for rice portion shown",
      "adjustment_made": false
    }},
    {{
      "segment_id": 2,
      "food_name": "Dal",
      "original_volume_litres": 0.500,
      "volume_reasonable": false,
      "suggested_volume_litres": 0.300,
      "confidence": 0.75,
      "reasoning": "Dal portion appears smaller than 500ml, suggesting 300ml",
      "adjustment_made": true
    }}
  ],
  "overall_confidence": 0.80,
  "notes": "Overall volumes seem reasonable with minor adjustments"
}}

IMPORTANT:
- Be conservative with adjustments
- Only suggest changes if you're reasonably confident (>0.7)
- Consider relative proportions between items
- Account for perspective and camera angle"""

        try:
            print("Calling VLM for volume verification...\n")
            
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                response_format={"type": "json_object"},
                max_tokens=2000,
                temperature=0.3
            )
            
            result = json.loads(response.choices[0].message.content)
            
            print("✅ VLM verification complete!\n")
            
            return result
            
        except json.JSONDecodeError as e:
            print(f"❌ Error: VLM returned invalid JSON: {e}")
            # Return original volumes as fallback
            return self._create_fallback_response(confirmed_foods)
        
        except Exception as e:
            print(f"❌ Error during VLM verification: {e}")
            return self._create_fallback_response(confirmed_foods)
    
    def _create_fallback_response(self, confirmed_foods):
        """Create fallback response if VLM fails"""
        verified = []
        
        for food in confirmed_foods:
            verified.append({
                "segment_id": food.get('segment_id'),
                "food_name": food.get('final_food_name'),
                "original_volume_litres": food.get('volume_litres'),
                "volume_reasonable": True,
                "suggested_volume_litres": food.get('volume_litres'),
                "confidence": 0.5,
                "reasoning": "VLM verification failed, using original estimate",
                "adjustment_made": False
            })
        
        return {
            "verified_volumes": verified,
            "overall_confidence": 0.5,
            "notes": "VLM verification failed, original volumes retained"
        }
    
    def print_verification_summary(self, verification_result):
        """Print a summary of verification results"""
        
        print("="*70)
        print("VOLUME VERIFICATION SUMMARY")
        print("="*70 + "\n")
        
        verified_items = verification_result.get('verified_volumes', [])
        
        for item in verified_items:
            seg_id = item.get('segment_id')
            name = item.get('food_name')
            original = item.get('original_volume_litres')
            suggested = item.get('suggested_volume_litres')
            reasonable = item.get('volume_reasonable')
            adjusted = item.get('adjustment_made')
            confidence = item.get('confidence')
            reasoning = item.get('reasoning')
            
            print(f"Segment {seg_id}: {name}")
            print(f"  Original Volume: {original:.3f}L")
            
            if adjusted:
                print(f"  ⚠️  ADJUSTED to: {suggested:.3f}L")
                change_pct = ((suggested - original) / original) * 100
                print(f"  Change: {change_pct:+.1f}%")
            else:
                print(f"  ✅ VERIFIED: {suggested:.3f}L")
            
            print(f"  Confidence: {confidence:.0%}")
            print(f"  Reasoning: {reasoning}")
            print()
        
        overall_conf = verification_result.get('overall_confidence', 0.0)
        notes = verification_result.get('notes', '')
        
        print(f"Overall Confidence: {overall_conf:.0%}")
        print(f"Notes: {notes}")
        print("="*70 + "\n")
    
    def process(self, confirmed_output_path, image_path):
        """
        Main processing logic
        
        Args:
            confirmed_output_path: Path to final_confirmed_output.json
            image_path: Path to original food image
        
        Returns:
            Verification results dict
        """
        
        print("\n" + "="*70)
        print("VOLUME VERIFICATION AGENT")
        print("="*70)
        print(f"Input: {confirmed_output_path}")
        print(f"Image: {image_path}")
        print("="*70 + "\n")
        
        # Load confirmed output
        try:
            with open(confirmed_output_path, 'r', encoding='utf-8') as f:
                confirmed_data = json.load(f)
        except FileNotFoundError:
            print(f"❌ Error: File not found: {confirmed_output_path}")
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"❌ Error: Invalid JSON in {confirmed_output_path}: {e}")
            sys.exit(1)
        
        # Check image exists
        if not os.path.exists(image_path):
            print(f"❌ Error: Image not found: {image_path}")
            sys.exit(1)
        
        # Extract confirmed foods
        confirmed_foods = confirmed_data.get('confirmed_results', [])
        
        if not confirmed_foods:
            print("❌ Error: No confirmed foods found in input file")
            sys.exit(1)
        
        print(f"Found {len(confirmed_foods)} food items to verify\n")
        
        # Verify volumes with VLM
        verification_result = self.verify_volumes_with_vlm(confirmed_foods, image_path)
        
        # Print summary
        self.print_verification_summary(verification_result)
        
        # Add metadata
        verification_result['input_file'] = confirmed_output_path
        verification_result['image_file'] = image_path
        verification_result['total_items'] = len(confirmed_foods)
        
        return verification_result


def main():
    """Main entry point"""
    
    if len(sys.argv) < 3:
        print("Usage: python volume_verify.py <final_confirmed_output.json> <original_image_path>")
        print("\nExample:")
        print('  python volume_verify.py final_confirmed_output.json food_image.jpg')
        sys.exit(1)
    
    confirmed_output_path = sys.argv[1]
    image_path = sys.argv[2]
    
    # Get API key from environment
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ Error: OPENAI_API_KEY not found in environment")
        sys.exit(1)
    
    # Initialize agent
    agent = VolumeVerifyAgent(api_key)
    
    # Process
    try:
        result = agent.process(confirmed_output_path, image_path)
        
        # Save output
        output_file = "verified_volumes.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Volume verification complete!")
        print(f"📄 Output saved to: {output_file}")
        
    except Exception as e:
        print(f"\n❌ Error during volume verification: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()