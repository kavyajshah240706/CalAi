from openai import OpenAI
import json

class DialogueAgent:
    def __init__(self, api_key, input_callback=None):
        self.client = OpenAI(api_key=api_key)
        self.input_callback = input_callback 

    def confirm_analysis(self, vlm_output: dict) -> dict:
        """Collect all VLM questions → Filter to top 3 → Ask user once → Process all answers"""
        
        print("\n" + "="*70)
        print("FOOD CLARIFICATION")
        print("="*70 + "\n")
        
        # STEP 1: Collect all questions from all segments
        all_questions = []
        segment_data_list = []
        
        for i, segment_data in enumerate(vlm_output.get('analysis_results', []), 1):
            segment_id = segment_data.get('segment_id')
            food_name = segment_data.get('food_name', 'Unknown')
            confidence = segment_data.get('confidence', 0.0)
            ambiguity_flag = segment_data.get('ambiguity_flag', False)
            major_uncertainties = segment_data.get('major_uncertainties', [])
            
            # Get the most important question from VLM
            most_important_q = segment_data.get('most_important_question', '')
            volume = segment_data.get('original_volume_litres', 0.0)
            
            segment_data_list.append({
                'segment_id': segment_id,
                'food_name': food_name,
                'confidence': confidence,
                'ambiguity_flag': ambiguity_flag,
                'major_uncertainties': major_uncertainties,
                'volume': volume,
                'most_important_question': most_important_q
            })
            
            # Add question if segment needs clarification
            needs_clarification = (
                ambiguity_flag or
                confidence < 0.95 or 
                len(major_uncertainties) > 0
            )
            
            if needs_clarification and most_important_q and most_important_q.strip():
                all_questions.append({
                    'segment_id': segment_id,
                    'food_name': food_name,
                    'question': most_important_q,
                    'confidence': confidence
                })
        
        # STEP 2: Filter to top 3 most important questions (avoid duplicates)
        selected_questions = self._select_top_questions(all_questions, max_questions=3)
        
        # STEP 3: Display segments info
        print("FOOD SEGMENTS IDENTIFIED:\n")
        for seg in segment_data_list:
            print(f"Segment {seg['segment_id']}: {seg['food_name']}")
            print(f"  Volume: {seg['volume']:.3f}L | Confidence: {seg['confidence']:.0%}")
            if seg['major_uncertainties']:
                print(f"  Uncertainty: {seg['major_uncertainties'][0][:80]}...")
            print()
        
        # STEP 4: Ask all selected questions at once
        user_answers = {}
        
        if selected_questions:
            print("="*70)
            print("CLARIFICATION QUESTIONS")
            print("="*70 + "\n")
            print(f"Please answer these {len(selected_questions)} question(s):\n")
            
            for idx, q_data in enumerate(selected_questions, 1):
                print(f"{idx}. [Segment {q_data['segment_id']} - {q_data['food_name']}]")
                print(f"   {q_data['question']}")
                print()
            
            print("Your answers (type freely, press Enter twice when done):")
            bulk_answer = self._get_user_input()
            
            if bulk_answer:
                # Parse answers using LLM
                user_answers = self._parse_bulk_answers(selected_questions, bulk_answer)
                
                print("\n" + "="*70)
                print("PARSED ANSWERS:")
                print("="*70)
                for seg_id, answer in user_answers.items():
                    print(f"Segment {seg_id}: {answer}")
                print()
            else:
                print("\nNo answers provided - using defaults\n")
        else:
            print("All segments have high confidence - no questions needed\n")
        
        # STEP 5: Synthesize final food names for each segment
        final_results = []
        
        for seg_data in segment_data_list:
            seg_id = seg_data['segment_id']
            user_answer = user_answers.get(seg_id, None)
            
            # Check if a question was actually ASKED for this segment
            question_was_asked = any(q['segment_id'] == seg_id for q in selected_questions)
            
            if user_answer and question_was_asked:
                # Synthesize with user input
                final_spec = self._call_synthesizer(
                    seg_data['food_name'],
                    seg_data['major_uncertainties'],
                    [seg_data['most_important_question']],
                    user_answer,
                    seg_data['volume']
                )
            else:
                # No question asked OR no answer - use original VLM name
                final_spec = {
                    "food_name": seg_data['food_name'],
                    "volume_litres": seg_data['volume'],
                    "clarifications": {},
                    "user_response": None,
                    "questions_asked": []
                }
            
            final_results.append({
                "segment_id": seg_id,
                "final_food_name": final_spec['food_name'],
                "volume_litres": final_spec['volume_litres'],
                "clarifications": final_spec.get('clarifications', {}),
                "user_response": final_spec.get('user_response'),
                "questions_asked": final_spec.get('questions_asked', [])
            })
        
        # STEP 6: Ask for additional suggestions
        print("\n" + "="*70)
        print("ADDITIONAL SUGGESTIONS")
        print("="*70 + "\n")
        print("Any additional details you'd like to add about any food item?")
        print("(cooking method, ingredients, preparation, etc.)")
        print("(Press Enter twice to finish):\n")
        
        additional_suggestions = self._get_user_input()
        
        if additional_suggestions:
            print(f"\nAdditional input: {additional_suggestions}\n")
            final_results = self._refine_with_suggestions(final_results, additional_suggestions)
        else:
            print("\nNo additional suggestions.\n")
        
        self._print_summary(final_results)
        
        return {
            "confirmed_results": final_results,
            "additional_suggestions": additional_suggestions
        }

    def _select_top_questions(self, all_questions, max_questions=3):
        """Select top N most important questions, avoiding duplicates"""
        
        if not all_questions:
            return []
        
        if len(all_questions) <= max_questions:
            return all_questions
        
        # Ask LLM to rank and select
        prompt = f"""Select the {max_questions} most important questions from this list.

QUESTIONS:
{json.dumps([{
    'segment_id': q['segment_id'],
    'food': q['food_name'],
    'question': q['question'],
    'confidence': q['confidence']
} for q in all_questions], indent=2)}

RULES:
1. Select max {max_questions} questions
2. Prioritize questions with lowest confidence scores
3. Avoid duplicate/similar questions
4. Focus on questions that affect calories significantly

OUTPUT JSON:
{{
  "selected_segment_ids": [1, 3, 5],
  "reasoning": "why these were chosen"
}}"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a question prioritization assistant. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.2
            )
            
            result = json.loads(response.choices[0].message.content)
            selected_ids = result.get('selected_segment_ids', [])
            
            # Filter questions by selected IDs
            selected = [q for q in all_questions if q['segment_id'] in selected_ids]
            return selected[:max_questions]
            
        except Exception as e:
            print(f"Question selection failed: {e}")
            # Fallback: take first 3
            return all_questions[:max_questions]

    def _parse_bulk_answers(self, questions, bulk_answer):
        """Parse user's bulk answer and map to specific segments"""
        
        prompt = f"""Parse user's bulk answer and extract answers for each specific question.

QUESTIONS ASKED:
{json.dumps([{
    'segment_id': q['segment_id'],
    'food': q['food_name'],
    'question': q['question']
} for q in questions], indent=2)}

USER'S BULK ANSWER:
{bulk_answer}

TASK:
Extract what the user said for each segment. If user didn't answer a question, set to null.

RULES:
- Match user's response to the correct segment
- Extract relevant portion of answer for each segment
- If user numbered their answers (1., 2., 3.), map accordingly
- If user mentioned segment/food explicitly, match that
- Keep answers concise but complete

OUTPUT JSON:
{{
  "answers": {{
    "1": "answer for segment 1 or null",
    "2": "answer for segment 2 or null",
    "3": "answer for segment 3 or null"
  }}
}}"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an answer parsing assistant. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.2
            )
            
            result = json.loads(response.choices[0].message.content)
            answers_dict = result.get('answers', {})
            
            # Convert string keys to int
            return {int(k): v for k, v in answers_dict.items() if v}
            
        except Exception as e:
            print(f"Answer parsing failed: {e}")
            return {}

    def _get_user_input(self):
        """Get user input via API or terminal"""
        if self.input_callback:
            # Use callback
            print("\n[WAITING_FOR_INPUT]")
            user_input = self.input_callback()
            print(f"[INPUT_RECEIVED]: {user_input[:100]}...")
            return user_input
        else:
            # Try API first, fallback to terminal
            try:
                import requests
                print("\n[WAITING_FOR_INPUT]")
                response = requests.get('http://localhost:5001/get-input', timeout=310)
                if response.status_code == 200:
                    user_input = response.json().get('input', '')
                    print(f"[INPUT_RECEIVED]: {user_input[:100]}...")
                    return user_input
            except:
                pass
            
            # Fallback to terminal input
            print("(Type your answer and press Enter twice):")
            lines = []
            empty_count = 0
            while True:
                try:
                    line = input()
                    if line == "":
                        empty_count += 1
                        if empty_count >= 2:
                            break
                    else:
                        empty_count = 0
                        lines.append(line)
                except:
                    break
            return "\n".join(lines).strip()

    def _call_synthesizer(self, vlm_name, uncertainties, questions, user_answer, volume):
        """Synthesize final food name with user clarifications"""
        
        prompt = f"""Create detailed food name from user input.

