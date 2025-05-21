import os
from pathlib import Path
import ast
from typing import Dict, List, Set

class ContextProvider:
    def __init__(self):
        self.infinigen_root = Path(__file__).parent.parent.parent
        self.assets_path = self.infinigen_root / "infinigen" / "assets" / "objects"
        
        # Define furniture categories and their paths
        self.furniture_factories = {
            "seating": [
                "seating/chairs/bar_chair.py",
                "seating/chairs/chair.py", 
                "seating/chairs/office_chair.py",
                "seating/bed.py",
                "seating/bedframe.py",
                "seating/mattress.py",
                "seating/pillow.py",
                "seating/sofa.py"
            ],
            "storage": [
                "shelves/single_cabinet.py",
                "shelves/cell_shelf.py",
                "shelves/kitchen_cabinet.py",
                "shelves/large_shelf.py",
                "shelves/simple_bookcase.py",
                "shelves/simple_desk.py",
                "shelves/triangle_shelf.py",
                "shelves/tv_stand.py",
                "shelves/kitchen_space.py",
                "shelves/kitchen_island.py"
            ],
            "tables": [
                "tables/table_dining.py",
                "tables/table_cocktail.py"
            ],
            "elements": [
                "elements/doors/glass_panel_door.py",
                "elements/doors/lite_door.py",
                "elements/doors/louver_door.py",
                "elements/doors/panel_door.py",
                "elements/rug.py"
            ]
        }
        
    def get_factory_context(self) -> str:
        """Analyze factory files to build context about available functions"""
        context = []
        
        print("\nScanning Factory Files...")
        context.append("""
AVAILABLE FURNITURE FACTORY IMPLEMENTATIONS:
The following patterns are extracted from actual furniture factories.
Study these to understand:
1. Available parameters and their typical values
2. Implementation patterns for different furniture types
3. Common geometric construction approaches
4. Standard dimensions and proportions
""")
        
        # Scan furniture factories by category
        for category, paths in self.furniture_factories.items():
            print(f"\nProcessing {category} factories...")
            context.append(f"\n{category.upper()} FACTORIES:")
            
            for factory_path in paths:
                full_path = self.assets_path / factory_path
                if full_path.exists():
                    print(f"  Reading: {factory_path}")
                    try:
                        with open(full_path, 'r') as f:
                            content = f.read()
                            tree = ast.parse(content)
                            
                        # Extract factory class and its methods
                        for node in ast.walk(tree):
                            if isinstance(node, ast.ClassDef) and node.name.endswith('Factory'):
                                context.append(f"\nFrom {factory_path}:")
                                context.append(f"Class: {node.name}")
                                
                                # Get initialization parameters
                                init_method = next((m for m in node.body if isinstance(m, ast.FunctionDef) and m.name == '__init__'), None)
                                if init_method:
                                    params = self._get_function_params(init_method)
                                    context.append("Constructor:" + params)
                                    print(f"    Found init params: {params}")
                                
                                # Look for create_asset and sample_parameters methods
                                for method_name in ['create_asset', 'sample_parameters']:
                                    method = next((m for m in node.body if isinstance(m, ast.FunctionDef) and m.name == method_name), None)
                                    if method:
                                        params = self._extract_parameters(method)
                                        if params:
                                            context.append(f"{method_name}:" + params)
                                            print(f"    Found {method_name} details")
                                
                                # Add key geometric operations
                                context.append("Key Operations:")
                                for line in content.split('\n'):
                                    if any(op in line for op in ['mesh.build_', 'draw.', 'bpy.ops']):
                                        context.append(f"  {line.strip()}")
                                
                    except Exception as e:
                        print(f"  Error processing {full_path}: {e}")
                else:
                    print(f"  Warning: File not found - {full_path}")
                        
        print("\nFactory context generation complete!")
        return "\n".join(context)
    
    def _get_function_params(self, node: ast.FunctionDef) -> str:
        """Extract function parameters with type hints"""
        params = []
        for arg in node.args.args:
            if arg.arg != 'self':
                if arg.annotation and isinstance(arg.annotation, ast.Name):
                    params.append(f"{arg.arg}: {arg.annotation.id}")
                else:
                    params.append(arg.arg)
        return f"({', '.join(params)})"
    
    def _extract_parameters(self, node: ast.FunctionDef) -> str:
        """Extract parameter definitions and implementations from factory methods"""
        params = []
        implementations = []
        
        # Look for parameter dictionaries
        for n in ast.walk(node):
            if isinstance(n, ast.Dict):
                for k, v in zip(n.keys, n.values):
                    if isinstance(k, ast.Constant):
                        params.append(f"- {k.value}")
                        
            # Look for assignments that might indicate parameters
            elif isinstance(n, ast.Assign):
                for target in n.targets:
                    if isinstance(target, ast.Name):
                        try:
                            if isinstance(n.value, ast.Constant):
                                implementations.append(f"- {target.id} = {n.value.value}")
                            elif isinstance(n.value, ast.Call):
                                if isinstance(n.value.func, ast.Name):
                                    if n.value.func.id in ['uniform', 'choice']:
                                        implementations.append(f"- {target.id} = {ast.unparse(n.value)}")
                        except:
                            continue
        
        result = []
        if params:
            result.append("Defined Parameters:" + "\n" + "\n".join(params))
        if implementations:
            result.append("Implementation Details:" + "\n" + "\n".join(implementations))
            
        return "\n" + "\n".join(result) if result else "" 