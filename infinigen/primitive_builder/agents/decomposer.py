import openai
from typing import Dict, List
import json

class SemanticDecomposer:
    def __init__(self, api_key: str):
        self.client = openai.OpenAI(api_key=api_key)
        
    def decompose(self, prompt: str) -> Dict:
        system_prompt = """You are a 3D modeling expert specializing in geometric decomposition. Break down objects into their core components, being EXPLICIT about:
        1. Quantities of identical components
        2. Their connections
        3. Geometric properties including curvature
        4. Spatial relationships

Example - Office Chair:
{
    "description": "A height-adjustable office chair with curved back support",
    "components": [
        {
            "name": "Seat_Base",
            "quantity": 1,
            "description": "Main padded sitting surface",
            "geometric_properties": {
                "shape": "curved_surface",
                "dimensions": {
                    "width": "medium",
                    "depth": "medium",
                    "height": "thin"
                },
                "curvature": {
                    "type": "ergonomic_curve",
                    "profile": "gentle",  # gentle, moderate, pronounced
                    "direction": "vertical"  # vertical, horizontal, both
                }
            },
            "connects_to": ["Backrest", "Armrests", "Legs"],
            "spatial_relationships": {
                "position": "central",
                "orientation": "horizontal"
            }
        },
        {
            "name": "Chair_Back",
            "quantity": 1,
            "description": "Supportive backrest",
            "geometric_properties": {
                "shape": "curved_component",
                "dimensions": {
                    "width": "medium",
                    "height": "tall",
                    "thickness": "medium"
                },
                "curvature": {
                    "type": "s_curve",  # straight, simple_curve, s_curve
                    "profile": "moderate",
                    "direction": "vertical"
                }
            },
            "connects_to": ["Seat_Base", "Armrests"]
        },
        {
            "name": "Chair_Leg",
            "quantity": 4,
            "description": "Support legs",
            "geometric_properties": {
                "shape": "curved_component",
                "dimensions": {
                    "length": "medium",
                    "thickness": "thin"
                },
                "curvature": {
                    "type": "simple_curve",  # or "straight" for vertical legs
                    "profile": "gentle",
                    "direction": "outward"
                }
            },
            "connects_to": ["Seat_Base", "Base_Support"]
        }
    ]
}

Curvature Types:
- straight: No curve, linear component
- simple_curve: Single direction curve
- s_curve: Complex curve with multiple directions
- ergonomic_curve: Specific for seating surfaces
- spiral: Helical or spiral curve
- compound_curve: Multiple connected curves

Profile Intensities:
- gentle: Slight, subtle curve
- moderate: Noticeable, balanced curve
- pronounced: Dramatic, strong curve

Curve Directions:
- vertical: Up/down curve
- horizontal: Left/right curve
- both: Combined curves
- outward: Away from center
- inward: Toward center
- spiral: Rotational curve

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
            print("\nSending prompt to GPT-4o...")
            response = self.client.chat.completions.create(
                model="gpt-4o-2024-08-06",
                messages=[
                    {"role": "system", "content": system_prompt + "\nIMPORTANT: Output ONLY valid JSON with no additional text."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                response_format={"type": "json_object"}  # Force JSON response
            )
            
            print("\nGPT-4o Response received. Attempting to parse JSON...")
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