VLM IDENTIFIED: {vlm_name}
VOLUME: {volume:.3f} litres

UNCERTAINTIES:
{chr(10).join(uncertainties) if uncertainties else "None"}

QUESTION ASKED:
{questions[0] if questions else "None"}

USER ANSWERED:
{user_answer}

TASK:
Create a detailed, specific food name incorporating user's clarification.

RULES:
- If user clarified food identity → update food name
- If user mentioned specifics → include them
- Be descriptive but concise

EXAMPLES:
User: "paneer not tofu" → "Paneer Curry"
User: "plain rice no oil" → "Plain Steamed Rice (No Oil)"
User: "it's grilled" → "Grilled [Food]"

OUTPUT JSON:
{{
  "food_name": "detailed name",
  "clarifications": {{"key": "value"}}
}}"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a food identification assistant. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.3
            )
            
            data = json.loads(response.choices[0].message.content)
            
            return {
                "food_name": data.get('food_name', vlm_name),
                "volume_litres": volume,
                "clarifications": data.get('clarifications', {}),
                "user_response": user_answer,
                "questions_asked": questions
            }
            
        except Exception as e:
            print(f"Synthesizer failed: {e}")
            return {
                "food_name": f"{vlm_name} [{user_answer[:30]}]",
                "volume_litres": volume,
                "clarifications": {},
                "user_response": user_answer,
                "questions_asked": questions
            }

    def _refine_with_suggestions(self, results, suggestions):
        """Refine results with additional suggestions"""
        
        prompt = f"""Update food names based on additional user suggestions.

CURRENT:
{json.dumps([{
    'id': r['segment_id'],
    'name': r['final_food_name'],
    'volume': r['volume_litres']
} for r in results], indent=2)}

USER SUGGESTIONS:
{suggestions}

Update relevant items based on suggestions. Keep others unchanged.

OUTPUT JSON:
{{
  "updates": [
    {{"segment_id": 1, "new_name": "updated name", "changed": true}},
    {{"segment_id": 2, "changed": false}}
  ]
}}"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.3
            )
            
            data = json.loads(response.choices[0].message.content)
            updates = data.get('updates', [])
            
            for update in updates:
                if update.get('changed'):
                    seg_id = update['segment_id']
                    for r in results:
                        if r['segment_id'] == seg_id:
                            r['final_food_name'] = update['new_name']
                            r['additional_suggestions'] = suggestions
            
            return results
            
        except Exception as e:
            print(f"Refinement failed: {e}")
            for r in results:
                r['additional_suggestions'] = suggestions
            return results

    def _print_summary(self, results):
        """Print final summary"""
        print("\n" + "="*70)
        print("FINAL CONFIRMED FOODS")
        print("="*70 + "\n")
        
        for r in results:
            print(f"{r['segment_id']}. {r['final_food_name']}")
            print(f"   Volume: {r['volume_litres']:.3f}L")
            if r.get('clarifications'):
                print(f"   Details: {r['clarifications']}")
            print()
        
        total = sum(r['volume_litres'] for r in results)
        print(f"Total: {len(results)} items, {total:.3f}L")
        print("="*70 + "\n")