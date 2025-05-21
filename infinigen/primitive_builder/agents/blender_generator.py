import bpy
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional
import json
from infinigen.assets.utils import draw, mesh, object
import importlib
from importlib import import_module
from infinigen.core import surface

def apply_material(obj, material_info):
    """Apply material using the module's apply() function"""
    try:
        # Import the material module dynamically
        module_path = material_info['path']
        print(f"Importing material from: {module_path}")
        
        # Import module
        module = import_module(module_path)
        
        # Call the module's apply() function with parameters
        module.apply(
            obj, 
            selection=material_info.get('selection'),
            **material_info.get('params', {})
        )
        print(f"✓ Successfully applied material to {obj.name}")
        
    except Exception as e:
        print(f"✗ Failed to apply material to {obj.name}: {e}")
        print(f"  Material info: {material_info}")

class BlenderGenerator:
    def __init__(self):
        # Default output directory if no custom path provided
        self.output_dir = Path.home() / "Desktop" / "generated-assets"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        print(f"BlenderGenerator initialized. Output directory: {self.output_dir}")
        
    def sample_distribution(self, dist_spec: Dict) -> float:
        """Sample value from distribution specification"""
        if isinstance(dist_spec, (int, float)):
            return dist_spec
            
        dist_type = dist_spec["distribution"]
        params = dist_spec["params"]
        
        if dist_type == "uniform":
            return np.random.uniform(params["min"], params["max"])
        elif dist_type == "normal":
            return np.random.normal(params["mean"], params["std"])
        elif dist_type == "log_uniform":
            return np.exp(np.random.uniform(np.log(params["low"]), 
                                          np.log(params["high"])))
                                          
    def sample_vector_distribution(self, dist_spec: Dict) -> List[float]:
        """Sample vector from distribution specification"""
        if isinstance(dist_spec, list):
            return dist_spec
            
        return [self.sample_distribution(dist_spec) for _ in range(3)]
            
    def create_file(self, components: List[Dict], custom_path: Optional[str] = None) -> str:
        print("\n=== Starting Blender File Creation ===")
        print(f"Received {len(components)} components")
        
        # Clear scene
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete()
        print("Scene cleared")
        
        all_objects = []
        
        # Process each component
        for component in components:
            component_name = component.get('name', 'unnamed')
            operations = component.get('operations', [])
            print(f"\nProcessing component '{component_name}' with {len(operations)} operations")
            
            component_objects = []
            
            # Process each operation for this component
            for op_spec in operations:
                operation = op_spec.get('operation', '')
                params = op_spec.get('params', {})
                transform = op_spec.get('transform', {})
                
                try:
                    if operation.startswith('bpy.ops'):
                        # Handle Blender operators
                        eval(operation)(**params)
                        continue
                    else:
                        module_name, func_name = operation.split('.')
                        if module_name == 'draw':
                            module = draw
                        elif module_name == 'mesh':
                            module = mesh
                        elif module_name == 'object':
                            module = object
                            
                        func = getattr(module, func_name)
                        result = func(**params)
                        
                        if isinstance(result, bpy.types.Object):
                            result_obj = result
                        else:
                            mesh_obj = bpy.data.objects.new(component_name, result)
                            bpy.context.scene.collection.objects.link(mesh_obj)
                            result_obj = mesh_obj
                        
                        # Apply transforms
                        if transform:
                            if 'location' in transform:
                                result_obj.location = transform['location']
                            if 'rotation' in transform:
                                result_obj.rotation_euler = transform['rotation']
                            if 'scale' in transform:
                                result_obj.scale = transform['scale']
                        
                        # Apply material if specified
                        if 'material' in component:
                            apply_material(result_obj, component['material'])
                        
                        component_objects.append(result_obj)
                    
                except Exception as e:
                    print(f"Error in operation: {str(e)}")
                    continue
            
            # Join all objects for this component
            if len(component_objects) > 1:
                bpy.ops.object.select_all(action='DESELECT')
                for obj in component_objects:
                    obj.select_set(True)
                bpy.context.view_layer.objects.active = component_objects[0]
                bpy.ops.object.join()
                all_objects.append(component_objects[0])
            elif component_objects:
                all_objects.append(component_objects[0])
        
        # Save file
        if custom_path:
            output_path = Path(custom_path).expanduser()
            output_path.parent.mkdir(parents=True, exist_ok=True)
        else:
            output_path = self.output_dir / "generated_object.blend"
        
        print(f"Saving to: {output_path}")
        bpy.ops.wm.save_as_mainfile(filepath=str(output_path))
        return str(output_path)