import os
from pathlib import Path
import sys
import openai
from typing import Optional
import argparse
import json
import subprocess
from importlib import import_module

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

    def generate(self, prompt: str) -> Optional[str]:
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
            
            # Create material
            material = material_function(**material_info.get('params', {}))
            
            # Apply to object
            if obj.data.materials:
                obj.data.materials[0] = material
            else:
                obj.data.materials.append(material)
            
            print(f"✓ Successfully applied {function_name} material to {obj.name}")
            return True
            
        except ImportError as e:
            print(f"✗ Failed to import material module: {e}")
            print(f"  Module path attempted: {module_path}")
            return False
        except AttributeError as e:
            print(f"✗ Failed to find material function: {e}")
            print(f"  Function attempted: {function_name}")
            return False
            
    except Exception as e:
        print(f"✗ Error applying material: {e}")
        return False

def create_mesh(component):
    """Create mesh from component and apply material"""
    try:
        # Create the mesh (your existing code)
        obj = None  # Replace with your actual mesh creation code
        
        # Apply material if specified
        if 'material' in component:
            success = apply_material(obj, component['material'])
            if not success:
                print(f"✗ Failed to apply material to {component['name']}")
        else:
            print(f"! No material specified for {component['name']}")
        
        return obj
        
    except Exception as e:
        print(f"✗ Error creating mesh for {component.get('name', 'unknown')}: {e}")
        return None

def create_object(components):
    """Create full object from components"""
    try:
        print("\n=== Creating Object from Components ===")
        created_objects = []
        
        for component in components:
            obj = create_mesh(component)
            if obj:
                created_objects.append(obj)
                print(f"✓ Created {component['name']}")
            else:
                print(f"✗ Failed to create {component['name']}")
        
        if created_objects:
            # Join objects if needed
            if len(created_objects) > 1:
                bpy.context.view_layer.objects.active = created_objects[0]
                for obj in created_objects[1:]:
                    obj.select_set(True)
                bpy.ops.object.join()
            
            print(f"\n✓ Successfully created object with {len(components)} components")
            return created_objects[0]
        else:
            print("\n✗ Failed to create any components")
            return None
            
    except Exception as e:
        print(f"\n✗ Error creating object: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(description='Generate 3D furniture from text description')
    parser.add_argument('prompt', type=str, help='Description of the furniture to generate')
    parser.add_argument('--output', type=str, help='Output path for the JSON file', default=None)
    args = parser.parse_args()

    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("Error: OPENAI_API_KEY environment variable not set")
        sys.exit(1)

    generator = FurnitureGenerator(api_key, args.output)
    output_path = generator.generate(args.prompt)
    
    if output_path:
        print(f"Generated files at: {output_path}")

if __name__ == "__main__":
    main() 