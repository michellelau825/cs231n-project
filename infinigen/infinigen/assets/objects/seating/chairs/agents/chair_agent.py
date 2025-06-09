import openai
import argparse
import json
from pathlib import Path
from typing import Literal

# TODO: add key and uncomment
# openai.api_key = ''

def determine_chair_type(description: str, chair_codes: dict) -> Literal["regular", "bar", "office"]:
    """Determine chair type by matching description against implementation capabilities"""
    
    messages = [
        {"role": "system", "content": """You are a furniture expert who understands Python code. 
Your task is to analyze chair generation code and match a description to the most appropriate implementation.
You will be given three different chair implementation codes and must choose which one best matches the description 
based ONLY on the parameters and capabilities shown in the code, NOT the names of the files."""},
        {"role": "user", "content": f"""
Here are three different chair implementation codes:

IMPLEMENTATION 1 (chair.py):
{chair_codes['regular']}

IMPLEMENTATION 2 (bar_chair.py):
{chair_codes['bar']}

IMPLEMENTATION 3 (office_chair.py):
{chair_codes['office']}

Given this chair description: "{description}"

Which implementation's parameters and capabilities best match this description? 
Respond with ONLY ONE of these exact words: 'regular', 'bar', or 'office'.
Base your decision SOLELY on which implementation's code can best create the described chair.
Ignore the names of the implementations - focus only on their parameters and capabilities."""}
    ]

    response = openai.chat.completions.create(
        model="gpt-4-0125-preview",
        messages=messages,
        temperature=0,
        max_tokens=10
    )
    
    return response.choices[0].message.content.strip().lower()

def generate_chair_params(description: str, output_path=None):
    """Generate chair parameters from a text description"""
    
    # Load all chair implementation codes first
    chair_module_map = {
        "regular": "chair.py",
        "bar": "bar_chair.py",
        "office": "office_chair.py"
    }
    
    chair_codes = {}
    for chair_type, filename in chair_module_map.items():
        chair_path = Path(__file__).parent.parent / filename
        with open(chair_path, 'r') as f:
            chair_codes[chair_type] = f.read()
    
    # Determine best implementation match based on code capabilities
    chair_type = determine_chair_type(description, chair_codes)
    
    messages = [
        {"role": "system", "content": f"You are a 3D furniture designer specializing in generating parameters for chair models. You understand Python code and can convert descriptions into specific parameter values."},
        {"role": "user", "content": f"""
Given this chair description: "{description}"

And this chair generation code:
{chair_codes[chair_type]}

Generate a JSON file with appropriate parameters to create this chair. 
Only define parameters that correspond with the description and are available in the implementation code.
The JSON should only include non-null parameters. Format the response as a valid JSON object.
"""}
    ]

    response = openai.chat.completions.create(
        model="gpt-4-0125-preview",
        messages=messages,
        temperature=0.3,
        max_tokens=2000
    )

    try:
        content = response.choices[0].message.content
        json_start = content.find('{')
        json_end = content.rfind('}') + 1
        json_str = content[json_start:json_end]
        json_str = json_str.replace('(', '[').replace(')', ']')
        params = json.loads(json_str)
        
        if output_path is None:
            # Create type-specific subdirectory under params
            params_dir = Path(__file__).parent.parent / "params" / chair_type
            params_dir.mkdir(parents=True, exist_ok=True)
            output_path = params_dir / f"generated_chair.json"
        else:
            output_path = Path(output_path)
            
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(params, f, indent=4)
            
        print(f"{chair_type.capitalize()} chair parameters saved to {output_path}")
        return params
        
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON response: {e}")
        return None

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate chair parameters from text description')
    parser.add_argument('description', type=str, help='Text description of the chair')
    parser.add_argument('--output', '-o', type=str, help='Output path for the JSON file')
    
    args = parser.parse_args()
    
    # Load chair codes first
    chair_module_map = {
        "regular": "chair.py",
        "bar": "bar_chair.py",
        "office": "office_chair.py"
    }
    
    chair_codes = {}
    for chair_type, filename in chair_module_map.items():
        chair_path = Path(__file__).parent.parent / filename
        with open(chair_path, 'r') as f:
            chair_codes[chair_type] = f.read()
    
    params = generate_chair_params(args.description, args.output)
    print("\nChair type detected:", determine_chair_type(args.description, chair_codes).upper())
    print("Generated parameters:", json.dumps(params, indent=2))
