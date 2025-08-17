#!/usr/bin/env python3
"""
Post Cascade Comment

Posts actionable remediation tips as PR comments when Rule B or C is triggered.
"""

import os
import sys
import json
import argparse
from typing import Dict, List, Any, Optional
from datetime import datetime

# Optional import for GitHub API
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    print("Warning: requests module not available - GitHub API calls will be skipped")


def load_json_file(file_path: str) -> Optional[Dict[str, Any]]:
    """Load JSON file with graceful fallback."""
    if not os.path.exists(file_path):
        return None
    
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Warning: Could not load {file_path}: {e}")
        return None


def extract_cascade_line(cascade_data: Dict[str, Any]) -> str:
    """Extract the CASCADE line from cascade data."""
    return cascade_data.get("summary", "CASCADE: no summary available")


def extract_slo_metrics(override_latency_file: str) -> Dict[str, Any]:
    """Extract SLO metrics from override latency stats."""
    data = load_json_file(override_latency_file)
    if not data:
        return {"p50": 0, "p95": 0, "p99": 0, "available": False}
    
    # Try to parse the text format if JSON structure is different
    if isinstance(data, str):
        # Parse text format
        lines = data.split('\n')
        p50 = p95 = p99 = 0
        for line in lines:
            if 'p50' in line.lower():
                try:
                    p50 = float(line.split(':')[1].strip().replace('ms', '').replace('s', ''))
                except:
                    pass
            elif 'p95' in line.lower():
                try:
                    p95 = float(line.split(':')[1].strip().replace('ms', '').replace('s', ''))
                except:
                    pass
            elif 'p99' in line.lower():
                try:
                    p99 = float(line.split(':')[1].strip().replace('ms', '').replace('s', ''))
                except:
                    pass
        return {"p50": p50, "p95": p95, "p99": p99, "available": True}
    
    stats = data.get("statistics", {})
    return {
        "p50": stats.get("p50", 0),
        "p95": stats.get("p95", 0),
        "p99": stats.get("p99", 0),
        "available": True
    }


def extract_complexity_tips(complexity_file: str) -> List[str]:
    """Extract top 3 complexity remediation tips."""
    data = load_json_file(complexity_file)
    if not data:
        return ["Complexity analysis not available"]
    
    tips = []
    
    # Check for high complexity modules
    modules = data.get("modules", {})
    high_complexity = {k: v for k, v in modules.items() if v >= 7}
    
    if high_complexity:
        tips.append(f"**High complexity detected**: {len(high_complexity)} modules with ≥7 flows")
        
        # Add specific remediation tips
        if len(tips) < 3:
            tips.append("**Split large modules**: Break delegation_manager.py into routing.py + interrupts.py")
        if len(tips) < 3:
            tips.append("**Extract handlers**: Move delegation handlers into separate classes")
        if len(tips) < 3:
            tips.append("**Consolidate flows**: Merge duplicate delegation handlers")
    
    # Add general tips if we don't have enough
    while len(tips) < 3:
        tips.append("**Review delegation patterns**: Consider factory or state machine patterns")
        if len(tips) >= 3:
            break
    
    return tips[:3]


def extract_latency_tips(override_latency_file: str) -> List[str]:
    """Extract top 3 latency remediation tips."""
    data = load_json_file(override_latency_file)
    if not data:
        return ["Latency analysis not available"]
    
    stats = data.get("statistics", {})
    p95 = stats.get("p95", 0)
    p99 = stats.get("p99", 0)
    
    tips = []
    
    # Add latency-specific tips
    if p95 >= 1500:
        tips.append("**Critical latency**: p95 ≥ 1500ms - optimize override path immediately")
    elif p95 >= 1200:
        tips.append("**High latency**: p95 ≥ 1200ms - review database queries in override resolution")
    
    if p99 >= 2000:
        tips.append("**Critical p99**: p99 ≥ 2000ms - implement caching for delegation chains")
    elif p99 >= 1600:
        tips.append("**High p99**: p99 ≥ 1600ms - profile override resolution logic")
    
    # Add general tips
    if len(tips) < 3:
        tips.append("**Optimize queries**: Review database queries in delegation override path")
    if len(tips) < 3:
        tips.append("**Implement caching**: Cache frequently accessed delegation chains")
    if len(tips) < 3:
        tips.append("**Review async patterns**: Check async/await usage in override logic")
    
    return tips[:3]


