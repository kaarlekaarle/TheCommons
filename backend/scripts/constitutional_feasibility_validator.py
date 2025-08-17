#!/usr/bin/env python3
"""
Constitutional Feasibility Validator

This script validates the technical feasibility of constitutional amendments
by cross-checking against the current architecture and detecting infeasible demands.
"""

import os
import sys
import json
import re
import ast
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Tuple

# Current architecture components
CURRENT_ARCHITECTURE = {
    "api_endpoints": {
        "auth": ["/api/token", "/api/users/me", "/api/auth/"],
        "users": ["/api/users/", "/api/users/{user_id}"],
        "polls": ["/api/polls/", "/api/polls/{poll_id}"],
        "votes": ["/api/votes/", "/api/votes/{vote_id}"],
        "delegations": ["/api/delegations/", "/api/delegations/{delegation_id}"],
        "options": ["/api/options/", "/api/options/{option_id}"],
        "comments": ["/api/comments/", "/api/comments/{comment_id}"],
        "reactions": ["/api/reactions/", "/api/reactions/{reaction_id}"],
        "activity": ["/api/activity/", "/api/activity/{activity_id}"],
        "content": ["/api/content/", "/api/content/{content_id}"],
        "labels": ["/api/labels/", "/api/labels/{label_id}"],
        "feedback": ["/api/feedback/", "/api/feedback/{feedback_id}"],
        "websocket": ["/api/websocket/"],
        "health": ["/api/health/"]
    },
    "database_tables": {
        "users": ["id", "username", "email", "created_at", "updated_at"],
        "polls": ["id", "title", "description", "creator_id", "created_at", "updated_at"],
        "options": ["id", "poll_id", "text", "created_at"],
        "votes": ["id", "user_id", "option_id", "created_at"],
        "delegations": ["id", "delegator_id", "delegate_id", "poll_id", "created_at", "revoked_at"],
        "comments": ["id", "user_id", "poll_id", "content", "created_at"],
        "comment_reactions": ["id", "comment_id", "user_id", "reaction_type", "created_at"],
        "labels": ["id", "name", "description", "created_at"],
        "poll_labels": ["id", "poll_id", "label_id"],
        "activity_log": ["id", "user_id", "action_type", "details", "created_at"],
        "delegation_stats": ["id", "user_id", "total_delegations", "active_delegations", "updated_at"],
        "ideas": ["id", "title", "description", "created_at"],
        "values": ["id", "name", "description", "created_at"]
    },
    "services": {
        "user_service": ["create_user", "get_user", "update_user", "delete_user"],
        "poll_service": ["create_poll", "get_poll", "update_poll", "delete_poll", "get_poll_results"],
        "delegation_service": ["create_delegation", "get_delegation", "revoke_delegation", "resolve_delegation_chain"],
        "content_loader": ["load_content", "get_content"],
        "feedback_service": ["create_feedback", "get_feedback"],
        "concentration_monitor": ["check_concentration", "get_concentration_stats"]
    },
    "models": {
        "User": ["id", "username", "email", "created_at", "updated_at"],
        "Poll": ["id", "title", "description", "creator_id", "created_at", "updated_at"],
        "Option": ["id", "poll_id", "text", "created_at"],
        "Vote": ["id", "user_id", "option_id", "created_at"],
        "Delegation": ["id", "delegator_id", "delegate_id", "poll_id", "created_at", "revoked_at"],
        "Comment": ["id", "user_id", "poll_id", "content", "created_at"],
        "CommentReaction": ["id", "comment_id", "user_id", "reaction_type", "created_at"],
        "Label": ["id", "name", "description", "created_at"],
        "PollLabel": ["id", "poll_id", "label_id"],
        "ActivityLog": ["id", "user_id", "action_type", "details", "created_at"],
        "DelegationStats": ["id", "user_id", "total_delegations", "active_delegations", "updated_at"],
        "Idea": ["id", "title", "description", "created_at"],
        "Value": ["id", "name", "description", "created_at"]
    },
    "technologies": {
        "backend": ["FastAPI", "SQLAlchemy", "PostgreSQL", "Redis", "Alembic"],
        "frontend": ["React", "TypeScript", "Tailwind CSS", "Vite"],
        "deployment": ["Docker", "Docker Compose", "GitHub Actions"],
        "testing": ["pytest", "Playwright", "Vitest"]
    },
    "infrastructure": {
        "database": "PostgreSQL",
        "cache": "Redis",
        "orm": "SQLAlchemy",
        "framework": "FastAPI",
        "authentication": "JWT",
        "rate_limiting": "Redis-based"
    }
}

