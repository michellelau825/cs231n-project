# Language-Driven Primitive-Based 3D Scene Generation with Infinigen

## 👩🏻‍💻 Authors: Michelle Lau, Eyrin Kim

Paper: [https://drive.google.com/file/d/1MTJJodJV7S9TS4Mzec-C9SP7TXxY3rDu/view?usp=sharing]

Our project is built on top of the Infinigen codebase. We wrote all our files in `cs231n-project/infinigen/primitive_builder`. 
Please check the `agents` folder for each agent's implementation and `full_agent.py` for the full implementation. 
`decomposed_agent.py` and `direct_primitive_agent.py` are incomplete versions of `full_agent.py` used for comparison.
<p align="center"> <img width="749" alt="Screenshot 2025-06-09 at 12 23 14 PM" src="https://github.com/user-attachments/assets/7e421280-764c-4a6f-96b5-7ca4b4bb5149" /> </p>

### 🛠 Steps for generating 3D scene
#### 1. Clone this repo
#### 2. Follow the official Infinigen repository for installation and setup: https://github.com/princeton-vl/infinigen 
#### 3. Setup OpenAI API Key
```bash
export OPENAI_API_KEY=’YOUR-KEY’ 
```
Visit the OpenAI Platform website to generate your API key.

#### 4. Run `full agent`
```bash
python primitive_builder/full_agent.py "DESCRIPTION" "CUSTOM_PATH_1" "CUSTOM_PATH_2"
```
This line generates a `DESCRIPTION` furniture, with the pre-validator version saved at custom path `"CUSTOM_PATH_1"` and the post-validator version saved at custom path `"CUSTOM_PATH_2"`. An example of the DESCRIPTION would be: "A round table with two candles on top of it."
<p align="center"> <img width="707" alt="Screenshot 2025-06-09 at 12 23 03 PM" src="https://github.com/user-attachments/assets/f07e7113-13c9-411d-996b-c0278a69d7bc" /> </p>
