import os
from pathlib import Path
import sys
import openai
from typing import Optional, Dict, List
import argparse
import json
import subprocess
from datetime import datetime

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

def generate_blend_file(json_path: Path) -> Optional[Path]:
    """Generate Blender file from JSON specifications"""
    try:
        # Find Blender executable
        blender_path = find_blender()
        if not blender_path:
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
    parser.add_argument('--output', type=str, help='Output path for the files', default=None)
    parser.add_argument('--json-only', action='store_true', help='Only generate JSON file, skip Blender file generation')
    args = parser.parse_args()

    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        sys.exit(1)

    generator = FurnitureGenerator(api_key, args.output)
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

if __name__ == "__main__":
    main() 