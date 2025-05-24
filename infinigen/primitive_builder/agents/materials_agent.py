import openai
import json
from typing import Dict, List, Any
from pathlib import Path

class MaterialsAgent:
    def __init__(self, api_key: str):
        self.client = openai.OpenAI(api_key=api_key)
        
    def assign_materials(self, components: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Assign materials to components based on their names and roles"""
        try:
            # Create a prompt that includes component names and roles
            component_descriptions = []
            for i, comp in enumerate(components):
                name = comp.get('name', f'Component_{i}')
                operation = comp.get('operation', 'unknown')
                component_descriptions.append(f"{name} ({operation})")
            
            prompt = f"""Analyze these furniture components and assign appropriate materials:
            {', '.join(component_descriptions)}
            
            For each component, suggest a material that would be appropriate for its role.
            Consider:
            1. Structural integrity (e.g., legs need strong materials)
            2. Comfort (e.g., seating surfaces need comfortable materials)
            3. Aesthetics (e.g., visible surfaces need attractive materials)
            4. Common furniture materials (wood, metal, fabric, leather, etc.)
            
            Respond with a JSON array of material assignments, each containing:
            {{
                "component_name": "name of the component",
                "material": {{
                    "type": "material type (e.g., wood, metal, fabric)",
                    "color": "main color",
                    "finish": "surface finish (e.g., polished, matte, textured)"
                }}
            }}"""

            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a furniture design expert specializing in materials and finishes."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1
            )
            
            content = response.choices[0].message.content
            print(f"Debug - Raw material response: {content}")
            
            # Parse the response as JSON
            try:
                material_assignments = json.loads(content)
                if not isinstance(material_assignments, list):
                    print(f"Error: Expected list of material assignments, got {type(material_assignments)}")
                    return components
                
                # Create a mapping of component names to material assignments
                material_map = {assignment['component_name']: assignment['material'] 
                              for assignment in material_assignments}
                
                # Apply materials to components
                for comp in components:
                    name = comp.get('name', '')
                    if name in material_map:
                        comp['material'] = material_map[name]
                    else:
                        # If no specific material was assigned, use a default
                        comp['material'] = {
                            'type': 'wood',
                            'color': 'natural',
                            'finish': 'matte'
                        }
                
                return components
                
            except json.JSONDecodeError as e:
                print(f"Error parsing material JSON response: {e}")
                print(f"Raw content: {content}")
                # Apply default materials if parsing fails
                for comp in components:
                    comp['material'] = {
                        'type': 'wood',
                        'color': 'natural',
                        'finish': 'matte'
                    }
                return components
                
        except Exception as e:
            print(f"Error in material assignment: {e}")
            # Apply default materials if there's an error
            for comp in components:
                comp['material'] = {
                    'type': 'wood',
                    'color': 'natural',
                    'finish': 'matte'
                }
            return components 