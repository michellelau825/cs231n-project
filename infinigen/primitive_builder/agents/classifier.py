import openai
from typing import Tuple, Literal
import json

class FurnitureClassifier:
    def __init__(self, api_key: str):
        self.client = openai.OpenAI(api_key=api_key)
        
    def classify(self, prompt: str) -> Tuple[Literal["pass", "not a furniture"], str]:
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
    "classification": "not a furniture",
    "explanation": "Primarily outdoor decorative item not serving indoor furnishing purposes"
}

Input: "The concept of time"
Output: {
    "classification": "not a furniture",
    "explanation": "Abstract concept without physical form or indoor utility"
}

Input: "A wall-mounted coat rack"
Output: {
    "classification": "pass",
    "explanation": "Indoor utility fixture for organizing clothing and accessories"
}

Respond with a JSON object containing 'classification' (either 'pass' or 'not a furniture') and 'explanation'."""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4-0125-preview",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1
            )
            
            result = json.loads(response.choices[0].message.content)
            return (result["classification"], result["explanation"])
            
        except Exception as e:
            print(f"Error in classification: {e}")
            return ("not a furniture", "Error in classification process")