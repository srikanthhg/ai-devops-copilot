# src/agent/main.py
import os
import json
import logging
import requests
from datetime import datetime
from openai import AzureOpenAI
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
from github import Github

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

class DevOpsCopilot:
    def __init__(self):
        # Azure OpenAI
        self.openai_client = AzureOpenAI(
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_version="2024-06-01",
            api_key=os.getenv("AZURE_OPENAI_KEY"),
        )
        # Azure AI Search
        self.search_client = SearchClient(
            endpoint=os.getenv("AZURE_SEARCH_ENDPOINT"),
            index_name="devops-runbooks",
            credential=AzureKeyCredential(os.getenv("AZURE_SEARCH_KEY")),
        )
        # GitHub
        self.gh = Github(os.getenv("GITHUB_TOKEN"))
        self.repo_name = os.getenv("GITHUB_REPOSITORY")

    def retrieve_context(self, error_snippet: str) -> str:
        """Query AI Search for relevant runbooks/past fixes"""
        results = self.search_client.search(
            search_text=error_snippet,
            select=["title", "content"],
            top=3
        )
        context = "\n\n".join([
            f"### {r['title']}\n{r['content']}" for r in results
        ])
        return context or "No internal runbooks found. Using base troubleshooting knowledge."

    def analyze_and_fix(self, logs: str) -> dict:
        """LLM analysis + fix generation"""
        context = self.retrieve_context(logs[:500])  # snippet for search
        
        prompt = f"""
        You are a Senior DevOps Engineer AI Copilot. Analyze the following pipeline failure logs and suggest a precise fix.
        
        CONTEXT (Internal Runbooks):
        {context}
        
        PIPELINE LOGS:
        {logs[:3000]}
        
        OUTPUT FORMAT (STRICT JSON):
        {{
          "root_cause": "1-2 sentence explanation",
          "fix_type": "bicep | terraform | yaml | config",
          "suggested_fix": "exact code/config snippet to apply",
          "confidence_score": 0.0-1.0,
          "rollback_plan": "how to revert if fix fails"
        }}
        """
        
        response = self.openai_client.chat.completions.create(
            model="gpt-4o-mini",  # or your deployed model
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)

    def create_fix_pr(self, analysis: dict, logs_file: str) -> str:
        """Auto-generate branch + PR with fix"""
        repo = self.gh.get_repo(self.repo_name)
        branch_name = f"copilot-fix-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
        # Create branch from main
        main_ref = repo.get_git_ref("heads/main")
        repo.create_git_ref(ref=f"refs/heads/{branch_name}", sha=main_ref.object.sha)
        
        # Create fix file (for MVP, saves as copilot-fix.md)
        fix_content = f"""# 🔧 Copilot Suggested Fix
- **Root Cause**: {analysis['root_cause']}
- **Confidence**: {analysis['confidence_score']*100:.0f}%
- **Type**: {analysis['fix_type']}

## Suggested Change
```{analysis['fix_type']}
{analysis['suggested_fix']}
