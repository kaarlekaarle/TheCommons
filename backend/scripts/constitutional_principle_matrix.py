#!/usr/bin/env python3
"""
Constitutional Principle Matrix

This script defines the untouchable core principles of The Commons Delegation Constitution
and provides validation rules to ensure amendments don't violate these principles.
"""

import os
import sys
import json
import re
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import subprocess

# Untouchable Core Principles - These are ABSOLUTE and never modifiable
UNTOUCHABLE_CORE_PRINCIPLES = {
    "power_circulation": {
        "name": "Power Must Circulate",
        "description": "Delegation is never a one-time handover. All delegated power must remain in motion.",
        "core_rule": "delegations must be revocable",
        "violation_keywords": [
            "permanent delegation", "irrevocable", "locked delegation", "fixed delegation",
            "static power", "immutable delegation", "unchangeable delegation", "final delegation",
            "delegation forever", "permanent transfer", "irreversible delegation"
        ],
        "protection_keywords": [
            "revocable", "revocation", "circulation", "motion", "fluid", "dynamic",
            "changeable", "modifiable", "temporary", "expiry", "auto-revoke"
        ],
        "file_patterns": [
            r".*delegation.*permanent.*",
            r".*delegation.*irrevocable.*",
            r".*delegation.*locked.*",
            r".*delegation.*fixed.*"
        ],
        "schema_constraints": [
            "no_permanent_flag",
            "revocation_capability_required",
            "expiry_mechanism_required"
        ]
    },
    "user_supremacy": {
        "name": "User Intent Supremacy",
        "description": "User intent always wins, instantly. No delegate can override user decisions.",
        "core_rule": "user intent always wins",
        "violation_keywords": [
            "delegate override", "delegate decision", "delegate authority", "delegate control",
            "user cannot override", "delegate final say", "delegate veto", "delegate approval required",
            "user blocked", "user restricted", "delegate permission", "delegate consent"
        ],
        "protection_keywords": [
            "user override", "user control", "user decision", "user intent", "user choice",
            "immediate override", "instant override", "user veto", "user approval"
        ],
        "file_patterns": [
            r".*delegate.*override.*user.*",
            r".*user.*cannot.*override.*",
            r".*delegate.*final.*say.*",
            r".*delegate.*permission.*required.*"
        ],
        "schema_constraints": [
            "user_override_capability_required",
            "no_delegate_veto",
            "immediate_user_control"
        ]
    },
    "radical_transparency": {
        "name": "Radical Transparency",
        "description": "All delegation flows must be visible and understandable.",
        "core_rule": "all flows must be visible",
        "violation_keywords": [
            "hidden delegation", "private delegation", "secret delegation", "opaque delegation",
            "confidential delegation", "anonymous delegation", "masked delegation", "obscured delegation",
            "invisible delegation", "concealed delegation", "delegation behind scenes"
        ],
        "protection_keywords": [
            "transparent", "visible", "public", "open", "auditable", "trackable",
            "logged", "monitored", "reported", "disclosed", "traceable"
        ],
        "file_patterns": [
            r".*hidden.*delegation.*",
            r".*private.*delegation.*",
            r".*secret.*delegation.*",
            r".*opaque.*delegation.*"
        ],
        "schema_constraints": [
            "all_delegations_logged",
            "chain_visibility_required",
            "no_hidden_layers"
        ]
    },
    "anti_hierarchy": {
        "name": "Prevent New Hierarchies",
        "description": "The system must actively resist concentration of delegations into super-representatives.",
        "core_rule": "no power concentration",
        "violation_keywords": [
            "super delegate", "super representative", "hierarchy", "rank", "level", "tier",
            "privileged delegate", "elite delegate", "vip delegate", "admin delegate",
            "moderator delegate", "authority delegate", "power concentration", "delegation monopoly",
            "super-delegate", "super_delegate", "superdelegate"
        ],
        "protection_keywords": [
            "flat", "equal", "distributed", "decentralized", "peer", "democratic",
            "consensus", "collective", "shared", "rotating", "diversity"
        ],
        "file_patterns": [
            r".*super.*delegate.*",
            r".*hierarchy.*delegation.*",
            r".*privileged.*delegate.*",
            r".*power.*concentration.*"
        ],
        "schema_constraints": [
            "no_privileged_classes",
            "concentration_limits_required",
            "diversity_enforcement"
        ]
    }
}

