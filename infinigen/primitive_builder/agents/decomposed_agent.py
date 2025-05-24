import openai
from typing import Dict, List, Any, Tuple
import json
from pathlib import Path
import subprocess
import sys
from .materials_agent import MaterialsAgent

class DecomposedPrimitiveGenerator:
    """An agent that generates primitive operations through semantic decomposition."""
    
    def __init__(self, api_key: str):
        self.client = openai.OpenAI(api_key=api_key)
        self.materials_agent = MaterialsAgent(api_key)
    
    def generate_primitives(self, prompt: str) -> List[Dict[str, Any]]:
        """Generate primitive operations directly from text description"""
        system_prompt = """You are a 3D modeling expert. Convert the following furniture description into a series of primitive operations.
        
        Available primitive operations:
        - build_prism_mesh: n (sides), r_min, r_max, height, tilt
        - build_convex_mesh: n (sides), height, tilt
        - build_cylinder_mesh: radius, height, segments
        - build_cone_mesh: radius, height, segments
        - build_sphere_mesh: radius, segments, rings
        - build_torus_mesh: major_radius, minor_radius, major_segments, minor_segments
        - build_box_mesh: width, depth, height
        - build_plane_mesh: width, depth
        - bezier_curve: anchors (list of [x,y,z]), vector_locations (list), resolution, to_mesh
        - align_bezier: anchors (list of [x,y,z]), axes (list), scale (list), vector_locations (list), resolution, to_mesh
        
        CRITICAL ORDERING RULES:
        1. Always start with ground-touching components (legs, base supports)
        2. Then build upward components that connect to them
        3. Finally add decorative elements (handles, trim)
        
        For each component, specify:
        1. The base shape using one of the primitive operations
        2. The exact parameters for that operation
        3. The transform (location, rotation, scale) to position it correctly
        
        Respond with a JSON array of operations, each containing:
        {
            "operation": "operation_name",
            "params": {param_name: value},
            "transform": {
                "location": [x, y, z],
                "rotation": [x, y, z],
                "scale": [x, y, z]
            }
        }
        
        Example for a chair leg:
        {
            "operation": "build_cylinder_mesh",
            "params": {
                "radius": 0.02,
                "height": 0.4,
                "segments": 16
            },
            "transform": {
                "location": [-0.2, 0.2, 0.2],
                "rotation": [0, 0, 0],
                "scale": [1, 1, 1]
            }
        }"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1
            )
            
            content = response.choices[0].message.content
            print(f"Debug - Raw response content: {content}")
            
            # Parse the response as JSON
            try:
                operations = json.loads(content)
                if isinstance(operations, list):
                    return operations
                elif isinstance(operations, dict) and "operations" in operations:
                    return operations["operations"]
                else:
                    print(f"Error: Unexpected response format: {type(operations)}")
                    return []
            except json.JSONDecodeError as e:
                print(f"Error parsing JSON response: {e}")
                print(f"Raw content: {content}")
                return []
                
        except Exception as e:
            print(f"Error in primitive generation: {e}")
            return []

    def generate(self, prompt: str, output_path: str = None) -> Tuple[str, str]:
        """Main generation pipeline"""
        print("\n=== Starting Generation Pipeline ===")
        print(f"Input Prompt: '{prompt}'")


        # Step 2: Generate Primitive Operations
        print("\n2. Generating Primitive Specifications...")
        primitive_specs = self.generate_primitives(prompt)
        if not primitive_specs:
            print("Error: No primitive specifications generated")
            return None, None
            
        print("Generated Specifications:")
        print(json.dumps(primitive_specs, indent=2))
        
        # Step 3: Assign Materials
        print("\n3. Assigning Materials...")
        components_with_materials = self.materials_agent.assign_materials(primitive_specs)
        
        if not components_with_materials:
            print("\nError: No components generated")
            return None, None

        # Step 4: Save JSON file
        print("\n4. Saving JSON file...")
        if output_path:
            json_path = Path(output_path).expanduser()
        else:
            json_path = Path.home() / "Desktop" / "generated-assets" / "primitives.json"
        
        json_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(json_path, 'w') as f:
                json.dump(components_with_materials, f, indent=2)
            print(f"JSON file saved at: {json_path}")
        except Exception as e:
            print(f"Error saving JSON file: {e}")
            return None, None

        # Step 5: Generate Blender file
        print("\n5. Generating Blender file...")
        try:
            # Get the project root directory
            project_root = Path(__file__).parent.parent.parent
            
            # Construct path to generate_blend_from_json.py
            blend_script = project_root / "primitive_calls" / "generate_blend_from_json.py"
            
            # Run the script using blender
            blend_cmd = [
                "blender",
                "--background",
                "--python",
                str(blend_script),
                "--",
                str(json_path)
            ]
            
            subprocess.run(blend_cmd, check=True)
            
            # Get the output blend file path
            blend_path = json_path.with_suffix('.blend')
            print(f"✓ Blender file generated at: {blend_path}")
            
            return str(json_path), str(blend_path)
            
        except subprocess.CalledProcessError as e:
            print(f"Error generating Blender file: {e}")
            return str(json_path), None
        except Exception as e:
            print(f"Unexpected error during Blender generation: {e}")
            return str(json_path), None 