# Feasibility check categories
FEASIBILITY_CHECKS = {
    "architecture_compatibility": {
        "name": "Architecture Compatibility Check",
        "description": "Check if amendment is compatible with current architecture",
        "severity": "critical"
    },
    "resource_requirements": {
        "name": "Resource Requirements Check",
        "description": "Check if amendment requires reasonable resources",
        "severity": "critical"
    },
    "implementation_complexity": {
        "name": "Implementation Complexity Check",
        "description": "Check if amendment is implementable with current complexity",
        "severity": "warning"
    },
    "dependency_analysis": {
        "name": "Dependency Analysis Check",
        "description": "Check if amendment has feasible dependencies",
        "severity": "warning"
    }
}

# Infeasible patterns and requirements
INFEASIBLE_PATTERNS = {
    "non_existent_modules": [
        r"import\s+(\w+)\s+from\s+['\"]backend\.(?!api|services|models|core)",
        r"from\s+backend\.(?!api|services|models|core)\.",
        r"backend\.(?!api|services|models|core)\."
    ],
    "infinite_resources": [
        r"infinite\s+(?:memory|storage|processing|bandwidth)",
        r"unlimited\s+(?:memory|storage|processing|bandwidth)",
        r"no\s+(?:memory|storage|processing|bandwidth)\s+limits"
    ],
    "impossible_performance": [
        r"instantaneous\s+(?:response|processing|calculation)",
        r"zero\s+(?:latency|delay|response\s+time)",
        r"real\s+time\s+(?:without\s+delay|instant)"
    ],
    "unsupported_technologies": [
        r"blockchain\s+integration",
        r"ai\s+ml\s+integration",
        r"machine\s+learning\s+integration",
        r"artificial\s+intelligence\s+integration"
    ]
}


