import json
import os
from pathlib import Path
from typing import List, Dict
import argparse
from full_agent import FurnitureGenerator

class BatchGenerator:
    def __init__(self, api_key: str):
        self.generator = FurnitureGenerator(api_key)
        
    def process_file(self, input_file: str):
        """Process a file containing multiple furniture prompts"""
        file_path = Path(input_file)
        
        if file_path.suffix == '.json':
            with open(file_path, 'r') as f:
                prompts = json.load(f)
        elif file_path.suffix == '.txt':
            prompts = self._parse_txt_file(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_path.suffix}")
            
        print(f"\nProcessing {len(prompts)} prompts from {file_path}")
        
        for i, prompt_data in enumerate(prompts, 1):
            try:
                # Extract prompt and output path
                if isinstance(prompt_data, dict):
                    prompt = prompt_data['prompt']
                    output_path = prompt_data.get('output_path')
                else:
                    prompt = prompt_data
                    output_path = None
                    
                print(f"\n=== Processing Prompt {i}/{len(prompts)} ===")
                print(f"Prompt: '{prompt}'")
                print(f"Output Path: {output_path or 'default'}")
                
                # Generate the furniture
                blend_path = self.generator.generate(prompt, output_path)
                
                if blend_path:
                    print(f"✓ Successfully generated: {blend_path}")
                else:
                    print(f"✗ Failed to generate furniture for prompt: '{prompt}'")
                    
            except Exception as e:
                print(f"✗ Error processing prompt {i}: {e}")
                continue
    
    def _parse_txt_file(self, file_path: Path) -> List[Dict]:
        """Parse a txt file with prompts and optional output paths"""
        prompts = []
        with open(file_path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                    
                # Check if line contains both prompt and path
                if ' -> ' in line:
                    prompt, output_path = line.split(' -> ')
                    prompts.append({
                        'prompt': prompt.strip(),
                        'output_path': output_path.strip()
                    })
                else:
                    prompts.append(line)
                    
        return prompts

def main():
    parser = argparse.ArgumentParser(description='Batch generate furniture from prompts file')
    parser.add_argument('input_file', type=str, help='Path to input file (.txt or .json)')
    args = parser.parse_args()
    
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("Error: OPENAI_API_KEY environment variable not set")
        return
        
    generator = BatchGenerator(api_key)
    generator.process_file(args.input_file)

if __name__ == "__main__":
    main() 