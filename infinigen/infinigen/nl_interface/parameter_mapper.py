import numpy as np
from typing import Dict, Any, Tuple

from infinigen.assets.objects.seating.chairs.bar_chair import BarChairFactory
from infinigen.assets.objects.tables.dining_table import TableDiningFactory
from infinigen.assets.objects.lamp.lamp import LampFactory
from infinigen.assets.objects.windows.window import WindowFactory
from infinigen.assets.material_assignments import AssetList
from infinigen.core.util.math import FixedSeed

class AssetParameterMapper:
    def __init__(self):
        # Core asset factories
        self.factories = {
            'chair': BarChairFactory,
            'table': TableDiningFactory,
            'lamp': LampFactory,
            'window': WindowFactory,
        }
        
        # Material mappings
        self.materials = {
            'wood': ['wood', 'oak', 'mahogany', 'pine'],
            'metal': ['metal', 'steel', 'aluminum', 'brass'],
            'glass': ['glass', 'transparent', 'clear'],
            'fabric': ['fabric', 'cloth', 'textile', 'leather'],
            'plastic': ['plastic', 'synthetic'],
            'ceramic': ['ceramic', 'porcelain', 'clay']
        }
        
        # Style configurations
        self.styles = {
            'modern': {'leg_style': 'straight', 'material': 'metal'},
            'traditional': {'leg_style': 'single_stand', 'material': 'wood'},
            'minimalist': {'leg_style': 'straight', 'material': 'metal'}
        }
        
        # Size configurations
        self.sizes = {
            'small': 0.8,
            'medium': 1.0,
            'large': 1.2
        }

    def parse_prompt(self, prompt: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Convert natural language to structured parameters"""
        # Extract basic information
        asset_type = self._extract_asset_type(prompt)
        style = self._extract_style(prompt)
        materials = self._extract_materials(prompt)
        size = self._extract_size(prompt)
        
        # Create factory parameters
        factory_params = {
            'asset_type': asset_type,
            'style': style,
            'size': size,
            **self.styles[style]
        }
        
        # Create material parameters
        material_params = {
            material: True for material in materials
        }
        
        return factory_params, material_params

    def _extract_asset_type(self, prompt: str) -> str:
        """Extract asset type from prompt"""
        for asset_type in self.factories:
            if asset_type in prompt.lower():
                return asset_type
        raise ValueError(f"No supported asset type found in prompt: {prompt}")

    def _extract_style(self, prompt: str) -> str:
        """Extract style from prompt"""
        for style in self.styles:
            if style in prompt.lower():
                return style
        return 'modern'  # Default style

    def _extract_materials(self, prompt: str) -> list:
        """Extract materials from prompt"""
        materials = []
        for material, keywords in self.materials.items():
            if any(kw in prompt.lower() for kw in keywords):
                materials.append(material)
        return materials or ['wood']  # Default material

    def _extract_size(self, prompt: str) -> str:
        """Extract size from prompt"""
        for size in self.sizes:
            if size in prompt.lower():
                return size
        return 'medium'  # Default size 