class ConstitutionalFeasibilityValidator:
    """Validator for technical feasibility of constitutional amendments."""
    
    def __init__(self):
        self.architecture = CURRENT_ARCHITECTURE
        self.infeasible_patterns = INFEASIBLE_PATTERNS
        self.feasibility_checks = FEASIBILITY_CHECKS
    
    def validate_feasibility(self, amendment_text: str, changed_files: List[str] = None) -> Dict[str, Any]:
        """Validate technical feasibility of amendment."""
        print("🔧 TECHNICAL FEASIBILITY VALIDATION")
        print("=" * 40)
        
        validation_result = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "unknown",
            "checks": {},
            "infeasible_demands": [],
            "warnings": [],
            "recommendations": []
        }
        
        # Run each feasibility check
        for check_id, check_config in self.feasibility_checks.items():
            print(f"Running {check_config['name']}...")
            
            if check_id == "architecture_compatibility":
                check_result = self._check_architecture_compatibility(amendment_text, changed_files)
            elif check_id == "resource_requirements":
                check_result = self._check_resource_requirements(amendment_text)
            elif check_id == "implementation_complexity":
                check_result = self._check_implementation_complexity(amendment_text, changed_files)
            elif check_id == "dependency_analysis":
                check_result = self._check_dependency_analysis(amendment_text, changed_files)
            else:
                check_result = self._run_placeholder_check(check_id, check_config)
            
            validation_result["checks"][check_id] = check_result
            
            status_icon = "✅" if check_result["status"] == "pass" else "❌" if check_result["status"] == "fail" else "⚠️"
            print(f"  {status_icon} {check_config['name']}: {check_result['status']}")
        
        # Collect infeasible demands and warnings
        for check_result in validation_result["checks"].values():
            if check_result.get("infeasible_demands"):
                validation_result["infeasible_demands"].extend(check_result["infeasible_demands"])
            
            if check_result.get("warnings"):
                validation_result["warnings"].extend(check_result["warnings"])
        
        # Determine overall status
        any_failed = any(check["status"] == "fail" for check in validation_result["checks"].values())
        any_warnings = any(check["status"] == "warning" for check in validation_result["checks"].values())
        
        if any_failed:
            validation_result["overall_status"] = "failed"
            validation_result["recommendations"].append("CRITICAL: Address infeasible demands before proceeding")
        elif any_warnings:
            validation_result["overall_status"] = "warning"
            validation_result["recommendations"].append("WARNING: Review implementation complexity and dependencies")
        else:
            validation_result["overall_status"] = "passed"
            validation_result["recommendations"].append("SUCCESS: Amendment is technically feasible")
        
        return validation_result
    
    def _check_architecture_compatibility(self, amendment_text: str, changed_files: List[str] = None) -> Dict[str, Any]:
        """Check if amendment is compatible with current architecture."""
        infeasible_demands = []
        warnings = []
        
        # Check for non-existent API endpoints
        for endpoint_type, endpoints in self.architecture["api_endpoints"].items():
            # Look for references to non-existent endpoints
            for endpoint in endpoints:
                if endpoint not in amendment_text and f"/api/{endpoint_type}/" in amendment_text:
                    warnings.append(f"Potential reference to non-existent {endpoint_type} endpoint")
        
        # Check for non-existent database tables
        for table_name, columns in self.architecture["database_tables"].items():
            # Look for references to non-existent tables
            if f"table {table_name}" in amendment_text.lower() and table_name not in self.architecture["database_tables"]:
                infeasible_demands.append(f"Reference to non-existent database table: {table_name}")
        
        # Check for non-existent services
        for service_name, methods in self.architecture["services"].items():
            # Look for references to non-existent services
            if f"service {service_name}" in amendment_text.lower() and service_name not in self.architecture["services"]:
                infeasible_demands.append(f"Reference to non-existent service: {service_name}")
        
        # Check for non-existent models
        for model_name, fields in self.architecture["models"].items():
            # Look for references to non-existent models
            if f"model {model_name}" in amendment_text.lower() and model_name not in self.architecture["models"]:
                infeasible_demands.append(f"Reference to non-existent model: {model_name}")
        
        status = "fail" if infeasible_demands else "warning" if warnings else "pass"
        
        return {
            "check_type": "architecture_compatibility",
            "status": status,
            "infeasible_demands": infeasible_demands,
            "warnings": warnings,
            "details": f"Found {len(infeasible_demands)} infeasible demands, {len(warnings)} warnings"
        }
    
    def _check_resource_requirements(self, amendment_text: str) -> Dict[str, Any]:
        """Check if amendment requires reasonable resources."""
        infeasible_demands = []
        warnings = []
        
        # Check for infinite resource requirements
        for pattern_type, patterns in self.infeasible_patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, amendment_text, re.IGNORECASE)
                if matches:
                    if pattern_type == "infinite_resources":
                        infeasible_demands.append(f"Infinite resource requirement: {matches[0]}")
                    elif pattern_type == "impossible_performance":
                        infeasible_demands.append(f"Impossible performance requirement: {matches[0]}")
                    elif pattern_type == "unsupported_technologies":
                        warnings.append(f"Unsupported technology requirement: {matches[0]}")
        
        # Check for unreasonable resource demands
        resource_keywords = {
            "memory": ["gb", "terabyte", "petabyte"],
            "storage": ["gb", "terabyte", "petabyte"],
            "processing": ["cpu", "cores", "threads"],
            "bandwidth": ["gbps", "terabit"]
        }
        
        for resource_type, units in resource_keywords.items():
            for unit in units:
                if unit in amendment_text.lower():
                    warnings.append(f"High resource requirement detected: {resource_type} in {unit}")
        
        status = "fail" if infeasible_demands else "warning" if warnings else "pass"
        
        return {
            "check_type": "resource_requirements",
            "status": status,
            "infeasible_demands": infeasible_demands,
            "warnings": warnings,
            "details": f"Found {len(infeasible_demands)} infeasible demands, {len(warnings)} warnings"
        }
    
    def _check_implementation_complexity(self, amendment_text: str, changed_files: List[str] = None) -> Dict[str, Any]:
        """Check if amendment is implementable with current complexity."""
        warnings = []
        
        # Check for complex architectural changes
        complexity_indicators = [
            "rewrite", "refactor", "restructure", "redesign",
            "new architecture", "new framework", "new database",
            "migration", "data migration", "schema change"
        ]
        
        for indicator in complexity_indicators:
            if indicator in amendment_text.lower():
                warnings.append(f"High complexity change detected: {indicator}")
        
        # Check for multiple file changes (indicates complexity)
        if changed_files and len(changed_files) > 10:
            warnings.append(f"Large number of file changes: {len(changed_files)} files")
        
        # Check for new technology requirements
        new_tech_indicators = [
            "new technology", "new library", "new dependency",
            "external service", "third party", "api integration"
        ]
        
        for indicator in new_tech_indicators:
            if indicator in amendment_text.lower():
                warnings.append(f"New technology requirement: {indicator}")
        
        status = "warning" if warnings else "pass"
        
        return {
            "check_type": "implementation_complexity",
            "status": status,
            "warnings": warnings,
            "details": f"Found {len(warnings)} complexity warnings"
        }
    
    def _check_dependency_analysis(self, amendment_text: str, changed_files: List[str] = None) -> Dict[str, Any]:
        """Check if amendment has feasible dependencies."""
        warnings = []
        
        # Check for external dependencies
        external_deps = [
            "external api", "third party", "external service",
            "cloud service", "saas", "external database"
        ]
        
        for dep in external_deps:
            if dep in amendment_text.lower():
                warnings.append(f"External dependency detected: {dep}")
        
        # Check for new internal dependencies
        if changed_files:
            new_modules = []
            for file_path in changed_files:
                if file_path.startswith("backend/") and file_path.endswith(".py"):
                    module_name = file_path.replace("backend/", "").replace(".py", "").replace("/", ".")
                    if module_name not in self._get_existing_modules():
                        new_modules.append(module_name)
            
            if new_modules:
                warnings.append(f"New modules required: {', '.join(new_modules[:3])}")
        
        status = "warning" if warnings else "pass"
        
        return {
            "check_type": "dependency_analysis",
            "status": status,
            "warnings": warnings,
            "details": f"Found {len(warnings)} dependency warnings"
        }
    
    def _get_existing_modules(self) -> Set[str]:
        """Get list of existing modules in the backend."""
        existing_modules = set()
        
        # Add known modules from architecture
        for category in ["api_endpoints", "services", "models"]:
            for module in self.architecture[category].keys():
                existing_modules.add(module)
        
        # Add common Python modules
        common_modules = [
            "os", "sys", "json", "re", "datetime", "pathlib", "typing",
            "fastapi", "sqlalchemy", "pydantic", "alembic", "redis"
        ]
        existing_modules.update(common_modules)
        
        return existing_modules
    
    def _run_placeholder_check(self, check_id: str, check_config: Dict[str, Any]) -> Dict[str, Any]:
        """Run placeholder feasibility check."""
        return {
            "check_type": check_id,
            "status": "pass",
            "details": f"Placeholder check - pass",
            "timestamp": datetime.now().isoformat()
        }
    
    def display_feasibility_report(self, validation_result: Dict[str, Any]) -> None:
        """Display a comprehensive feasibility report."""
        print(f"\n�� TECHNICAL FEASIBILITY REPORT")
        print("=" * 40)
        print(f"Overall Status: {validation_result['overall_status'].upper()}")
        print(f"Infeasible Demands: {len(validation_result['infeasible_demands'])}")
        print(f"Warnings: {len(validation_result['warnings'])}")
        
        # Display check results
        print(f"\n🔍 FEASIBILITY CHECK RESULTS")
        print("-" * 30)
        for check_id, check_result in validation_result["checks"].items():
            status_icon = "❌" if check_result["status"] == "fail" else "⚠️" if check_result["status"] == "warning" else "✅"
            print(f"{status_icon} {check_result['check_type']}: {check_result['status']}")
            
            if check_result.get("infeasible_demands"):
                for demand in check_result["infeasible_demands"][:2]:  # Show first 2
                    print(f"   ❌ {demand}")
            
            if check_result.get("warnings"):
                for warning in check_result["warnings"][:2]:  # Show first 2
                    print(f"   ⚠️  {warning}")
        
        # Display infeasible demands
        if validation_result["infeasible_demands"]:
            print(f"\n🚨 INFEASIBLE DEMANDS")
            print("-" * 20)
            for demand in validation_result["infeasible_demands"]:
                print(f"❌ {demand}")
        
        # Display warnings
        if validation_result["warnings"]:
            print(f"\n⚠️  WARNINGS")
            print("-" * 10)
            for warning in validation_result["warnings"]:
                print(f"⚠️  {warning}")
        
        # Display recommendations
        if validation_result["recommendations"]:
            print(f"\n💡 RECOMMENDATIONS")
            print("-" * 15)
            for recommendation in validation_result["recommendations"]:
                print(f"• {recommendation}")
        
        # Final status
        print(f"\n🎯 FINAL STATUS: {validation_result['overall_status'].upper()}")
        if validation_result["overall_status"] == "passed":
            print("✅ Amendment is technically feasible - may proceed")
        elif validation_result["overall_status"] == "warning":
            print("⚠️  Amendment has complexity warnings - review recommended")
        else:
            print("❌ Amendment is technically infeasible - address issues before proceeding")


