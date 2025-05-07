import numpy as np
from typing import Dict, Any

import bpy
from infinigen.core.util.math import FixedSeed
from infinigen.assets.material_assignments import AssetList
from infinigen.core import surface

from .parameter_mapper import AssetParameterMapper

class InfinigenNLInterface:
    def __init__(self):
        self.parameter_mapper = AssetParameterMapper()
        
    def generate_asset(self, prompt: str) -> Dict[str, Any]:
        """Generate asset from natural language prompt"""
        # Parse prompt into parameters
        factory_params, material_params = self.parameter_mapper.parse_prompt(prompt)
        
        # Create and configure factory
        factory = self._create_factory(factory_params)
        
        # Generate asset
        with FixedSeed(np.random.randint(1e9)):
            # Create the asset
            obj = factory.create_asset()
            
            # Finalize the asset (apply wear and tear if specified)
            factory.finalize_assets([obj])
            
            # Position the asset
            obj.location = (0, 0, 0)
            
            # Return result
            return {
                'type': factory_params['asset_type'],
                'style': factory_params['style'],
                'materials': list(material_params.keys()),
                'size': factory_params['size'],
                'object': obj
            }

    def _create_factory(self, params: Dict[str, Any]):
        """Create appropriate factory instance"""
        # Get the factory class
        factory_class = self.parameter_mapper.factories[params['asset_type']]
        
        # Create factory instance with seed
        factory = factory_class(
            factory_seed=np.random.randint(1e9),
            dimensions=None  # Let the factory decide the dimensions
        )
        
        return factory

    def _apply_materials(self, asset: Any, material_params: Dict[str, Any]) -> None:
        """Apply materials to asset"""
        material_assignments = AssetList[asset.__class__.__name__]()
        
        for material_type, enabled in material_params.items():
            if enabled and material_type in material_assignments:
                material = material_assignments[material_type].assign_material()
                self._apply_material_to_parts(asset, material)

    def _apply_material_to_parts(self, asset: Any, material: Any) -> None:
        """Apply material to asset parts"""
        if hasattr(asset, 'active_material'):
            asset.active_material = surface.shaderfunc_to_material(material)
        elif hasattr(asset, 'children'):
            for child in asset.children:
                if hasattr(child, 'active_material'):
                    child.active_material = surface.shaderfunc_to_material(material) 