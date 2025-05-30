import os
from pathlib import Path
import sys
import openai
from typing import Optional, Dict, List
import argparse
import json
import subprocess
from datetime import datetime
import traceback
import numpy as np

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from primitive_builder.agents.classifier import FurnitureClassifier
from primitive_builder.agents.decomposer import SemanticDecomposer
from primitive_builder.agents.primitive_calls import PrimitiveGenerator
from primitive_builder.agents.blender_generator import BlenderGenerator
from primitive_builder.agents.validator import ComponentValidator

class FurnitureGenerator:
    def __init__(self, api_key: str, output_path: Optional[str] = None):
        self.classifier = FurnitureClassifier(api_key)
        self.decomposer = SemanticDecomposer(api_key)
        self.primitive_gen = PrimitiveGenerator(api_key)
        self.validator = ComponentValidator(api_key)
        self.blender_gen = BlenderGenerator()
        self.output_path = output_path

    def generate(self, prompt: str, pre_validate_path: Optional[str] = None, post_validate_path: Optional[str] = None, validate: bool = True) -> str:
        """Generate 3D furniture from text description"""
        print("\n=== Starting Generation Pipeline ===")
        print(f"Input Prompt: '{prompt}'")
        
        # Extract semantic relationships from components
        if "components" in components:
            for comp in components["components"]:
                # Add component name
                if "name" in comp:
                    required_components.add(comp["name"].lower())
                
                # Add geometric properties
                if "geometric_properties" in comp:
                    props = comp["geometric_properties"]
                    if "shape" in props:
                        required_properties.add(props["shape"].lower())
                    if "identical" in props and props["identical"]:
                        required_properties.add("identical_components")
                    if "mirrored_positions" in props:
                        required_properties.add("mirrored_components")
                    if "radial_arrangement" in props:
                        required_properties.add("radial_components")
                        
                # Add spatial relationships
                if "spatial_relationships" in components:
                    for rel in components["spatial_relationships"]:
                        if "connected" in rel.lower():
                            required_properties.add("connected_components")
                        if "centered" in rel.lower():
                            required_properties.add("centered_components")
                        if "symmetrical" in rel.lower():
                            required_properties.add("symmetrical_components")
                            
        return required_components, required_properties

    def validate_primitive_specs(self, primitive_specs: List[Dict], required_components: Set[str], required_properties: Set[str]) -> bool:
        """Validate that primitive specifications match semantic requirements"""
        found_components = set()
        found_properties = set()
        
        # Track component relationships
        component_positions = {}  # Track positions for symmetry/radial checks
        component_connections = set()  # Track connected components
        
        # Step 4: Save pre-validation file
        print("\n4. Creating Pre-validation Blender File...")
        pre_validate_blend = self.blender_gen.create_file(
            primitive_specs,
            custom_path=str(Path(pre_validate_path).expanduser()) if pre_validate_path else None
        )
        print(f"Pre-validation file created at: {pre_validate_blend}")
        
        # Step 5: Validate and save post-validation file if enabled
        if validate:
            print("\n5. Validating Component Connections...")
            validated_components = self.validator.validate_and_fix(primitive_specs)
            print("Validated Components:")
            print(json.dumps(validated_components, indent=2))
            
            print("\n6. Creating Post-validation Blender File...")
            post_validate_blend = self.blender_gen.create_file(
                validated_components,
                custom_path=str(Path(post_validate_path).expanduser()) if post_validate_path else None
            )
            print(f"Post-validation file created at: {post_validate_blend}")
            return post_validate_blend
        
        return pre_validate_blend

