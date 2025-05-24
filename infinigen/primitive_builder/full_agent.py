import os
from pathlib import Path
import sys
import openai
from typing import Optional, Dict, List
import argparse
import json
import subprocess
<<<<<<< Updated upstream
from importlib import import_module
=======
from datetime import datetime
>>>>>>> Stashed changes

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from primitive_builder.agents.classifier import FurnitureClassifier
from primitive_builder.agents.decomposer import SemanticDecomposer
from primitive_builder.agents.primitive_calls import PrimitiveGenerator

class FurnitureGenerator:
    def __init__(self, api_key: str, output_path: Optional[str] = None):
        self.classifier = FurnitureClassifier(api_key)
        self.decomposer = SemanticDecomposer(api_key)
        self.primitive_gen = PrimitiveGenerator(api_key)
        self.output_path = output_path

    def generate_json(self, prompt: str) -> Optional[Path]:
        """Generate JSON specifications without requiring Blender"""
        print("\n=== Starting Generation Pipeline ===")
        print(f"Input Prompt: '{prompt}'")
        
        # Step 1: Classification
        print("\n1. Running Classifier...")
        classification, explanation = self.classifier.classify(prompt)
        print(f"Classification Result: {classification}")
        print(f"Explanation: {explanation}")
        
        if classification == "not a furniture":
            print("Rejected: Generation stopped.")
            return None

        # Step 2: Semantic Decomposition
        print("\n2. Running Semantic Decomposition...")
        components = self.decomposer.decompose(prompt)
        print("Decomposed Components:")
        print(json.dumps(components, indent=2))
        
        # Step 3: Generate Primitive Calls
        print("\n3. Generating Primitive Specifications...")
        primitive_specs = self.primitive_gen.generate(components)
        
<<<<<<< Updated upstream
        # Convert to the expected format
        formatted_specs = []
        for component in primitive_specs:
            if isinstance(component, dict) and "operations" in component:
                for op in component["operations"]:
                    if isinstance(op, dict) and "operation" in op:
                        # Convert mesh.build_cylinder_mesh to build_cylinder_mesh
                        op_name = op["operation"].split(".")[-1]
                        formatted_specs.append({
                            "operation": op_name,
                            "params": op.get("params", {}),
                            "transform": op.get("transform", {})
                        })
        
        print("Generated Specifications:")
        print(json.dumps(formatted_specs, indent=2))
        
        # Step 4: Save JSON file
        print("\n4. Saving JSON file...")
        output_path = Path(self.output_path).expanduser() if self.output_path else Path.home() / "Desktop" / "generated-assets" / "primitives.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        print(f"Debug - formatted_specs before saving: {formatted_specs}")
        print(f"Debug - formatted_specs type: {type(formatted_specs)}")
        print(f"Debug - formatted_specs length: {len(formatted_specs)}")
        
        try:
            with open(output_path, 'w') as f:
                json.dump(formatted_specs, f, indent=2)
            print(f"Debug - File size after writing: {output_path.stat().st_size} bytes")
        except Exception as e:
            print(f"Debug - Error writing file: {str(e)}")
        
        print(f"JSON file saved at: {output_path}")
        
        # Step 5: Generate Blender file
        print("\n5. Generating Blender file...")
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
        except subprocess.CalledProcessError as e:
            print(f"✗ Error generating Blender file: {e}")
            return None
        
        print("\n=== Generation Complete ===")
        return str(output_path)
=======
        # Create output directory with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = Path(self.output_path).expanduser() if self.output_path else Path.home() / "Desktop" / "generated-assets"
        output_dir = output_dir.resolve()  # Resolve any symlinks or relative paths
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate unique filename with timestamp
        base_name = f"furniture_{timestamp}"
        json_path = output_dir / f"{base_name}.json"
        
        # Save JSON file
        with open(json_path, "w") as f:
            json.dump(primitive_specs, f, indent=2)
        print(f"\nJSON specifications saved to: {json_path}")
        
        return json_path
>>>>>>> Stashed changes

def generate_blend_file(json_path: Path) -> Optional[Path]:
    """Generate Blender file from JSON specifications"""
    try:
        # Find Blender executable
        blender_path = find_blender()
        if not blender_path:
            print("Error: Could not find Blender executable")
            return None

        # Construct the command
        script_path = project_root / "primitive_builder" / "generate_blend_from_json.py"
        cmd = [
            str(blender_path),
            "--background",
            "--python",
            str(script_path),
            "--",
            str(json_path)
        ]

        # Run the command
        print(f"Running command: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            # The blend file will be in the same directory as the JSON file
            blend_path = json_path.with_suffix('.blend')
            if blend_path.exists():
                return blend_path
        else:
            print(f"Error running Blender: {result.stderr}")
            print(f"Command output: {result.stdout}")
        
        return None

    except Exception as e:
        print(f"Error generating Blender file: {e}")
        return None

def find_blender() -> Optional[Path]:
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

def main():
    parser = argparse.ArgumentParser(description='Generate 3D furniture from text description')
    parser.add_argument('prompt', type=str, help='Description of the furniture to generate')
<<<<<<< Updated upstream
    parser.add_argument('--output', type=str, help='Output path for the JSON file', default=None)
=======
    parser.add_argument('--output', type=str, help='Output path for the files', default=None)
    parser.add_argument('--json-only', action='store_true', help='Only generate JSON file, skip Blender file generation')
>>>>>>> Stashed changes
    args = parser.parse_args()

    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("Error: OPENAI_API_KEY environment variable not set")
        sys.exit(1)

    generator = FurnitureGenerator(api_key, args.output)
<<<<<<< Updated upstream
    output_path = generator.generate(args.prompt)
    
    if output_path:
        print(f"Generated files at: {output_path}")
=======
    json_path = generator.generate_json(args.prompt)
    
    if json_path:
        if not args.json_only:
            print("\nGenerating Blender file...")
            blend_path = generate_blend_file(json_path)
            if blend_path:
                print(f"Blender file created at: {blend_path}")
            else:
                print("Failed to generate Blender file")
        print("\nGeneration Complete!")
    else:
        print("\nGeneration Failed!")
>>>>>>> Stashed changes

if __name__ == "__main__":
    main() 