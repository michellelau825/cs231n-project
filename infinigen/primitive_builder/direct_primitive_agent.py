import os
from pathlib import Path
import sys
import openai
from typing import Optional, Dict, Any, List
import argparse
import json
import subprocess
import time
from importlib import import_module

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from primitive_builder.agents.classifier import FurnitureClassifier

class DirectPrimitiveGenerator:
    """
    A streamlined version of the primitive generator that directly maps text descriptions
    to Blender primitives without component decomposition.
    
    Design Decisions:
    1. Direct Mapping: Instead of decomposing into components, we map directly to primitives
       to reduce complexity and processing time.
    2. Simplified Structure: Operations are flat rather than hierarchical, making it easier
       to generate and process.
    3. Material Handling: Materials are applied at the object level rather than per-component.
    
    Limitations:
    1. Less Precise: Without component decomposition, the generated models may be less
       detailed or accurate.
    2. Limited Relationships: Spatial relationships between parts are simplified.
    3. Less Flexible: Harder to handle complex furniture with many interacting parts.
    """
    
    def __init__(self, api_key: str, output_path: Optional[str] = None):
        self.classifier = FurnitureClassifier(api_key)
        self.output_path = output_path
        self.metrics = {
            "execution_time": 0,
            "operation_count": 0,
            "success": False
        }

    def generate_primitives(self, prompt: str) -> Dict[str, Any]:
        """Generate primitive operations directly from the prompt"""
        system_prompt = """
        You are a 3D modeling expert. Convert the following furniture description into a series of primitive operations.
        Available operations (Blender's built-in primitives):
        - bpy.ops.mesh.primitive_cube_add: size, location, rotation, scale
        - bpy.ops.mesh.primitive_cylinder_add: radius, depth, location, rotation, scale
        - bpy.ops.mesh.primitive_uv_sphere_add: radius, location, rotation, scale
        - bpy.ops.mesh.primitive_cone_add: radius1, radius2, depth, location, rotation, scale
        - bpy.ops.mesh.primitive_torus_add: major_radius, minor_radius, location, rotation, scale
        - bpy.ops.mesh.primitive_plane_add: size, location, rotation, scale
        
        Respond with a JSON array of operations, each containing:
        1. operation: The name of the operation (e.g., "bpy.ops.mesh.primitive_cube_add")
        2. params: Parameters for the operation (e.g., {"size": 1.0, "location": [0, 0, 0]})
        
        Example format:
        [
            {
                "operation": "bpy.ops.mesh.primitive_cube_add",
                "params": {
                    "size": 1.2,
                    "location": [0, 0, 0.72],
                    "rotation": [0, 0, 0],
                    "scale": [1, 1, 1]
                }
            }
        ]
        
        Important: Each operation MUST have an "operation" field and a "params" field.
        Use only the built-in Blender primitives listed above.
        """
        
        client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1
        )
        
        try:
            specs = json.loads(response.choices[0].message.content)
            # Ensure specs is a list
            if not isinstance(specs, list):
                specs = [specs]
            
            # Validate and format each spec
            formatted_specs = []
            for spec in specs:
                if isinstance(spec, dict) and "operation" in spec:
                    formatted_specs.append({
                        "operation": spec["operation"],
                        "params": spec.get("params", {})
                    })
            
            self.metrics["operation_count"] = len(formatted_specs)
            return formatted_specs
        except json.JSONDecodeError:
            print("Error: Failed to parse primitive specifications")
            return []

    def generate(self, prompt: str) -> Optional[str]:
        start_time = time.time()
        print("\n=== Starting Direct Generation Pipeline ===")
        print(f"Input Prompt: '{prompt}'")
        
        # Step 1: Classification
        print("\n1. Running Classifier...")
        classification, explanation = self.classifier.classify(prompt)
        print(f"Classification Result: {classification}")
        print(f"Explanation: {explanation}")
        
        if classification == "not a furniture":
            print("Rejected: Generation stopped.")
            self.metrics["success"] = False
            return None

        # Step 2: Generate Primitives
        print("\n2. Generating Primitive Specifications...")
        primitive_specs = self.generate_primitives(prompt)
        print("Generated Specifications:")
        print(json.dumps(primitive_specs, indent=2))
        
        # Step 3: Save JSON file
        print("\n3. Saving JSON file...")
        output_path = Path(self.output_path).expanduser() if self.output_path else Path.home() / "Desktop" / "generated-assets" / "primitives.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(primitive_specs, f, indent=2)
        
        print(f"JSON file saved at: {output_path}")
        
        # Step 4: Generate Blender file
        print("\n4. Generating Blender file...")
        blend_script = project_root / "primitive_builder" / "generate_blend_from_json.py"
        blend_cmd = [
            "blender",
            "--background",
            "--python",
            str(blend_script),
            "--",
            str(output_path)
        ]
        
        try:
            subprocess.run(blend_cmd, check=True)
            print(f"✓ Blender file generated successfully")
            self.metrics["success"] = True
        except subprocess.CalledProcessError as e:
            print(f"✗ Error generating Blender file: {e}")
            self.metrics["success"] = False
            return None
        
        # Record metrics
        self.metrics["execution_time"] = time.time() - start_time
        for metric, value in self.metrics.items():
            print(f"METRIC: {metric}={value}")
        
        print("\n=== Generation Complete ===")
        return str(output_path)

def main():
    parser = argparse.ArgumentParser(description='Generate 3D furniture from text description using direct primitive mapping')
    parser.add_argument('prompt', type=str, help='Description of the furniture to generate')
    parser.add_argument('--output', type=str, help='Output path for the JSON file', default=None)
    args = parser.parse_args()

    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("Error: OPENAI_API_KEY environment variable not set")
        sys.exit(1)

    generator = DirectPrimitiveGenerator(api_key, args.output)
    output_path = generator.generate(args.prompt)
    
    if output_path:
        print(f"Generated files at: {output_path}")

if __name__ == "__main__":
    main() 