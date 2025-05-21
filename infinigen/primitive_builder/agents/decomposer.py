import openai
from typing import Dict, List
import json

class SemanticDecomposer:
    def __init__(self, api_key: str):
        self.client = openai.OpenAI(api_key=api_key)
        
    def decompose(self, prompt: str) -> Dict:
        system_prompt = """You are a 3D modeling expert specializing in geometric decomposition. Break down objects into their core components, being EXPLICIT about quantities of identical components.

Example 1 - Office Chair:
Input: "A height-adjustable office chair with armrests"
Output: {
    "description": "A height-adjustable seat mounted on a central support column that branches into a five-pronged star-shaped base. Each prong terminates in a caster wheel. The seat is padded with a contoured surface. A curved backrest extends upward from the rear, featuring lumbar support. Two identical adjustable armrests are mounted to the sides.",
    "components": [
        {
            "name": "Seat_Base",
            "quantity": 1,
            "description": "Main padded sitting surface with slight contour",
            "geometric_properties": {
                "shape": "curved rectangular prism",
                "proportions": "width slightly greater than depth"
            }
        },
        {
            "name": "Armrest",
            "quantity": 2,
            "description": "Curved support structures for arms",
            "geometric_properties": {
                "shape": "curved bar",
                "identical": true,
                "mirrored_positions": "left and right of seat"
            }
        },
        {
            "name": "Star_Base_Prong",
            "quantity": 5,
            "description": "Radial support arms with wheels",
            "geometric_properties": {
                "shape": "elongated triangle",
                "identical": true,
                "radial_arrangement": "72 degrees apart"
            }
        }
    ],
    "spatial_relationships": [
        "Seat Base centered on central column",
        "Armrests symmetrically placed on left and right sides",
        "Five identical prongs arranged radially"
    ]
}

REQUIREMENTS:
1. Always specify exact quantities for each component
2. Mark identical components with "identical": true
3. Describe spatial arrangement for multiple components
4. Use precise measurements where possible
5. Specify if components are mirrored, radial, or linearly arranged
6. Group truly identical components together with a quantity
7. Break down nested identical components (e.g., chair legs within chairs)

Provide a similar breakdown for the given object, focusing on:
1. Exact quantities of each component
2. Identification of identical components
3. Precise geometric description
4. Spatial relationships between components
5. Nested identical components

Avoid mentioning colors, materials, or textures unless specifically relevant to the shape."""

        try:
            print("\nSending prompt to GPT-4...")
            response = self.client.chat.completions.create(
                model="gpt-4-0125-preview",
                messages=[
                    {"role": "system", "content": system_prompt + "\nIMPORTANT: Output ONLY valid JSON with no additional text."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                response_format={"type": "json_object"}  # Force JSON response
            )
            
            print("\nGPT-4 Response received. Attempting to parse JSON...")
            content = response.choices[0].message.content
            print(f"\nRaw response:\n{content}")
            
            try:
                # Find the first '{' and last '}'
                start_idx = content.find('{')
                end_idx = content.rfind('}')
                if start_idx != -1 and end_idx != -1:
                    content = content[start_idx:end_idx + 1]
                    print("\nExtracted JSON content:")
                    print(content)
                
                parsed = json.loads(content)
                print("\nJSON parsed successfully!")
                return parsed
                
            except json.JSONDecodeError as je:
                print(f"\nJSON parsing error: {str(je)}")
                print(f"Error occurred at position: {je.pos}")
                print(f"Line number: {je.lineno}")
                print(f"Column number: {je.colno}")
                print("\nProblematic content:")
                print(content)
                return None
                
        except Exception as e:
            print(f"\nAPI or other error: {str(e)}")
            print(f"Full error: {repr(e)}")
            return None