def extract_modules_with_high_flows(complexity_file: str) -> List[str]:
    """Extract modules with flows ≥6."""
    data = load_json_file(complexity_file)
    if not data:
        return ["Complexity analysis not available"]
    
    modules = data.get("modules", {})
    high_flows = [(k, v) for k, v in modules.items() if v >= 6]
    
    if not high_flows:
        return ["No modules with flows ≥6"]
    
    # Sort by flow count descending
    high_flows.sort(key=lambda x: x[1], reverse=True)
    
    # Format as list of strings
    result = []
    for module, flows in high_flows:
        result.append(f"{module}: {flows} flows")
    
    return result


def compose_comment(cascade_line: str, slo_metrics: Dict[str, Any], 
                   complexity_tips: List[str], latency_tips: List[str],
                   modules_with_high_flows: List[str]) -> str:
    """Compose the PR comment with cascade info and remediation tips."""
    
    comment = f"""## 🔍 Constitutional Cascade Alert

**CASCADE**: {cascade_line}

### 📊 Current SLO Status"""
    
    if slo_metrics["available"]:
        comment += f"""
- **Override Latency**: p50={slo_metrics['p50']}ms, p95={slo_metrics['p95']}ms, p99={slo_metrics['p99']}ms
- **Targets**: p95 < 1500ms, p99 < 2000ms"""
    else:
        comment += "\n- **SLO Data**: Not available"
    
    comment += """

### 📈 Complexity Analysis

**Modules with flows ≥6:**
"""
    
    for module in modules_with_high_flows:
        comment += f"- {module}\n"
    
    comment += """
### 🛠️ Remediation Tips

#### Complexity Issues:
"""
    
    for tip in complexity_tips:
        comment += f"- {tip}\n"
    
    comment += """
#### Latency Issues:
"""
    
    for tip in latency_tips:
        comment += f"- {tip}\n"
    
    comment += """
### 📚 Resources
- [Cascade Rules](docs/cascade_rules.md#complexity)
- [SLO Guide](docs/SLO_delegation_backend.md)
- [Constitutional Amendment Process](docs/constitutional_amendment_process.md)

---
*This comment was auto-generated by the constitutional cascade system.*
"""
    
    return comment


def post_github_comment(comment: str, pr_number: int, token: str, repo: str) -> bool:
    """Post comment to GitHub PR."""
    if not REQUESTS_AVAILABLE:
        print("❌ Cannot post comment: requests module not available")
        return False
    
    url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments"
    
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "constitutional-cascade-bot"
    }
    
    data = {
        "body": comment
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        
        comment_data = response.json()
        print(f"✅ Comment posted successfully: {comment_data['html_url']}")
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to post comment: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response: {e.response.text}")
        return False


def find_existing_comment(pr_number: int, token: str, repo: str) -> Optional[int]:
    """Find existing cascade comment to update instead of creating new one."""
    if not REQUESTS_AVAILABLE:
        print("⚠️  Cannot check existing comments: requests module not available")
        return None
    
    url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments"
    
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "constitutional-cascade-bot"
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        comments = response.json()
        for comment in comments:
            if "Constitutional Cascade Alert" in comment["body"]:
                return comment["id"]
        
        return None
        
    except requests.exceptions.RequestException as e:
        print(f"Warning: Could not check existing comments: {e}")
        return None


def update_github_comment(comment: str, comment_id: int, token: str, repo: str) -> bool:
    """Update existing GitHub comment."""
    if not REQUESTS_AVAILABLE:
        print("❌ Cannot update comment: requests module not available")
        return False
    
    url = f"https://api.github.com/repos/{repo}/issues/comments/{comment_id}"
    
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "constitutional-cascade-bot"
    }
    
    data = {
        "body": comment
    }
    
    try:
        response = requests.patch(url, headers=headers, json=data)
        response.raise_for_status()
        
        comment_data = response.json()
        print(f"✅ Comment updated successfully: {comment_data['html_url']}")
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to update comment: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response: {e.response.text}")
        return False


