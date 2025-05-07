from typing import Dict, List

class PromptTemplates:
    """Templates for natural language prompts to generate assets"""
    
    @staticmethod
    def get_asset_templates() -> Dict[str, str]:
        """Get templates for different asset types"""
        return {
            'chair': """
            Create a {style} {type} chair with:
            - Material: {materials}
            - Size: {size}
            - Features: {features}
            - Additional details: {details}
            """,
            
            'table': """
            Generate a {style} {type} table with:
            - Material: {materials}
            - Size: {size}
            - Features: {features}
            - Additional details: {details}
            """,
            
            'lamp': """
            Make a {style} {type} lamp with:
            - Material: {materials}
            - Size: {size}
            - Features: {features}
            - Additional details: {details}
            """,
            
            'window': """
            Create a {style} window with:
            - Material: {materials}
            - Size: {size}
            - Features: {features}
            - Additional details: {details}
            """
        }
    
    @staticmethod
    def get_style_options() -> List[str]:
        """Get available style options"""
        return [
            'modern',
            'traditional',
            'minimalist',
            'industrial',
            'rustic',
            'contemporary'
        ]
    
    @staticmethod
    def get_material_options() -> List[str]:
        """Get available material options"""
        return [
            'wood',
            'metal',
            'glass',
            'fabric',
            'plastic',
            'ceramic'
        ]
    
    @staticmethod
    def get_size_options() -> List[str]:
        """Get available size options"""
        return [
            'small',
            'medium',
            'large'
        ]
    
    @staticmethod
    def get_feature_options() -> List[str]:
        """Get available feature options"""
        return [
            'adjustable',
            'foldable',
            'stackable',
            'portable',
            'customizable'
        ]
    
    @staticmethod
    def format_prompt(asset_type: str, **kwargs) -> str:
        """Format a prompt using the appropriate template"""
        templates = PromptTemplates.get_asset_templates()
        if asset_type not in templates:
            raise ValueError(f"Unknown asset type: {asset_type}")
            
        template = templates[asset_type]
        return template.format(**kwargs) 