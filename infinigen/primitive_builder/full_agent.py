import os
from pathlib import Path
import sys
import openai
from typing import Optional, Dict, List
import argparse
import json
import bpy
from importlib import import_module

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
        
        # Step 1: Classification
        print("\n1. Running Classifier...")
        classification, explanation = self.classifier.classify(prompt)
        print(f"Classification Result: {classification}")
        print(f"Explanation: {explanation}")
        
        if classification == "does not pass":
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
        print("Generated Specifications:")
        print(json.dumps(primitive_specs, indent=2))
        
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
            
            # Save validated components to JSON file
            validated_json_path = Path(post_validate_path).expanduser()
            validated_json_path.parent.mkdir(parents=True, exist_ok=True)
            validated_json_path = validated_json_path.parent / "validated_components.json"
            with open(validated_json_path, 'w') as f:
                json.dump(validated_components, f, indent=2)
            print(f"Saved validated components to: {validated_json_path}")
            
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
    parser.add_argument('pre_validate_path', type=str, help='Output path for pre-validation blend file')
    parser.add_argument('post_validate_path', type=str, help='Output path for post-validation blend file')
    parser.add_argument('--no-validate', action='store_true', help='Skip validation step')
    args = parser.parse_args()

    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("Error: OPENAI_API_KEY environment variable not set")
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