def apply_material(obj, material_info):
    """Apply material to object based on material_info"""
    try:
        print(f"\nApplying material to {obj.name}:")
        print(f"- Material path: {material_info['path']}")
        print(f"- Material params: {material_info.get('params', {})}")
        
        # Parse the material path
        *module_parts, function_name = material_info['path'].split('.')
        module_path = '.'.join(module_parts)
        
        # Add infinigen to Python path if needed
        infinigen_root = Path(__file__).parent.parent.parent
        if str(infinigen_root) not in sys.path:
            sys.path.append(str(infinigen_root))
        
        try:
            # Import the material module
            material_module = import_module(module_path)
            material_function = getattr(material_module, function_name)
            
            # Handle numbered components (e.g., Leg_1, Leg_2 -> leg)
            base_name = name.split('_')[0] if '_' in name else name
            found_components.add(base_name)
            
            # Check for curved elements
            if "bezier" in op or "curve" in op:
                found_properties.add("curved")
                # Check for complex shapes (heart, etc.)
                if "anchors" in params and len(params["anchors"]) >= 5:
                    found_properties.add("complex_shape")
                    
            # Track component positions for relationship validation
            if "location" in transform:
                loc = transform["location"]
                component_positions[base_name] = loc
                
            # Check for connected components
            if "connected" in op or any("connect" in p.lower() for p in params):
                component_connections.add(base_name)
                
        # Convert required components to lowercase for comparison
        required_components = {comp.lower() for comp in required_components}
        
        # Validate required components
        if not required_components.issubset(found_components):
            print(f"Missing components: {required_components - found_components}")
            return False
            
        # Validate required properties
        if "curved" in required_properties and "curved" not in found_properties:
            print("Missing curved elements")
            return False
            
        if "complex_shape" in required_properties and "complex_shape" not in found_properties:
            print("Missing complex shape elements")
            return False
            
        if "connected_components" in required_properties and len(component_connections) < 2:
            print("Components not properly connected")
            return False
            
        if "symmetrical_components" in required_properties:
            # Check for symmetry in component positions
            if not self._check_symmetry(component_positions):
                print("Components not properly symmetrical")
                return False
                
        if "radial_components" in required_properties:
            # Check for radial arrangement
            if not self._check_radial_arrangement(component_positions):
                print("Components not properly arranged radially")
                return False
                
        return True
        
    def _check_symmetry(self, positions: Dict[str, List[float]]) -> bool:
        """Check if components are arranged symmetrically"""
        if len(positions) < 2:
            return False
            
        # Check for mirror symmetry along any axis
        for comp1, pos1 in positions.items():
            for comp2, pos2 in positions.items():
                if comp1 != comp2:
                    # Check x-axis symmetry
                    if abs(pos1[0] + pos2[0]) < 0.1 and abs(pos1[1] - pos2[1]) < 0.1:
                        return True
                    # Check y-axis symmetry
                    if abs(pos1[1] + pos2[1]) < 0.1 and abs(pos1[0] - pos2[0]) < 0.1:
                        return True
        return False
        
    def _check_radial_arrangement(self, positions: Dict[str, List[float]]) -> bool:
        """Check if components are arranged radially"""
        if len(positions) < 3:
            return False
            
        # Calculate angles between components
        angles = []
        center = [0, 0, 0]
        for pos in positions.values():
            angle = np.arctan2(pos[1] - center[1], pos[0] - center[0])
            angles.append(angle)
            
        # Check if angles are roughly evenly distributed
        angles.sort()
        angle_diffs = [angles[i+1] - angles[i] for i in range(len(angles)-1)]
        angle_diffs.append(2*np.pi - (angles[-1] - angles[0]))
        
        # Check if differences are roughly equal
        mean_diff = np.mean(angle_diffs)
        return all(abs(diff - mean_diff) < 0.1 for diff in angle_diffs)

    def generate_json(self, prompt: str) -> Optional[Path]:
        """Generate JSON specifications without requiring Blender"""
        try:
            # Step 1: Classification
            classification, explanation = self.classifier.classify(prompt)
            
            if classification == "not a furniture":
                return None

            # Step 2: Semantic Decomposition
            components = self.decomposer.decompose(prompt)
            
            # Analyze semantic structure
            required_components, required_properties = self.analyze_semantic_structure(prompt, components)
            
            # Step 3: Generate Primitive Calls
            primitive_specs = self.primitive_gen.generate(components)
            
            if not primitive_specs:
                return None
                
            # Validate primitive specifications
            if not self.validate_primitive_specs(primitive_specs, required_components, required_properties):
                print("Validation failed. Retrying generation...")
                primitive_specs = self.primitive_gen.generate(components)
                if not primitive_specs or not self.validate_primitive_specs(primitive_specs, required_components, required_properties):
                    return None
                
            # Create output directory with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            if self.output_path:
                output_dir = Path(self.output_path).expanduser()
            else:
                output_dir = Path.home() / "Desktop" / "generated-assets"
            
            output_dir.mkdir(parents=True, exist_ok=True)
            json_path = output_dir / f"furniture_{timestamp}.json"
            
            # Save JSON file
            try:
                with open(json_path, 'w') as f:
                    json.dump(primitive_specs, f, indent=2)
                return json_path
            except Exception as e:
                return None
                
        except Exception as e:
            return None

def generate_blend_file(json_path: Path) -> Optional[Path]:
    """Generate Blender file from JSON specifications"""
    try:
        # Find Blender executable
        blender_path = find_blender()
        if not blender_path:
            return None
            
        # Get the project root directory
        project_root = Path(__file__).parent.parent
        
        # Construct path to generate_blend_from_json.py
        blend_script = project_root / "primitive_builder" / "generate_blend_from_json.py"
        
        if not blend_script.exists():
            return None
            
        # Run the script using blender
        blend_cmd = [
            str(blender_path),
            "--background",
            "--python",
            str(blend_script),
            "--",
            str(json_path)
        ]
        
        subprocess.run(blend_cmd, check=True)
        
        # Get the output blend file path
        blend_path = json_path.with_suffix('.blend')
        if blend_path.exists():
            return blend_path
        else:
            return None
            
    except subprocess.CalledProcessError:
        return None
    except Exception:
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
    parser.add_argument('pre_validate_path', type=str, help='Output path for pre-validation blend file')
    parser.add_argument('post_validate_path', type=str, help='Output path for post-validation blend file')
    parser.add_argument('--no-validate', action='store_true', help='Skip validation step')
    args = parser.parse_args()

    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        sys.exit(1)

    generator = FurnitureGenerator(api_key)
    blend_path = generator.generate(
        args.prompt, 
        pre_validate_path=args.pre_validate_path,
        post_validate_path=args.post_validate_path,
        validate=not args.no_validate
    )
    
    if blend_path:
        print(f"\nFinal Blender file: {blend_path}")

if __name__ == "__main__":
    main() 