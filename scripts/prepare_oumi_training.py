"""Prepare training dataset from algorithm library for Oumi"""
import json
from pathlib import Path
import ast

def extract_training_examples(repo_path: Path, max_samples: int = 500):
    """Extract code examples as instruction-response pairs"""
    training_data = []
    
    for py_file in list(repo_path.rglob("*.py"))[:max_samples]:
        try:
            with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    docstring = ast.get_docstring(node) or "No description"
                    code = ast.unparse(node)
                    
                    # Create instruction-response pair
                    training_data.append({
                        "instruction": f"Implement a function for: {docstring[:100]}",
                        "input": f"Function name: {node.name}",
                        "output": code,
                        "source": str(py_file.name)
                    })
        except Exception as e:
            continue
    
    return training_data

# Gather from multiple repos
repos = [
    Path("~/repos/KRYPTOR").expanduser(),
    Path("~/repos/Cryptography").expanduser(),
]

all_training_data = []
for repo in repos:
    if repo.exists():
        print(f"Scanning {repo}...")
        data = extract_training_examples(repo, max_samples=250)
        all_training_data.extend(data)
        print(f"  Found {len(data)} examples")

# Save in Oumi format (JSONL)
output_path = Path("~/nexus_evo/hackathon/oumi/crypto_training.jsonl").expanduser()
output_path.parent.mkdir(parents=True, exist_ok=True)

with open(output_path, 'w') as f:
    for example in all_training_data:
        f.write(json.dumps(example) + '\n')

print(f"\n✅ Created training dataset: {len(all_training_data)} examples")
print(f"📁 Saved to: {output_path}")