# Validation rule types
VALIDATION_RULE_TYPES = {
    "keyword_check": {
        "name": "Keyword Violation Check",
        "description": "Check for violation keywords in amendment text",
        "severity": "critical"
    },
    "pattern_check": {
        "name": "Pattern Violation Check", 
        "description": "Check for violation patterns in file changes",
        "severity": "critical"
    },
    "schema_check": {
        "name": "Schema Constraint Check",
        "description": "Check for schema constraint violations",
        "severity": "critical"
    },
    "protection_check": {
        "name": "Protection Mechanism Check",
        "description": "Check for presence of protection mechanisms",
        "severity": "warning"
    },
    "delegation_graph_check": {
        "name": "Delegation Graph Analysis",
        "description": "Analyze delegation graph for super-delegate patterns",
        "severity": "critical"
    }
}


class ConstitutionalPrincipleMatrix:
    """Matrix for validating constitutional principle integrity."""
    
    def __init__(self):
        self.principles = UNTOUCHABLE_CORE_PRINCIPLES
        self.validation_rules = VALIDATION_RULE_TYPES
    
    def validate_amendment_integrity(self, amendment_text: str, changed_files: List[str] = None) -> Dict[str, Any]:
        """Validate amendment against all core principles."""
        print("🏛️ PHILOSOPHICAL INTEGRITY VALIDATION")
        print("=" * 45)
        
        validation_result = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "unknown",
            "principles_validated": {},
            "critical_violations": [],
            "warnings": [],
            "recommendations": []
        }
        
        # Validate each principle
        for principle_id, principle in self.principles.items():
            print(f"Validating {principle['name']}...")
            
            principle_result = self._validate_principle(principle_id, principle, amendment_text, changed_files)
            validation_result["principles_validated"][principle_id] = principle_result
            
            # Collect violations and warnings
            if principle_result["violations"]:
                validation_result["critical_violations"].extend(principle_result["violations"])
            
            if principle_result["warnings"]:
                validation_result["warnings"].extend(principle_result["warnings"])
        
        # Special validation for delegation graph analysis
        if changed_files and any("delegation" in f.lower() for f in changed_files):
            print("Analyzing delegation graph for super-delegate patterns...")
            graph_result = self._validate_delegation_graph(changed_files)
            if graph_result["violations"]:
                validation_result["critical_violations"].extend(graph_result["violations"])
            if graph_result["warnings"]:
                validation_result["warnings"].extend(graph_result["warnings"])
        
        # Determine overall status
        if validation_result["critical_violations"]:
            validation_result["overall_status"] = "failed"
            validation_result["recommendations"].append("CRITICAL: Address all principle violations before proceeding")
        elif validation_result["warnings"]:
            validation_result["overall_status"] = "warning"
            validation_result["recommendations"].append("WARNING: Review warnings and consider addressing them")
        else:
            validation_result["overall_status"] = "passed"
            validation_result["recommendations"].append("SUCCESS: All core principles maintained")
        
        return validation_result
    
    def _validate_principle(self, principle_id: str, principle: Dict[str, Any], 
                          amendment_text: str, changed_files: List[str] = None) -> Dict[str, Any]:
        """Validate a specific principle against the amendment."""
        principle_result = {
            "principle_id": principle_id,
            "principle_name": principle["name"],
            "core_rule": principle["core_rule"],
            "status": "unknown",
            "violations": [],
            "warnings": [],
            "checks_performed": []
        }
        
        # Keyword violation check
        keyword_violations = self._check_keyword_violations(principle, amendment_text)
        if keyword_violations:
            principle_result["violations"].extend(keyword_violations)
            principle_result["checks_performed"].append("keyword_violation_check")
        
        # Pattern violation check
        if changed_files:
            pattern_violations = self._check_pattern_violations(principle, changed_files)
            if pattern_violations:
                principle_result["violations"].extend(pattern_violations)
                principle_result["checks_performed"].append("pattern_violation_check")
        
        # Protection mechanism check
        protection_warnings = self._check_protection_mechanisms(principle, amendment_text)
        if protection_warnings:
            principle_result["warnings"].extend(protection_warnings)
            principle_result["checks_performed"].append("protection_check")
        
        # Determine principle status
        if principle_result["violations"]:
            principle_result["status"] = "failed"
        elif principle_result["warnings"]:
            principle_result["status"] = "warning"
        else:
            principle_result["status"] = "passed"
        
        return principle_result
    
    def _validate_delegation_graph(self, changed_files: List[str]) -> Dict[str, Any]:
        """Validate delegation graph for super-delegate patterns."""
        graph_result = {
            "check_type": "delegation_graph_analysis",
            "status": "unknown",
            "violations": [],
            "warnings": [],
            "super_delegates_found": [],
            "graph_analysis": {}
        }
        
        try:
            # Analyze delegation-related files for super-delegate patterns
            for file_path in changed_files:
                if "delegation" in file_path.lower():
                    file_violations = self._analyze_delegation_file(file_path)
                    if file_violations:
                        graph_result["violations"].extend(file_violations)
            
            # Check for super-delegate patterns in code
            super_delegate_patterns = self._detect_super_delegate_patterns(changed_files)
            if super_delegate_patterns:
                graph_result["super_delegates_found"] = super_delegate_patterns
                graph_result["violations"].append({
                    "type": "super_delegate_pattern",
                    "severity": "critical",
                    "description": "Super-delegate pattern detected in delegation code",
                    "details": f"Found {len(super_delegate_patterns)} potential super-delegate patterns",
                    "patterns": super_delegate_patterns,
                    "recommendation": "Remove super-delegate patterns to maintain anti-hierarchy principle"
                })
            
            # Determine status
            if graph_result["violations"]:
                graph_result["status"] = "failed"
            else:
                graph_result["status"] = "passed"
                
        except Exception as e:
            graph_result["status"] = "error"
            graph_result["warnings"].append({
                "type": "graph_analysis_error",
                "severity": "warning",
                "description": f"Error analyzing delegation graph: {str(e)}",
                "recommendation": "Review delegation changes manually for super-delegate patterns"
            })
        
        return graph_result
    
    def _detect_super_delegate_patterns(self, changed_files: List[str]) -> List[Dict[str, Any]]:
        """Detect super-delegate patterns in changed files."""
        patterns = []
        
        for file_path in changed_files:
            if "delegation" in file_path.lower() and os.path.exists(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Look for super-delegate patterns
                    super_delegate_patterns = [
                        r'super\s*[-_]?\s*delegate',
                        r'super\s*[-_]?\s*representative',
                        r'privileged\s+delegate',
                        r'elite\s+delegate',
                        r'vip\s+delegate',
                        r'admin\s+delegate',
                        r'moderator\s+delegate',
                        r'authority\s+delegate',
                        r'power\s+concentration',
                        r'delegation\s+monopoly',
                        r'multiple\s+override\s+authority',
                        r'>\s*1\s*direct\s+override',
                        r'more\s+than\s+one\s+direct\s+authority'
                    ]
                    
                    for pattern in super_delegate_patterns:
                        matches = re.finditer(pattern, content, re.IGNORECASE)
                        for match in matches:
                            line_num = content[:match.start()].count('\n') + 1
                            patterns.append({
                                "file": file_path,
                                "line": line_num,
                                "pattern": pattern,
                                "match": match.group(),
                                "context": self._get_line_context(content, line_num)
                            })
                            
                except Exception as e:
                    print(f"Warning: Could not analyze file {file_path}: {e}")
        
        return patterns
    
    def _get_line_context(self, content: str, line_num: int) -> str:
        """Get context around a specific line number."""
        lines = content.split('\n')
        if 0 < line_num <= len(lines):
            start = max(0, line_num - 2)
            end = min(len(lines), line_num + 1)
            context_lines = lines[start:end]
            return '\n'.join(context_lines)
        return ""
    
    def _analyze_delegation_file(self, file_path: str) -> List[Dict[str, Any]]:
        """Analyze a delegation file for constitutional violations."""
        violations = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for super-delegate patterns
            if re.search(r'super\s*[-_]?\s*delegate', content, re.IGNORECASE):
                violations.append({
                    "type": "super_delegate_detected",
                    "severity": "critical",
                    "description": "Super-delegate pattern detected",
                    "file": file_path,
                    "recommendation": "Remove super-delegate patterns to maintain anti-hierarchy principle"
                })
            
            # Check for multiple override authority patterns
            if re.search(r'multiple\s+override\s+authority|>\s*1\s*direct\s+override', content, re.IGNORECASE):
                violations.append({
                    "type": "multiple_override_authority",
                    "severity": "critical",
                    "description": "Multiple override authority pattern detected",
                    "file": file_path,
                    "recommendation": "Ensure no node has more than one direct override authority"
                })
                
        except Exception as e:
            violations.append({
                "type": "file_analysis_error",
                "severity": "warning",
                "description": f"Could not analyze file {file_path}: {e}",
                "file": file_path,
                "recommendation": "Review file manually for constitutional violations"
            })
        
        return violations
    
    def _check_keyword_violations(self, principle: Dict[str, Any], amendment_text: str) -> List[str]:
        """Check for violation keywords in amendment text."""
        amendment_lower = amendment_text.lower()
        violations = []
        
        for keyword in principle["violation_keywords"]:
            if keyword.lower() in amendment_lower:
                violations.append(f"Violation keyword found: '{keyword}'")
        
        return violations
    
    def _check_pattern_violations(self, principle: Dict[str, Any], changed_files: List[str]) -> List[str]:
        """Check for violation patterns in changed files."""
        violations = []
        
        for pattern in principle["file_patterns"]:
            for file_path in changed_files:
                if re.search(pattern, file_path, re.IGNORECASE):
                    violations.append(f"Violation pattern found in {file_path}: '{pattern}'")
        
        return violations
    
    def _check_protection_mechanisms(self, principle: Dict[str, Any], amendment_text: str) -> List[str]:
        """Check for presence of protection mechanisms."""
        amendment_lower = amendment_text.lower()
        warnings = []
        protections_found = 0
        
        for keyword in principle["protection_keywords"]:
            if keyword.lower() in amendment_lower:
                protections_found += 1
        
        if protections_found == 0:
            warnings.append(f"No protection mechanisms found for {principle['name']}")
        
        return warnings
    
    def get_principle_summary(self) -> Dict[str, Any]:
        """Get a summary of all principles."""
        summary = {
            "total_principles": len(self.principles),
            "principles": {}
        }
        
        for principle_id, principle in self.principles.items():
            summary["principles"][principle_id] = {
                "name": principle["name"],
                "core_rule": principle["core_rule"],
                "violation_keywords_count": len(principle["violation_keywords"]),
                "protection_keywords_count": len(principle["protection_keywords"]),
                "file_patterns_count": len(principle["file_patterns"]),
                "schema_constraints_count": len(principle["schema_constraints"])
            }
        
        return summary
    
    def display_validation_report(self, validation_result: Dict[str, Any]) -> None:
        """Display a comprehensive validation report."""
        print(f"\n📋 PHILOSOPHICAL INTEGRITY REPORT")
        print("=" * 40)
        print(f"Overall Status: {validation_result['overall_status'].upper()}")
        print(f"Critical Violations: {len(validation_result['critical_violations'])}")
        print(f"Warnings: {len(validation_result['warnings'])}")
        
        # Display principle results
        print(f"\n🔍 PRINCIPLE VALIDATION RESULTS")
        print("-" * 30)
        for principle_id, principle_result in validation_result["principles_validated"].items():
            status_icon = "❌" if principle_result["status"] == "failed" else "⚠️" if principle_result["status"] == "warning" else "✅"
            print(f"{status_icon} {principle_result['principle_name']}: {principle_result['status']}")
            
            if principle_result["violations"]:
                for violation in principle_result["violations"][:2]:  # Show first 2 violations
                    print(f"   ❌ {violation}")
            
            if principle_result["warnings"]:
                for warning in principle_result["warnings"][:2]:  # Show first 2 warnings
                    print(f"   ⚠️  {warning}")
        
        # Display critical violations
        if validation_result["critical_violations"]:
            print(f"\n🚨 CRITICAL VIOLATIONS")
            print("-" * 20)
            for violation in validation_result["critical_violations"]:
                print(f"❌ {violation}")
        
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
            print("✅ All core principles maintained - amendment may proceed")
        elif validation_result["overall_status"] == "warning":
            print("⚠️  Warnings detected - review recommended before proceeding")
        else:
            print("❌ Critical violations detected - amendment blocked")


def main():
    """Main CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Constitutional Principle Matrix Validation")
    parser.add_argument("--validate", help="Validate amendment text against principles")
    parser.add_argument("--files", nargs="+", help="Changed files to validate")
    parser.add_argument("--output", help="Output file for results")
    parser.add_argument("--detect-super-delegates", action="store_true", help="Detect super-delegate patterns")
    parser.add_argument("--git-changes", action="store_true", help="Use git diff for changed files")
    
    args = parser.parse_args()
    
    matrix = ConstitutionalPrincipleMatrix()
    
    if args.detect_super_delegates:
        print("🚨 SUPER-DELEGATE PATTERN DETECTION")
        print("=" * 40)
        
        # Get changed files
        changed_files = []
        if args.git_changes:
            changed_files = get_git_changed_files()
        elif args.files:
            changed_files = args.files
        
        # Filter for delegation-related files
        delegation_files = [f for f in changed_files if "delegation" in f.lower()]
        
        if not delegation_files:
            print("✅ No delegation files changed - no super-delegate patterns to check")
            return 0
        
        print(f"Analyzing {len(delegation_files)} delegation files for super-delegate patterns...")
        
        # Detect super-delegate patterns
        patterns = matrix._detect_super_delegate_patterns(delegation_files)
        
        if patterns:
            print(f"❌ Found {len(patterns)} super-delegate patterns:")
            for pattern in patterns:
                print(f"  • {pattern['file']}:{pattern['line']} - '{pattern['match']}'")
            print("\n🔒 SUPER-DELEGATE PATTERNS VIOLATE ANTI-HIERARCHY PRINCIPLE")
            print("Remove these patterns to maintain constitutional integrity.")
            return 1
        else:
            print("✅ No super-delegate patterns detected")
            print("Anti-hierarchy principle maintained.")
            return 0
    
    elif args.validate:
        # Validate amendment text
        with open(args.validate, 'r') as f:
            amendment_text = f.read()
        
        changed_files = []
        if args.git_changes:
            changed_files = get_git_changed_files()
        elif args.files:
            changed_files = args.files
        
        result = matrix.validate_amendment_integrity(amendment_text, changed_files)
        
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(result, f, indent=2)
        
        matrix.display_validation_report(result)
        
        return 0 if result["overall_status"] == "passed" else 1
    
    else:
        # Show principle summary
        summary = matrix.get_principle_summary()
        print("📋 CONSTITUTIONAL PRINCIPLE SUMMARY")
        print("=" * 40)
        print(f"Total Principles: {summary['total_principles']}")
        print()
        
        for principle_id, principle_info in summary["principles"].items():
            print(f"{principle_id}:")
            print(f"  Name: {principle_info['name']}")
            print(f"  Core Rule: {principle_info['core_rule']}")
            print(f"  Violation Keywords: {principle_info['violation_keywords_count']}")
            print(f"  Protection Keywords: {principle_info['protection_keywords_count']}")
            print(f"  File Patterns: {principle_info['file_patterns_count']}")
            print(f"  Schema Constraints: {principle_info['schema_constraints_count']}")
            print()
        return 0

def get_git_changed_files() -> List[str]:
    """Get list of changed files from git diff."""
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", "HEAD~1"],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip().split('\n') if result.stdout.strip() else []
    except subprocess.CalledProcessError:
        # If HEAD~1 doesn't exist, get all files
        try:
            result = subprocess.run(
                ["git", "ls-files"],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip().split('\n') if result.stdout.strip() else []
        except subprocess.CalledProcessError:
            return []

if __name__ == "__main__":
    exit(main())
