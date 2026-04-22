#!/usr/bin/env python3
"""
Smart log fetcher: Tries GitHub Logs API, falls back to workflow context on 403
"""
import os
import sys
import json
import logging
import requests
import argparse

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

def fetch_logs(run_id: str, repo: str, token: str, output: str) -> bool:
    """Attempt to fetch logs via GitHub API"""
    url = f"https://api.github.com/repos/{repo}/actions/runs/{run_id}/logs"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    
    try:
        logging.info(f"📥 Fetching logs from {url}")
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            with open(output, "wb") as f:
                f.write(response.content)
            logging.info(f"✅ Logs saved to {output} ({len(response.content)} bytes)")
            return True
        elif response.status_code == 403:
            logging.warning(f"⚠️ 403 Forbidden: {response.json().get('message')}")
            return False
        else:
            logging.error(f"❌ HTTP {response.status_code}: {response.text[:200]}")
            return False
    except Exception as e:
        logging.error(f"❌ Request failed: {e}")
        return False

def create_synthetic_logs(run_id: str, repo: str, output: str):
    """Create minimal context when logs aren't available"""
    content = f"""[SYNTHETIC LOGS - Full logs require admin:read permission]
Run ID: {run_id}
Repository: {repo}
Timestamp: $(date -u +"%Y-%m-%dT%H:%M:%SZ")

# 🔍 Common DevOps Failure Patterns to Investigate:
## Azure/IaC Issues
- [ ] Bicep/Terraform syntax error (run: az deployment group validate / terraform validate)
- [ ] Managed Identity missing RBAC role (check: Contributor, Reader, AcrPull)
- [ ] Resource quota exceeded (check: Azure Subscription > Quotas)
- [ ] Network/NSG blocking outbound (ports 443, 80, 53)

## GitHub Actions Issues  
- [ ] Secret not configured (check: Repo Settings > Secrets)
- [ ] Runner resource constraints (CPU/memory timeout)
- [ ] Branch protection blocking PR creation

## AI/LLM Issues
- [ ] Azure OpenAI quota limit reached
- [ ] Embedding model mismatch in AI Search
- [ ] Prompt context window exceeded (>128K tokens)

# 💡 Next Step: Run Copilot agent with this context for best-effort analysis
"""
    with open(output, "w") as f:
        f.write(content)
    logging.info(f"📝 Synthetic logs created at {output}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--repo", required=True) 
    parser.add_argument("--token", required=True)
    parser.add_argument("--output", default="pipeline_logs.txt")
    args = parser.parse_args()
    
    success = fetch_logs(args.run_id, args.repo, args.token, args.output)
    if not success:
        logging.info("🔄 Falling back to synthetic logs...")
        create_synthetic_logs(args.run_id, args.repo, args.output)
        sys.exit(0)  # Exit success so workflow continues
EOF
chmod +x scripts/fetch_logs.py
