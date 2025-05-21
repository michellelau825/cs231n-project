import openai
import json
from typing import Dict, List
from pathlib import Path

class MaterialsAgent:
    def __init__(self, api_key: str):
        self.client = openai.OpenAI(api_key=api_key)
        
    def assign_materials(self, components: List[Dict]) -> List[Dict]:
        """Assign appropriate materials to each component"""
        
        system_prompt = """You are a materials expert. Analyze the components and output a JSON with appropriate material assignments for each furniture component.

        AVAILABLE MATERIALS:
        1. From infinigen.assets.materials.metal.brushed_metal:
           - Used for modern metallic finishes
           - Parameters: scale (float), base_color (optional [r,g,b,1.0]), seed (optional float)
           - Example: scale=1.0, base_color=[0.8, 0.8, 0.8, 1.0], seed=42.0

        Output format example:
        {
            "Table_Leg_1": {
                "material_path": "infinigen.assets.materials.metal.brushed_metal",
                "material_params": {
                    "scale": 1.0,
                    "base_color": [0.8, 0.8, 0.8, 1.0],
                    "seed": 42.0
                },
                "selection": null,
                "reason": "Modern metallic finish suitable for table support"
            }
        }"""

        try:
            print("\n=== Assigning Materials to Components ===")
            response = self.client.chat.completions.create(
                model="gpt-4-0125-preview",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Please analyze these components and provide a JSON response with material assignments: {json.dumps(components)}"}
                ],
                temperature=0.2,
                response_format={"type": "json_object"}
            )
            
            material_assignments = json.loads(response.choices[0].message.content)
            
            for comp in components:
                if comp['name'] in material_assignments:
                    material_info = material_assignments[comp['name']]
                    
                    # Store material info as strings and parameters
                    comp['material'] = {
                        'path': material_info['material_path'],
                        'params': material_info['material_params'],
                        'selection': material_info.get('selection', None)
                    }
                    
                    print(f"\nAssigned material to {comp['name']}:")
                    print(f"- Material: {material_info['material_path']}")
                    print(f"- Params: {material_info['material_params']}")
                    print(f"- Reason: {material_info['reason']}")
            
            return components
            
        except Exception as e:
            print(f"Error assigning materials: {e}")
            return components 