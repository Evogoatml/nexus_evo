"""Oumi integration for training custom models from algorithm library"""
import logging
from pathlib import Path
from typing import List, Dict
import subprocess
import json

logger = logging.getLogger(__name__)

class OumiTrainer:
    """Train specialized models using Oumi"""
    
    def __init__(self):
        self.workspace = Path("~/nexus_evo/hackathon/oumi").expanduser()
        self.workspace.mkdir(parents=True, exist_ok=True)
        self.models_dir = self.workspace / "models"
        self.models_dir.mkdir(exist_ok=True)
    
    def create_training_dataset(self, algorithm_samples: List[Dict]) -> Path:
        """
        Convert algorithm samples into Oumi training format
        Format: {"instruction": "...", "response": "..."}
        """
        dataset_path = self.workspace / "training_data.jsonl"
        
        with open(dataset_path, 'w') as f:
            for sample in algorithm_samples:
                training_example = {
                    "instruction": f"Implement {sample['task']}",
                    "response": sample['code'],
                    "input": sample.get('context', '')
                }
                f.write(json.dumps(training_example) + '\n')
        
        logger.info(f"Created dataset: {len(algorithm_samples)} samples")
        return dataset_path
    
    def train_specialized_model(
        self,
        base_model: str = "HuggingFaceTB/SmolLM2-135M",
        dataset_path: Path = None,
        task_name: str = "crypto"
    ) -> Dict:
        """
        Fine-tune a model for specialized tasks
        Example: Train a crypto-specialized model from your KRYPTOR algorithms
        """
        try:
            config_path = self.workspace / f"{task_name}_config.yaml"
            
            # Create Oumi training config
            config = f"""
model_name: {base_model}
dataset:
  path: {dataset_path}
  format: instruction
training:
  num_epochs: 3
  batch_size: 4
  learning_rate: 2e-5
  output_dir: {self.models_dir / task_name}
"""
            config_path.write_text(config)
            
            # Run Oumi training
            logger.info(f"Training {task_name} model...")
            result = subprocess.run(
                ["oumi", "train", "-c", str(config_path)],
                capture_output=True,
                text=True,
                timeout=1800  # 30 min max
            )
            
            if result.returncode == 0:
                return {
                    "success": True,
                    "model_path": str(self.models_dir / task_name),
                    "task": task_name,
                    "output": result.stdout
                }
            else:
                return {
                    "success": False,
                    "error": result.stderr
                }
                
        except Exception as e:
            logger.error(f"Training failed: {e}")
            return {"success": False, "error": str(e)}
    
    def evaluate_model(self, model_path: Path) -> Dict:
        """Evaluate trained model"""
        try:
            eval_config = self.workspace / "eval_config.yaml"
            eval_config.write_text(f"""
model_path: {model_path}
tasks: [hellaswag, arc_easy]
""")
            
            result = subprocess.run(
                ["oumi", "evaluate", "-c", str(eval_config)],
                capture_output=True,
                text=True,
                timeout=600
            )
            
            return {
                "success": True,
                "metrics": result.stdout
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

oumi_trainer = OumiTrainer()