def should_post_comment(cascade_data: Dict[str, Any]) -> bool:
    """Check if we should post a comment (Rule B or C triggered)."""
    if not cascade_data:
        return False
    
    cascade_results = cascade_data.get("cascade_results", [])
    
    for result in cascade_results:
        rule_id = result.get("rule_id", "")
        if rule_id in ["B", "C"]:
            return True
    
    return False


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Post cascade remediation tips as PR comment")
    parser.add_argument("--cascade-file", default="reports/constitutional_cascade.json",
                       help="Path to cascade JSON file")
    parser.add_argument("--warnings-file", default="reports/constitutional_warnings.json",
                       help="Path to warnings JSON file")
    parser.add_argument("--override-latency-file", default="reports/override_latency_stats.json",
                       help="Path to override latency stats file")
    parser.add_argument("--complexity-file", default="reports/complexity_stats.json",
                       help="Path to complexity stats file")
    parser.add_argument("--dry-run", action="store_true",
                       help="Print comment without posting")
    
    args = parser.parse_args()
    
    print("🤖 CASCADE COMMENT BOT")
    print("=====================")
    
    # Load cascade data
    cascade_data = load_json_file(args.cascade_file)
    if not cascade_data:
        print("⚠️  No cascade data found - skipping comment")
        return
    
    # Check if we should post a comment
    if not should_post_comment(cascade_data):
        print("ℹ️  No Rule B or C triggered - skipping comment")
        return
    
    # Extract data
    cascade_line = extract_cascade_line(cascade_data)
    slo_metrics = extract_slo_metrics(args.override_latency_file)
    complexity_tips = extract_complexity_tips(args.complexity_file)
    latency_tips = extract_latency_tips(args.override_latency_file)
    modules_with_high_flows = extract_modules_with_high_flows(args.complexity_file)
    
    # Compose comment
    comment = compose_comment(cascade_line, slo_metrics, complexity_tips, latency_tips, modules_with_high_flows)
    
    if args.dry_run:
        print("\n📝 COMMENT PREVIEW:")
        print("=" * 50)
        print(comment)
        print("=" * 50)
        return
    
    # Get GitHub environment variables
    token = os.environ.get("GITHUB_TOKEN")
    pr_number = os.environ.get("PR_NUMBER")
    repo = os.environ.get("GITHUB_REPOSITORY")
    
    if not all([token, pr_number, repo]):
        print("❌ Missing required environment variables:")
        print(f"  GITHUB_TOKEN: {'✓' if token else '✗'}")
        print(f"  PR_NUMBER: {'✓' if pr_number else '✗'}")
        print(f"  GITHUB_REPOSITORY: {'✓' if repo else '✗'}")
        return
    
    try:
        pr_number = int(pr_number)
    except ValueError:
        print(f"❌ Invalid PR number: {pr_number}")
        return
    
    # Check for existing comment
    existing_comment_id = find_existing_comment(pr_number, token, repo)
    
    if existing_comment_id:
        print(f"📝 Updating existing comment {existing_comment_id}...")
        success = update_github_comment(comment, existing_comment_id, token, repo)
    else:
        print(f"📝 Posting new comment to PR #{pr_number}...")
        success = post_github_comment(comment, pr_number, token, repo)
    
    if success:
        print("✅ Cascade comment posted/updated successfully")
    else:
        print("❌ Failed to post/update cascade comment")
        sys.exit(1)


if __name__ == "__main__":
    main()
