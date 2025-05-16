import json
from pathlib import Path

def generate_scene_json(num_chairs=2):
    """Generate a JSON file describing a scene with a table and chairs"""
    scene = {
        "objects": [
            {
                "type": "table",
                "name": "DiningTable",
                "dimensions": {
                    "width": 1.8,    # 180cm
                    "depth": 0.9,    # 90cm
                    "height": 0.75,  # 75cm
                    "thickness": 0.05  # 5cm
                },
                "position": [0, 0, 0],
                "legs": [
                    {
                        "position": [0.85, 0.4, 0],
                        "height": 0.7,
                        "radius": 0.03
                    },
                    {
                        "position": [0.85, -0.4, 0],
                        "height": 0.7,
                        "radius": 0.03
                    },
                    {
                        "position": [-0.85, 0.4, 0],
                        "height": 0.7,
                        "radius": 0.03
                    },
                    {
                        "position": [-0.85, -0.4, 0],
                        "height": 0.7,
                        "radius": 0.03
                    }
                ]
            }
        ]
    }
    
    # Add chairs
    chair_positions = [
        ((0, -1.2), 0),      # Front
        ((0, 1.2), 180),     # Back
    ]
    
    if num_chairs > 2:
        chair_positions.extend([
            ((-1.2, 0), 90),     # Left
            ((1.2, 0), -90)      # Right
        ])
    
    for i, (pos, rot) in enumerate(chair_positions[:num_chairs]):
        scene["objects"].append({
            "type": "chair",
            "name": f"Chair{i+1}",
            "dimensions": {
                "width": 0.45,    # 45cm
                "depth": 0.45,    # 45cm
                "height": 0.9,    # 90cm
                "thickness": 0.05  # 5cm
            },
            "position": [pos[0], pos[1], 0],
            "rotation": rot,
            "legs": [
                {
                    "position": [0.2, 0.2, 0],
                    "height": 0.45,
                    "radius": 0.015
                },
                {
                    "position": [0.2, -0.2, 0],
                    "height": 0.45,
                    "radius": 0.015
                },
                {
                    "position": [-0.2, 0.2, 0],
                    "height": 0.45,
                    "radius": 0.015
                },
                {
                    "position": [-0.2, -0.2, 0],
                    "height": 0.45,
                    "radius": 0.015
                }
            ]
        })
    
    return scene

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--chairs", type=int, default=2, help="Number of chairs to generate")
    args = parser.parse_args()
    
    scene = generate_scene_json(args.chairs)
    
    # Save to file
    output_dir = Path.home() / "Desktop" / "generated-assets"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "scene.json"
    
    with open(output_path, "w") as f:
        json.dump(scene, f, indent=2)
    
    print(f"Scene JSON saved to: {output_path}") 