def main():
    """Main CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Constitutional Feasibility Validator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python constitutional_feasibility_validator.py --validate --text "Add new API endpoint"
  python constitutional_feasibility_validator.py --validate --file amendment.txt
  python constitutional_feasibility_validator.py --architecture
  python constitutional_feasibility_validator.py --list-checks
        """
    )
    
    parser.add_argument(
        '--validate', '-v',
        action='store_true',
        help='Validate amendment feasibility'
    )
    
    parser.add_argument(
        '--text', '-t',
        help='Amendment text to validate'
    )
    
    parser.add_argument(
        '--file', '-f',
        help='File containing amendment text to validate'
    )
    
    parser.add_argument(
        '--architecture', '-a',
        action='store_true',
        help='Show current architecture'
    )
    
    parser.add_argument(
        '--list-checks', '-l',
        action='store_true',
        help='List available feasibility checks'
    )
    
    parser.add_argument(
        '--output', '-o',
        help='Output file for results (JSON format)'
    )
    
    args = parser.parse_args()
    
    validator = ConstitutionalFeasibilityValidator()
    
    if args.architecture:
        print("🏗️ CURRENT ARCHITECTURE")
        print("=" * 25)
        for category, components in CURRENT_ARCHITECTURE.items():
            print(f"\n{category.upper()}:")
            if isinstance(components, dict):
                for component, details in components.items():
                    if isinstance(details, list):
                        print(f"  {component}: {len(details)} items")
                    else:
                        print(f"  {component}: {details}")
            else:
                print(f"  {components}")
        return
    
    if args.list_checks:
        print("🔍 AVAILABLE FEASIBILITY CHECKS")
        print("=" * 35)
        for check_id, check_config in FEASIBILITY_CHECKS.items():
            print(f"\n{check_id}:")
            print(f"  Name: {check_config['name']}")
            print(f"  Description: {check_config['description']}")
            print(f"  Severity: {check_config['severity']}")
        return
    
    if args.validate:
        if not args.text and not args.file:
            print("❌ --validate requires either --text or --file")
            sys.exit(1)
        
        # Get amendment text
        if args.text:
            amendment_text = args.text
        else:
            with open(args.file, 'r') as f:
                amendment_text = f.read()
        
        # Validate feasibility
        validation_result = validator.validate_feasibility(amendment_text)
        
        # Display report
        validator.display_feasibility_report(validation_result)
        
        # Save results if requested
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(validation_result, f, indent=2)
            print(f"\n📄 Results saved to: {args.output}")
        
        # Exit with appropriate code
        if validation_result["overall_status"] == "failed":
            sys.exit(1)
        elif validation_result["overall_status"] == "warning":
            sys.exit(2)
        else:
            sys.exit(0)
    
    else:
        print("❌ Must specify one of: --validate, --architecture, or --list-checks")
        sys.exit(1)


if __name__ == "__main__":
    main()
