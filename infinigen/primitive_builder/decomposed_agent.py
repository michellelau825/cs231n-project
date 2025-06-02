import sys
from pathlib import Path
from typing import Optional

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

import openai
from typing import Dict, List, Any, Tuple
import json
import subprocess
import os
import argparse
from agents.classifier import FurnitureClassifier
from agents.materials_agent import MaterialsAgent

def find_blender() -> Path:
    """Find Blender executable on the system"""
    # Common Blender installation paths
    possible_paths = [
        # macOS
        Path("/Applications/Blender.app/Contents/MacOS/Blender"),
        # Linux
        Path("/usr/bin/blender"),
        Path("/usr/local/bin/blender"),
        # Windows
        Path("C:/Program Files/Blender Foundation/Blender 3.x/blender.exe"),
        Path("C:/Program Files/Blender Foundation/Blender 4.x/blender.exe"),
    ]

    # Check if blender is in PATH
    try:
        blender_path = subprocess.check_output(["which", "blender"], text=True).strip()
        if blender_path:
            return Path(blender_path)
    except subprocess.CalledProcessError:
        pass

    # Check common installation paths
    for path in possible_paths:
        if path.exists():
            return path

    return None

def generate_blend_file(json_path: Path) -> Optional[Path]:
    """Generate Blender file from JSON specifications"""
    try:
        
        # Find Blender executable
        blender_path = find_blender()
        print(f"4. Blender path: {blender_path}")
        if not blender_path:
            print("Error: Could not find Blender executable")
            return None

        # Construct the command
        script_path = project_root / "infinigen" / "primitive_builder" / "generate_blend_from_json.py"
        print(f"5. Script path exists: {script_path.exists()}")
        print(f"6. Script path absolute: {script_path.absolute()}")
        
        cmd = [
            str(blender_path),
            "--background",
            "--python",
            str(script_path),
            "--",
            str(json_path)
        ]

        # Run the command
        print(f"\n7. Running command: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        print(f"8. Command return code: {result.returncode}")
        if result.stderr:
            print(f"9. Command stderr:\n{result.stderr}")
        if result.stdout:
            print(f"10. Command stdout:\n{result.stdout}")
        
        if result.returncode == 0:
            # The blend file will be in the same directory as the JSON file
            blend_path = json_path.with_suffix('.blend')
            print(f"11. Expected blend path: {blend_path}")
            print(f"12. Blend file exists: {blend_path.exists()}")
            if blend_path.exists():
                return blend_path
        else:
            print(f"Error running Blender: {result.stderr}")
            print(f"Command output: {result.stdout}")
        
        return None

    except Exception as e:
        print(f"Error generating Blender file: {e}")
        import traceback
        print("Full traceback:")
        print(traceback.format_exc())
        return None

class DecomposedPrimitiveGenerator:
    """An agent that generates primitive operations through semantic decomposition."""
    
    def __init__(self, api_key: str):
        self.client = openai.OpenAI(api_key=api_key)
        self.classifier = FurnitureClassifier(api_key)
        self.materials_agent = MaterialsAgent(api_key)
        
    def classify(self, prompt: str) -> Tuple[str, str]:
        """First step: Classify if the prompt is valid furniture"""
        return self.classifier.classify(prompt)

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
        1. A unique name for the component (e.g., "Leg_1", "Seat", "Backrest")
        2. The base shape using one of the primitive operations
        3. The exact parameters for that operation
        4. The transform (location, rotation, scale) to position it correctly
        
        Respond with a JSON array of components, each containing:
        {
            "name": "component_name",
            "operations": [
                {
                    "operation": "operation_name",
                    "params": {param_name: value},
                    "transform": {
                        "location": [x, y, z],
                        "rotation": [x, y, z],
                        "scale": [x, y, z]
                    }
                }
            ]
        }
        
        Example for a chair leg:
        {
            "name": "Leg_1",
            "operations": [
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
                }
            ]
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
        
        # Step 1: Classification
        print("\n1. Running Classifier...")
        classification, explanation = self.classify(prompt)
        print(f"Classification Result: {classification}")
        print(f"Explanation: {explanation}")
        
        if classification == "not a furniture":
            print("Rejected: Generation stopped.")
            return None, None

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
            # If output path ends with .blend, replace it with .json
            output_path = str(Path(output_path).with_suffix('.json'))
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
        blend_path = generate_blend_file(json_path)
        if blend_path:
            print(f"✓ Blender file generated at: {blend_path}")
            return str(json_path), str(blend_path)
        else:
            print("Failed to generate Blender file")
            return str(json_path), None

def main():
    parser = argparse.ArgumentParser(description='Generate 3D furniture from text description using decomposed agent')
    parser.add_argument('prompt', type=str, help='Description of the furniture to generate')
    parser.add_argument('--output', type=str, help='Output path for the files', default=None)
    parser.add_argument('--json-only', action='store_true', help='Only generate JSON file, skip Blender file generation')
    args = parser.parse_args()

    # Get API key from environment variable
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("Error: OPENAI_API_KEY environment variable not set")
        print("Please set it using: export OPENAI_API_KEY='your-api-key'")
        sys.exit(1)

    generator = DecomposedPrimitiveGenerator(api_key)
    json_path, blend_path = generator.generate(args.prompt, args.output)
    
    if json_path:
        if not args.json_only and blend_path:
            print(f"\nGeneration Complete!")
            print(f"JSON file: {json_path}")
            print(f"Blender file: {blend_path}")
        else:
            print(f"\nGeneration Complete!")
            print(f"JSON file: {json_path}")
    else:
        print("\nGeneration Failed!")

if __name__ == "__main__":
    main() 