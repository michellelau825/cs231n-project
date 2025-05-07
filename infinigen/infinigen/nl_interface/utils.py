from typing import Dict, Any, List
import re

def extract_asset_type(prompt: str) -> str:
    """Extract the asset type from a prompt"""
    asset_types = ['chair', 'table', 'lamp', 'window']
    for asset_type in asset_types:
        if asset_type in prompt.lower():
            return asset_type
    return None

def extract_materials(prompt: str) -> List[str]:
    """Extract materials from a prompt"""
    material_keywords = {
        'wood': ['wood', 'oak', 'mahogany', 'pine'],
        'metal': ['metal', 'steel', 'aluminum', 'brass'],
        'glass': ['glass', 'transparent', 'clear'],
        'fabric': ['fabric', 'cloth', 'textile', 'leather'],
        'plastic': ['plastic', 'synthetic'],
        'ceramic': ['ceramic', 'porcelain', 'clay']
    }
    
    materials = []
    for material, keywords in material_keywords.items():
        if any(keyword in prompt.lower() for keyword in keywords):
            materials.append(material)
    return materials

def extract_style(prompt: str) -> str:
    """Extract style from a prompt"""
    styles = ['modern', 'traditional', 'minimalist', 'industrial', 'rustic', 'contemporary']
    for style in styles:
        if style in prompt.lower():
            return style
    return 'modern'  # Default style

def extract_size(prompt: str) -> str:
    """Extract size from a prompt"""
    sizes = ['small', 'medium', 'large']
    for size in sizes:
        if size in prompt.lower():
            return size
    return 'medium'  # Default size

def extract_features(prompt: str) -> List[str]:
    """Extract features from a prompt"""
    features = ['adjustable', 'foldable', 'stackable', 'portable', 'customizable']
    found_features = []
    for feature in features:
        if feature in prompt.lower():
            found_features.append(feature)
    return found_features

def parse_prompt(prompt: str) -> Dict[str, Any]:
    """Parse a natural language prompt into structured data"""
    return {
        'asset_type': extract_asset_type(prompt),
        'style': extract_style(prompt),
        'materials': extract_materials(prompt),
        'size': extract_size(prompt),
        'features': extract_features(prompt)
    }

def validate_prompt(prompt: str) -> bool:
    """Validate if a prompt contains all necessary information"""
    parsed = parse_prompt(prompt)
    return all([
        parsed['asset_type'],
        parsed['style'],
        parsed['materials'],
        parsed['size']
    ])

def format_prompt_for_llm(prompt: str) -> str:
    """Format a prompt for LLM processing"""
    # Add any necessary formatting or preprocessing here
    return prompt.strip() 