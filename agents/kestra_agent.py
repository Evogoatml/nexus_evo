"""Kestra workflow orchestration for Nexus EVO"""
import logging
from typing import Dict, List, Any
from pathlib import Path
import json
import subprocess

logger = logging.getLogger(__name__)

class KestraOrchestrator:
    """Orchestrate complex workflows using Kestra"""
    
    def __init__(self):
        self.workspace = Path("~/nexus_evo/hackathon/kestra").expanduser()
        self.workspace.mkdir(parents=True, exist_ok=True)
        self.flows_dir = self.workspace / "flows"
        self.flows_dir.mkdir(exist_ok=True)
    
    def create_algorithm_analysis_flow(self) -> Path:
        """
        Create a Kestra flow that:
        1. Scans algorithm repos
        2. Summarizes capabilities using AI
        3. Makes recommendations
        """
        flow_config = {
            "id": "algorithm-analysis",
            "namespace": "nexus.evo",
            "tasks": [
                {
                    "id": "scan_repos",
                    "type": "io.kestra.core.tasks.scripts.Python",
                    "script": """
import os
import json
from pathlib import Path

repos = [
    '~/repos/KRYPTOR',
    '~/repos/Cryptography',
    '~/repos/Computer-Security-algorithms'
]

algorithms = []
for repo in repos:
    repo_path = Path(repo).expanduser()
    if repo_path.exists():
        for py_file in repo_path.rglob('*.py'):
            algorithms.append({
                'file': str(py_file),
                'repo': repo,
                'size': py_file.stat().st_size
            })

print(json.dumps(algorithms))
"""
                },
                {
                    "id": "ai_summarize",
                    "type": "io.kestra.plugin.ai.Agent",
                    "prompt": "Analyze these cryptographic algorithms and summarize their capabilities, strengths, and use cases: {{ outputs.scan_repos.value }}",
                    "model": "gpt-4o-mini"
                },
                {
                    "id": "make_recommendation",
                    "type": "io.kestra.plugin.ai.Agent",
                    "prompt": "Based on this analysis: {{ outputs.ai_summarize.value }}, recommend the best algorithm for: AES encryption with key rotation",
                    "model": "gpt-4o-mini"
                }
            ]
        }
        
        flow_path = self.flows_dir / "algorithm_analysis.yaml"
        import yaml
        with open(flow_path, 'w') as f:
            yaml.dump(flow_config, f)
        
        logger.info(f"Created Kestra flow: {flow_path}")
        return flow_path
    
    def execute_flow(self, flow_id: str) -> Dict[str, Any]:
        """Execute a Kestra flow and return results"""
        try:
            # Execute via Kestra CLI or API
            result = subprocess.run(
                ["kestra", "flow", "execute", flow_id],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                return {
                    "success": True,
                    "output": result.stdout,
                    "flow_id": flow_id
                }
            else:
                return {
                    "success": False,
                    "error": result.stderr
                }
        except Exception as e:
            logger.error(f"Flow execution failed: {e}")
            return {"success": False, "error": str(e)}
    
    def algorithm_selector_workflow(self, task_description: str) -> Dict:
        """
        AI-powered algorithm selection workflow
        Demonstrates: Data summarization + Decision making
        """
        workflow_result = {
            "task": task_description,
            "steps": []
        }
        
        # Step 1: Scan available algorithms
        logger.info("Step 1: Scanning algorithm library...")
        scan_result = self._scan_algorithms()
        workflow_result["steps"].append({
            "name": "scan",
            "found": len(scan_result)
        })
        
        # Step 2: Summarize with AI (Kestra AI Agent)
        logger.info("Step 2: AI summarization...")
        summary = self._ai_summarize(scan_result, task_description)
        workflow_result["steps"].append({
            "name": "summarize",
            "summary": summary
        })
        
        # Step 3: Make decision
        logger.info("Step 3: Decision making...")
        decision = self._make_decision(summary, task_description)
        workflow_result["steps"].append({
            "name": "decide",
            "recommendation": decision
        })
        
        return workflow_result
    
    def _scan_algorithms(self) -> List[Dict]:
        """Scan algorithm repositories"""
        algorithms = []
        repos = [
            Path("~/repos/KRYPTOR").expanduser(),
            Path("~/repos/Cryptography").expanduser(),
        ]
        
        for repo in repos:
            if repo.exists():
                for py_file in list(repo.rglob("*.py"))[:20]:  # Limit for demo
                    algorithms.append({
                        "file": py_file.name,
                        "path": str(py_file),
                        "repo": repo.name
                    })
        
        return algorithms
    
    def _ai_summarize(self, algorithms: List[Dict], task: str) -> str:
        """Use LLM to summarize capabilities"""
        from core.llm import LLMInterface
        
        llm = LLMInterface()
        prompt = f"""
Analyze these cryptographic algorithms and summarize which are relevant for: {task}

Algorithms found:
{json.dumps(algorithms, indent=2)}

Provide a concise summary of the most relevant ones.
"""
        return llm.generate_from_prompt(prompt, max_tokens=500)
    
    def _make_decision(self, summary: str, task: str) -> str:
        """AI-powered decision making"""
        from core.llm import LLMInterface
        
        llm = LLMInterface()
        prompt = f"""
Based on this analysis:
{summary}

Task: {task}

Make a specific recommendation: Which algorithm should be used and why?
Format: "Use [algorithm] because [reason]"
"""
        return llm.generate_from_prompt(prompt, max_tokens=200)

kestra_orchestrator = KestraOrchestrator()
