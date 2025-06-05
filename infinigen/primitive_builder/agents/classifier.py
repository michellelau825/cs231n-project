import openai
from typing import Tuple, Literal
import json

class FurnitureClassifier:
    def __init__(self, api_key: str):
        self.client = openai.OpenAI(api_key=api_key)
        
    def classify(self, prompt: str) -> Tuple[Literal["pass", "does not pass"], str]:
        system_prompt = """You are an expert at classifying indoor objects and furniture. Your task is to determine if a described object is appropriate for indoor furniture generation.
DO NOT use keywords to make your decision. Instead, analyze the object's:
1. Primary use context (indoor vs outdoor)
2. Physical characteristics (tangible form, size, stability)
3. Relationship to indoor living spaces

Examples:
Input: "A comfortable rocking chair with curved runners"
Output: {
    "classification": "pass",
    "explanation": "Primary indoor seating furniture with physical form suitable for indoor spaces"
}

Input: "A garden gnome"
Output: {
    "classification": "does not pass",
    "explanation": "Primarily outdoor decorative item not serving indoor furnishing purposes"
}

Input: "The concept of time"
Output: {
    "classification": "does not pass",
    "explanation": "Abstract concept without physical form or indoor utility"
}

Input: "A wall-mounted coat rack"
Output: {
    "classification": "pass",
    "explanation": "Indoor utility fixture for organizing clothing and accessories"
}

Respond with a JSON object containing 'classification' (either 'pass' or 'does not pass') and 'explanation'."""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-2024-08-06",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            return (result["classification"], result["explanation"])
            
        except Exception as e:
            print(f"Error in classification: {e}")
            print(f"Error type: {type(e)}")
            print(f"Full error details: {repr(e)}")
            return ("does not pass", "Error in classification process")