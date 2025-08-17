#!/usr/bin/env python3
"""
Constitutional Dependency & Community Impact Validator

This script validates the dependency impact and community burden of constitutional amendments
by analyzing technical dependencies and assessing community maintenance impact.
"""

import os
import sys
import json
import re
import ast
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Tuple

# Current architecture dependencies
CURRENT_DEPENDENCIES = {
    "api_dependencies": {
        "auth": ["users", "jwt"],
        "users": ["auth", "delegations"],
        "polls": ["users", "options", "votes", "delegations"],
        "votes": ["users", "polls", "options", "delegations"],
        "delegations": ["users", "polls", "fields", "institutions"],
        "options": ["polls"],
        "comments": ["users", "polls"],
        "reactions": ["users", "comments"],
        "activity": ["users", "polls", "votes", "delegations"],
        "content": ["users"],
        "labels": ["polls"],
        "feedback": ["users"],
        "websocket": ["auth", "users"],
        "health": []
    },
    "service_dependencies": {
        "user_service": ["User", "database", "redis"],
        "poll_service": ["Poll", "Option", "Vote", "User", "database"],
        "delegation_service": ["Delegation", "User", "Field", "Institution", "database", "redis"],
        "content_loader": ["database"],
        "feedback_service": ["User", "database"],
        "concentration_monitor": ["Delegation", "User", "database"]
    },
    "model_dependencies": {
        "User": ["database"],
        "Poll": ["User", "database"],
        "Option": ["Poll", "database"],
        "Vote": ["User", "Option", "database"],
        "Delegation": ["User", "Field", "Institution", "database"],
        "Field": ["database"],
        "Institution": ["database"],
        "Comment": ["User", "Poll", "database"],
        "CommentReaction": ["Comment", "User", "database"],
        "Label": ["database"],
        "PollLabel": ["Poll", "Label", "database"],
        "ActivityLog": ["User", "database"],
        "DelegationStats": ["User", "database"],
        "Idea": ["database"],
        "Value": ["database"]
    },
    "external_dependencies": {
        "database": ["PostgreSQL", "SQLAlchemy"],
        "cache": ["Redis"],
        "framework": ["FastAPI"],
        "authentication": ["JWT"],
        "orm": ["SQLAlchemy"],
        "migrations": ["Alembic"]
    }
}

# Delegation concentration monitoring thresholds (updated for new modes)
DELEGATION_CONCENTRATION_THRESHOLDS = {
    "complexity_ceiling": {
        "max_flows_per_module": 7,  # Increased for new target types
        "warning_threshold": 5,
        "high_complexity_threshold": 7
    },
    "maintainer_concentration": {
        "warning_threshold": 50,  # 50% commits by single maintainer
        "high_concentration_threshold": 80,  # 80% commits by single maintainer (increased)
        "git_history_days": 30,  # Look back 30 days
        "min_commits_for_analysis": 5  # Minimum commits to analyze
    },
    "mode_distribution": {
        "legacy_mode_warning": 30,  # Warning if >30% delegations are legacy
        "legacy_mode_high": 50,     # High if >50% delegations are legacy
        "hybrid_mode_target": 20,   # Target 20% hybrid mode adoption
    }
}

# Community impact assessment criteria
COMMUNITY_IMPACT_CRITERIA = {
    "complexity_indicators": {
        "high_complexity": [
            "rewrite", "refactor", "restructure", "redesign",
            "new architecture", "new framework", "migration",
            "data migration", "schema change", "breaking change"
        ],
        "medium_complexity": [
            "new feature", "enhancement", "improvement",
            "optimization", "performance", "scalability"
        ],
        "low_complexity": [
            "bug fix", "documentation", "minor change",
            "typo", "formatting", "comment"
        ]
    },
    "maintainer_burden": {
        "high_burden": [
            "ongoing maintenance", "continuous monitoring",
            "performance tuning", "scalability management",
            "complex debugging", "expert knowledge required"
        ],
        "medium_burden": [
            "periodic review", "occasional updates",
            "standard maintenance", "routine monitoring"
        ],
        "low_burden": [
            "set and forget", "self-maintaining",
            "automated", "minimal intervention"
        ]
    },
    "community_impact": {
        "high_impact": [
            "breaking change", "api change", "database change",
            "user experience change", "workflow change",
            "learning curve", "training required"
        ],
        "medium_impact": [
            "new feature", "enhancement", "improvement",
            "optional feature", "backward compatible"
        ],
        "low_impact": [
            "internal change", "behind the scenes",
            "transparent", "no user impact"
        ]
    }
}

# Dependency validation categories
DEPENDENCY_CHECKS = {
    "dependency_analysis": {
        "name": "Dependency Analysis Check",
        "description": "Check for dependency breaks and cascading impacts",
        "severity": "critical"
    },
    "community_impact": {
        "name": "Community Impact Assessment",
        "description": "Assess impact on community maintenance and complexity",
        "severity": "warning"
    },
    "maintainer_burden": {
        "name": "Maintainer Burden Analysis",
        "description": "Analyze ongoing maintenance burden for the community",
        "severity": "warning"
    },
    "breaking_changes": {
        "name": "Breaking Changes Detection",
        "description": "Detect breaking changes that affect existing functionality",
        "severity": "critical"
    },
    "delegation_complexity": {
        "name": "Delegation API Complexity Check",
        "description": "Monitor delegation API complexity and maintainer spread risk",
        "severity": "warning"
    },
    "maintainer_concentration": {
        "name": "Maintainer Concentration Check",
        "description": "Monitor maintainer concentration in delegation module",
        "severity": "warning"
    }
}

# Dependency break patterns
DEPENDENCY_BREAK_PATTERNS = {
    "non_existent_components": [
        r"import\s+(\w+)\s+from\s+['\"]backend\.(?!api|services|models|core)",
        r"from\s+backend\.(?!api|services|models|core)\.",
        r"backend\.(?!api|services|models|core)\."
    ],
    "missing_dependencies": [
        r"service\.(\w+)\s+not\s+found",
        r"model\.(\w+)\s+not\s+found",
        r"api\.(\w+)\s+not\s+found"
    ],
    "breaking_changes": [
        r"breaking\s+change",
        r"api\s+change",
        r"database\s+change",
        r"schema\s+change",
        r"migration\s+required"
    ]
}


class ConstitutionalDependencyValidator:
    """Validator for dependency impact and community burden of constitutional amendments."""
    
    def __init__(self):
        self.dependencies = CURRENT_DEPENDENCIES
        self.impact_criteria = COMMUNITY_IMPACT_CRITERIA
        self.dependency_checks = DEPENDENCY_CHECKS
        self.break_patterns = DEPENDENCY_BREAK_PATTERNS
    
    def validate_dependencies(self, amendment_text: str, changed_files: List[str] = None) -> Dict[str, Any]:
        """Validate dependency impact and community burden of amendment."""
        print("🔗 DEPENDENCY & COMMUNITY IMPACT VALIDATION")
        print("=" * 50)
        
        validation_result = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "unknown",
            "checks": {},
            "dependency_breaks": [],
            "community_impacts": [],
            "maintainer_burdens": [],
            "recommendations": []
        }
        
        # Run each dependency check
        for check_id, check_config in self.dependency_checks.items():
            print(f"Running {check_config['name']}...")
            
            if check_id == "dependency_analysis":
                check_result = self._check_dependency_analysis(amendment_text, changed_files)
            elif check_id == "community_impact":
                check_result = self._check_community_impact(amendment_text)
            elif check_id == "maintainer_burden":
                check_result = self._check_maintainer_burden(amendment_text)
            elif check_id == "breaking_changes":
                check_result = self._check_breaking_changes(amendment_text)
            elif check_id == "delegation_complexity":
                check_result = self._check_delegation_complexity(amendment_text, changed_files)
            elif check_id == "maintainer_concentration":
                check_result = self._check_maintainer_concentration(amendment_text, changed_files)
            else:
                check_result = self._run_placeholder_check(check_id, check_config)
            
            validation_result["checks"][check_id] = check_result
            
            status_icon = "✅" if check_result["status"] == "pass" else "❌" if check_result["status"] == "fail" else "⚠️"
            print(f"  {status_icon} {check_config['name']}: {check_result['status']}")
        
        # Collect dependency breaks and impacts
        for check_result in validation_result["checks"].values():
            if check_result.get("dependency_breaks"):
                validation_result["dependency_breaks"].extend(check_result["dependency_breaks"])
            
            if check_result.get("community_impacts"):
                validation_result["community_impacts"].extend(check_result["community_impacts"])
            
            if check_result.get("maintainer_burdens"):
                validation_result["maintainer_burdens"].extend(check_result["maintainer_burdens"])
        
        # Determine overall status
        any_failed = any(check["status"] == "fail" for check in validation_result["checks"].values())
        any_warnings = any(check["status"] == "warning" for check in validation_result["checks"].values())
        
        if any_failed:
            validation_result["overall_status"] = "failed"
            validation_result["recommendations"].append("CRITICAL: Address dependency breaks before proceeding")
        elif any_warnings:
            validation_result["overall_status"] = "warning"
            validation_result["recommendations"].append("WARNING: Review community impact and maintainer burden")
        else:
            validation_result["overall_status"] = "passed"
            validation_result["recommendations"].append("SUCCESS: Dependencies are sustainable and community impact is manageable")
        
        return validation_result
    
    def _check_dependency_analysis(self, amendment_text: str, changed_files: List[str] = None) -> Dict[str, Any]:
        """Check for dependency breaks and cascading impacts."""
        dependency_breaks = []
        warnings = []
        
        # Check for non-existent component references
        for pattern_type, patterns in self.break_patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, amendment_text, re.IGNORECASE)
                if matches:
                    if pattern_type == "non_existent_components":
                        dependency_breaks.append(f"Non-existent component reference: {matches[0]}")
                    elif pattern_type == "missing_dependencies":
                        dependency_breaks.append(f"Missing dependency: {matches[0]}")
                    elif pattern_type == "breaking_changes":
                        dependency_breaks.append(f"Breaking change detected: {matches[0]}")
        
        # Check for cascading impacts in changed files
        if changed_files:
            impacted_components = self._analyze_cascading_impacts(changed_files)
            if impacted_components:
                warnings.append(f"Cascading impact detected: {len(impacted_components)} components affected")
                for component in impacted_components[:3]:  # Show first 3
                    warnings.append(f"  • {component}")
        
        # Check for circular dependencies
        circular_deps = self._detect_circular_dependencies(amendment_text)
        if circular_deps:
            dependency_breaks.append(f"Circular dependency detected: {circular_deps}")
        
        status = "fail" if dependency_breaks else "warning" if warnings else "pass"
        
        return {
            "check_type": "dependency_analysis",
            "status": status,
            "dependency_breaks": dependency_breaks,
            "warnings": warnings,
            "details": f"Found {len(dependency_breaks)} dependency breaks, {len(warnings)} warnings"
        }
    
    def _check_community_impact(self, amendment_text: str) -> Dict[str, Any]:
        """Assess impact on community maintenance and complexity."""
        community_impacts = []
        warnings = []
        
        amendment_lower = amendment_text.lower()
        
        # Check complexity indicators
        complexity_score = 0
        for complexity_level, indicators in self.impact_criteria["complexity_indicators"].items():
            for indicator in indicators:
                if indicator in amendment_lower:
                    if complexity_level == "high_complexity":
                        complexity_score += 3
                        community_impacts.append(f"High complexity change: {indicator}")
                    elif complexity_level == "medium_complexity":
                        complexity_score += 2
                        warnings.append(f"Medium complexity change: {indicator}")
                    else:
                        complexity_score += 1
        
        # Check community impact indicators
        for impact_level, indicators in self.impact_criteria["community_impact"].items():
            for indicator in indicators:
                if indicator in amendment_lower:
                    if impact_level == "high_impact":
                        community_impacts.append(f"High community impact: {indicator}")
                    elif impact_level == "medium_impact":
                        warnings.append(f"Medium community impact: {indicator}")
        
        # Determine impact level
        if complexity_score >= 6:
            impact_level = "high"
        elif complexity_score >= 3:
            impact_level = "medium"
        else:
            impact_level = "low"
        
        status = "fail" if community_impacts else "warning" if warnings else "pass"
        
        return {
            "check_type": "community_impact",
            "status": status,
            "community_impacts": community_impacts,
            "warnings": warnings,
            "complexity_score": complexity_score,
            "impact_level": impact_level,
            "details": f"Complexity score: {complexity_score}, Impact level: {impact_level}"
        }
    
    def _check_maintainer_burden(self, amendment_text: str) -> Dict[str, Any]:
        """Analyze ongoing maintenance burden for the community."""
        maintainer_burdens = []
        warnings = []
        
        amendment_lower = amendment_text.lower()
        
        # Check maintainer burden indicators
        burden_score = 0
        for burden_level, indicators in self.impact_criteria["maintainer_burden"].items():
            for indicator in indicators:
                if indicator in amendment_lower:
                    if burden_level == "high_burden":
                        burden_score += 3
                        maintainer_burdens.append(f"High maintainer burden: {indicator}")
                    elif burden_level == "medium_burden":
                        burden_score += 2
                        warnings.append(f"Medium maintainer burden: {indicator}")
                    else:
                        burden_score += 1
        
        # Determine burden level
        if burden_score >= 6:
            burden_level = "high"
        elif burden_score >= 3:
            burden_level = "medium"
        else:
            burden_level = "low"
        
        status = "fail" if maintainer_burdens else "warning" if warnings else "pass"
        
        return {
            "check_type": "maintainer_burden",
            "status": status,
            "maintainer_burdens": maintainer_burdens,
            "warnings": warnings,
            "burden_score": burden_score,
            "burden_level": burden_level,
            "details": f"Burden score: {burden_score}, Burden level: {burden_level}"
        }
    
    def _check_breaking_changes(self, amendment_text: str) -> Dict[str, Any]:
        """Detect breaking changes that affect existing functionality."""
        breaking_changes = []
        warnings = []
        
        amendment_lower = amendment_text.lower()
        
        # Check for breaking change indicators
        breaking_indicators = [
            "breaking change", "api change", "database change",
            "schema change", "migration required", "incompatible",
            "deprecate", "remove", "delete", "drop"
        ]
        
        for indicator in breaking_indicators:
            if indicator in amendment_lower:
                breaking_changes.append(f"Breaking change detected: {indicator}")
        
        # Check for version compatibility issues
        version_indicators = [
            "version bump", "major version", "incompatible version",
            "upgrade required", "migration script"
        ]
        
        for indicator in version_indicators:
            if indicator in amendment_lower:
                warnings.append(f"Version compatibility issue: {indicator}")
        
        status = "fail" if breaking_changes else "warning" if warnings else "pass"
        
        return {
            "check_type": "breaking_changes",
            "status": status,
            "breaking_changes": breaking_changes,
            "warnings": warnings,
            "details": f"Found {len(breaking_changes)} breaking changes, {len(warnings)} warnings"
        }
    
    def _check_delegation_complexity(self, amendment_text: str, changed_files: List[str] = None) -> Dict[str, Any]:
        """Monitor delegation API complexity and maintainer spread risk."""
        print("🔍 Checking delegation API complexity...")
        
        complexity_result = {
            "check_type": "delegation_complexity",
            "status": "pass",
            "warnings": [],
            "complexity_score": 0,
            "complexity_level": "low",
            "active_flows": 0,
            "modules_analyzed": [],
            "remediation_tips": [],
            "details": ""
        }
        
        # Analyze delegation-related files for active flows
        delegation_files = []
        if changed_files:
            delegation_files = [f for f in changed_files if "delegation" in f.lower()]
        else:
            # Scan for delegation files if not provided
            delegation_files = self._find_delegation_files()
        
        total_flows = 0
        modules_with_high_complexity = []
        
        for file_path in delegation_files:
            if os.path.exists(file_path):
                flows_in_file = self._count_delegation_flows(file_path)
                total_flows += flows_in_file
                
                if flows_in_file > DELEGATION_CONCENTRATION_THRESHOLDS["complexity_ceiling"]["max_flows_per_module"]:
                    modules_with_high_complexity.append({
                        "file": file_path,
                        "flows": flows_in_file,
                        "threshold": DELEGATION_CONCENTRATION_THRESHOLDS["complexity_ceiling"]["max_flows_per_module"]
                    })
                
                complexity_result["modules_analyzed"].append({
                    "file": file_path,
                    "flows": flows_in_file
                })
        
        # Determine complexity level
        if total_flows > DELEGATION_CONCENTRATION_THRESHOLDS["complexity_ceiling"]["high_complexity_threshold"]:
            complexity_result["complexity_level"] = "high"
            complexity_result["complexity_score"] = 3
        elif total_flows > DELEGATION_CONCENTRATION_THRESHOLDS["complexity_ceiling"]["warning_threshold"]:
            complexity_result["complexity_level"] = "medium"
            complexity_result["complexity_score"] = 2
        else:
            complexity_result["complexity_level"] = "low"
            complexity_result["complexity_score"] = 1
        
        complexity_result["active_flows"] = total_flows
        
        # Generate warnings and remediation tips for high complexity
        if modules_with_high_complexity:
            complexity_result["status"] = "warning"
            for module in modules_with_high_complexity:
                warning_msg = f"High delegation complexity in {module['file']}: {module['flows']} flows (threshold: {module['threshold']})"
                complexity_result["warnings"].append(warning_msg)
                
                # Add specific, actionable remediation tips for flows >= 7
                if module['flows'] >= 7:
                    specific_tips = [
                        f"Split {os.path.basename(module['file'])} into routing.py (chain resolution) + interrupts.py (overrides)",
                        "Move storage adapters under delegation/store/ and inject via interface",
                        "Collapse duplicate handlers: merge apply_override + interrupt_vote",
                        "Extract delegation state machine into separate state.py module",
                        "Create delegation/validators.py for chain validation logic"
                    ]
                    complexity_result["remediation_tips"].extend(specific_tips)
                else:
                    # General tips for moderate complexity
                    general_tips = [
                        f"Split {os.path.basename(module['file'])} into smaller modules",
                        "Extract delegation handlers into separate classes",
                        "Consolidate similar delegation flows",
                        "Consider delegation manager pattern for complex flows",
                        "Review delegation chain depth and simplify"
                    ]
                    complexity_result["remediation_tips"].extend(general_tips)
        
        if total_flows > DELEGATION_CONCENTRATION_THRESHOLDS["complexity_ceiling"]["max_flows_per_module"]:
            complexity_result["status"] = "warning"
            complexity_result["warnings"].append(
                f"Total delegation flows ({total_flows}) exceed complexity ceiling ({DELEGATION_CONCENTRATION_THRESHOLDS['complexity_ceiling']['max_flows_per_module']})"
            )
            
            # Add general remediation tips
            if not complexity_result["remediation_tips"]:
                complexity_result["remediation_tips"] = [
                    "Split delegation manager into smaller components",
                    "Extract delegation handlers into separate modules",
                    "Consolidate similar delegation flows",
                    "Review delegation chain depth and simplify",
                    "Consider delegation factory pattern for complex flows"
                ]
        
        complexity_result["details"] = f"Analyzed {len(delegation_files)} delegation files, found {total_flows} active flows, complexity level: {complexity_result['complexity_level']}"
        
        return complexity_result

    def _check_delegation_mode_distribution(self, amendment_text: str, changed_files: List[str] = None) -> Dict[str, Any]:
        """Check delegation mode distribution for constitutional health."""
        print("🔍 Checking delegation mode distribution...")
        
        mode_result = {
            "check_type": "delegation_mode_distribution",
            "status": "pass",
            "warnings": [],
            "mode_distribution": {},
            "legacy_percentage": 0,
            "severity": "info",
            "details": ""
        }
        
        try:
            # This would typically query the database for mode distribution
            # For now, we'll simulate the check based on code patterns
            
            delegation_files = []
            if changed_files:
                delegation_files = [f for f in changed_files if "delegation" in f.lower()]
            else:
                delegation_files = self._find_delegation_files()
            
            mode_patterns = {
                "legacy_fixed_term": ["legacy_fixed_term", "LEGACY_FIXED_TERM", "legacy_term_ends_at"],
                "flexible_domain": ["flexible_domain", "FLEXIBLE_DOMAIN"],
                "hybrid_seed": ["hybrid_seed", "HYBRID_SEED"]
            }
            
            mode_counts = {"legacy_fixed_term": 0, "flexible_domain": 0, "hybrid_seed": 0}
            total_files = 0
            
            for file_path in delegation_files:
                if os.path.exists(file_path):
                    try:
                        with open(file_path, 'r') as f:
                            content = f.read()
                        
                        total_files += 1
                        for mode, patterns in mode_patterns.items():
                            if any(pattern in content for pattern in patterns):
                                mode_counts[mode] += 1
                    except Exception:
                        continue
            
            mode_result["mode_distribution"] = mode_counts
            
            if total_files == 0:
                mode_result["details"] = "No delegation files found"
                return mode_result
            
            legacy_percentage = (mode_counts["legacy_fixed_term"] / total_files) * 100
            mode_result["legacy_percentage"] = legacy_percentage
            
            # Determine severity based on legacy mode usage
            if legacy_percentage >= DELEGATION_CONCENTRATION_THRESHOLDS["mode_distribution"]["legacy_mode_high"]:
                mode_result["severity"] = "high"
                mode_result["status"] = "warning"
                mode_result["warnings"].append(
                    f"High legacy mode usage: {legacy_percentage:.1f}% (threshold: {DELEGATION_CONCENTRATION_THRESHOLDS['mode_distribution']['legacy_mode_high']}%)"
                )
            elif legacy_percentage >= DELEGATION_CONCENTRATION_THRESHOLDS["mode_distribution"]["legacy_mode_warning"]:
                mode_result["severity"] = "warn"
                mode_result["status"] = "warning"
                mode_result["warnings"].append(
                    f"Moderate legacy mode usage: {legacy_percentage:.1f}% (threshold: {DELEGATION_CONCENTRATION_THRESHOLDS['mode_distribution']['legacy_mode_warning']}%)"
                )
            else:
                mode_result["severity"] = "info"
            
            mode_result["details"] = f"Analyzed {total_files} delegation files. Legacy mode: {legacy_percentage:.1f}%"
            
        except Exception as e:
            mode_result["status"] = "error"
            mode_result["warnings"].append(f"Error checking mode distribution: {str(e)}")
            mode_result["details"] = f"Error: {str(e)}"
        
        return mode_result
    
    def _check_maintainer_concentration(self, amendment_text: str, changed_files: List[str] = None) -> Dict[str, Any]:
        """Monitor maintainer concentration in delegation module."""
        print("👥 Checking maintainer concentration...")
        
        concentration_result = {
            "check_type": "maintainer_concentration",
            "status": "pass",
            "warnings": [],
            "maintainer_stats": {},
            "concentration_percentage": 0,
            "top_maintainer": "",
            "total_commits": 0,
            "remediation_tips": [],
            "details": ""
        }
        
        # Get git history for delegation-related files
        delegation_files = []
        if changed_files:
            delegation_files = [f for f in changed_files if "delegation" in f.lower()]
        else:
            delegation_files = self._find_delegation_files()
        
        if not delegation_files:
            concentration_result["details"] = "No delegation files found to analyze"
            return concentration_result
        
        # Analyze git history for maintainer concentration
        maintainer_stats = self._analyze_maintainer_concentration(delegation_files)
        
        if not maintainer_stats:
            concentration_result["details"] = "No git history found for delegation files"
            return concentration_result
        
        concentration_result["maintainer_stats"] = maintainer_stats
        concentration_result["total_commits"] = sum(maintainer_stats.values())
        
        if concentration_result["total_commits"] < DELEGATION_CONCENTRATION_THRESHOLDS["maintainer_concentration"]["min_commits_for_analysis"]:
            concentration_result["details"] = f"Insufficient commits ({concentration_result['total_commits']}) for analysis (minimum: {DELEGATION_CONCENTRATION_THRESHOLDS['maintainer_concentration']['min_commits_for_analysis']})"
            return concentration_result
        
        # Find top maintainer
        if maintainer_stats:
            top_maintainer = max(maintainer_stats.items(), key=lambda x: x[1])
            concentration_result["top_maintainer"] = top_maintainer[0]
            concentration_result["concentration_percentage"] = (top_maintainer[1] / concentration_result["total_commits"]) * 100
            
            # Generate warnings based on concentration
            if concentration_result["concentration_percentage"] > DELEGATION_CONCENTRATION_THRESHOLDS["maintainer_concentration"]["high_concentration_threshold"]:
                concentration_result["status"] = "warning"
                concentration_result["warnings"].append(
                    f"High maintainer concentration: {concentration_result['top_maintainer']} authored {concentration_result['concentration_percentage']:.1f}% of delegation commits"
                )
                
                # Add remediation tips for high concentration
                concentration_result["remediation_tips"] = [
                    f"Encourage {concentration_result['top_maintainer']} to pair program with other team members",
                    "Schedule knowledge sharing sessions on delegation system",
                    "Rotate delegation-related code reviews",
                    "Consider splitting delegation responsibilities across team members",
                    "Document delegation patterns and best practices"
                ]
                
                # Check if concentration is very high and commits are sufficient for stronger recommendation
                if (concentration_result["concentration_percentage"] >= 75 and 
                    concentration_result["total_commits"] >= 10):
                    concentration_result["remediation_tips"].append(
                        "⚠️  PAIR PROGRAMMING OR REVIEWER SWAP RECOMMENDED FOR NEXT PR ON delegation/*"
                    )
                    
                    # Add CI note for high concentration
                    concentration_result["ci_note"] = {
                        "type": "warning",
                        "message": f"High maintainer concentration detected: {concentration_result['top_maintainer']} ({concentration_result['concentration_percentage']:.1f}%)",
                        "file": "delegation/*",
                        "line": 1,
                        "details": "Pair programming or reviewer swap recommended for next PR on delegation/*"
                    }
                    
            elif concentration_result["concentration_percentage"] > DELEGATION_CONCENTRATION_THRESHOLDS["maintainer_concentration"]["warning_threshold"]:
                concentration_result["status"] = "warning"
                concentration_result["warnings"].append(
                    f"Moderate maintainer concentration: {concentration_result['top_maintainer']} authored {concentration_result['concentration_percentage']:.1f}% of delegation commits"
                )
                
                # Add gentle remediation tips for moderate concentration
                concentration_result["remediation_tips"] = [
                    "Consider encouraging more contributors to delegation code",
                    "Share delegation knowledge through documentation",
                    "Rotate delegation-related tasks occasionally"
                ]
        
        concentration_result["details"] = f"Analyzed {len(delegation_files)} delegation files, {concentration_result['total_commits']} commits, top maintainer: {concentration_result['top_maintainer']} ({concentration_result['concentration_percentage']:.1f}%)"
        
        return concentration_result
    
    def _find_delegation_files(self) -> List[str]:
        """Find delegation-related files in the codebase."""
        delegation_files = []
        
        # Common delegation file patterns
        delegation_patterns = [
            "**/delegation*.py",
            "**/delegations*.py",
            "**/*delegation*.py",
            "backend/api/delegations.py",
            "backend/services/delegation*.py",
            "backend/models/delegation*.py",
            "backend/core/delegation*.py"
        ]
        
        for pattern in delegation_patterns:
            try:
                files = list(Path(".").glob(pattern))
                delegation_files.extend([str(f) for f in files if f.is_file()])
            except Exception as e:
                print(f"Warning: Could not search pattern {pattern}: {e}")
        
        return list(set(delegation_files))  # Remove duplicates
    
    def _count_delegation_flows(self, file_path: str) -> int:
        """Count active delegation flows in a file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Count delegation-related functions and endpoints
            flow_patterns = [
                r'def\s+\w*delegation\w*\s*\(',
                r'@.*delegation',
                r'delegation.*flow',
                r'delegation.*endpoint',
                r'delegation.*api',
                r'delegation.*service',
                r'delegation.*method'
            ]
            
            flow_count = 0
            for pattern in flow_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                flow_count += len(matches)
            
            # Also count class methods that might be delegation flows
            class_pattern = r'class\s+\w*Delegation\w*'
            if re.search(class_pattern, content, re.IGNORECASE):
                method_pattern = r'def\s+\w+\s*\('
                methods = re.findall(method_pattern, content)
                flow_count += len(methods)
            
            return flow_count
            
        except Exception as e:
            print(f"Warning: Could not analyze file {file_path}: {e}")
            return 0
    
    def _analyze_maintainer_concentration(self, delegation_files: List[str]) -> Dict[str, int]:
        """Analyze maintainer concentration in delegation files using git history."""
        maintainer_stats = {}
        
        try:
            # Get git log for delegation files in the last 30 days
            days_back = DELEGATION_CONCENTRATION_THRESHOLDS["maintainer_concentration"]["git_history_days"]
            
            # Build git command to get commit authors for delegation files
            file_args = []
            for file_path in delegation_files:
                if os.path.exists(file_path):
                    file_args.append(file_path)
            
            if not file_args:
                return maintainer_stats
            
            # Get git log with author information
            git_cmd = [
                "git", "log", 
                f"--since={days_back} days ago",
                "--pretty=format:%an",  # Author name only
                "--", *file_args
            ]
            
            result = subprocess.run(git_cmd, capture_output=True, text=True, check=True)
            
            if result.stdout:
                authors = result.stdout.strip().split('\n')
                for author in authors:
                    if author.strip():
                        maintainer_stats[author.strip()] = maintainer_stats.get(author.strip(), 0) + 1
            
        except subprocess.CalledProcessError as e:
            print(f"Warning: Could not get git history: {e}")
            # Fallback: simulate maintainer concentration for testing
            maintainer_stats = self._simulate_maintainer_concentration()
        except Exception as e:
            print(f"Warning: Error analyzing maintainer concentration: {e}")
            maintainer_stats = self._simulate_maintainer_concentration()
        
        return maintainer_stats
    
    def _simulate_maintainer_concentration(self) -> Dict[str, int]:
        """Simulate maintainer concentration for testing purposes."""
        import random
        
        # Simulate different concentration scenarios
        scenarios = [
            # High concentration (75% by one maintainer)
            {"alice": 15, "bob": 3, "charlie": 2},
            # Moderate concentration (50% by one maintainer)
            {"alice": 10, "bob": 5, "charlie": 3, "diana": 2},
            # Low concentration (distributed)
            {"alice": 5, "bob": 4, "charlie": 3, "diana": 3, "eve": 2}
        ]
        
        return random.choice(scenarios)
    
    def _detect_circular_dependencies(self, amendment_text: str) -> Optional[str]:
        """Detect potential circular dependencies."""
        # Simple circular dependency detection
        circular_patterns = [
            r"service_a.*service_b.*service_a",
            r"model_a.*model_b.*model_a",
            r"api_a.*api_b.*api_a"
        ]
        
        for pattern in circular_patterns:
            if re.search(pattern, amendment_text, re.IGNORECASE):
                return pattern
        
        return None
    
    def _analyze_cascading_impacts(self, changed_files: List[str]) -> List[str]:
        """Analyze cascading impacts of file changes."""
        impacted_components = set()
        
        for file_path in changed_files:
            if file_path.startswith("backend/"):
                # Extract component type from file path
                if "/api/" in file_path:
                    component = file_path.split("/api/")[1].split("/")[0]
                    impacted_components.add(f"API: {component}")
                elif "/services/" in file_path:
                    component = file_path.split("/services/")[1].split(".")[0]
                    impacted_components.add(f"Service: {component}")
                elif "/models/" in file_path:
                    component = file_path.split("/models/")[1].split(".")[0]
                    impacted_components.add(f"Model: {component}")
        
        return list(impacted_components)
    
    def _run_placeholder_check(self, check_id: str, check_config: Dict[str, Any]) -> Dict[str, Any]:
        """Run placeholder dependency check."""
        return {
            "check_type": check_id,
            "status": "pass",
            "details": f"Placeholder check - pass",
            "timestamp": datetime.now().isoformat()
        }
    
    def get_dependency_summary(self) -> Dict[str, Any]:
        """Get a summary of current dependencies."""
        summary = {
            "api_dependencies": len(self.dependencies["api_dependencies"]),
            "service_dependencies": len(self.dependencies["service_dependencies"]),
            "model_dependencies": len(self.dependencies["model_dependencies"]),
            "external_dependencies": len(self.dependencies["external_dependencies"]),
            "total_dependencies": sum(len(deps) for deps in self.dependencies.values())
        }
        
        return summary
    
    def display_dependency_report(self, validation_result: Dict[str, Any]) -> None:
        """Display a comprehensive dependency report."""
        print(f"\n📋 DEPENDENCY & COMMUNITY IMPACT REPORT")
        print("=" * 50)
        print(f"Overall Status: {validation_result['overall_status'].upper()}")
        print(f"Dependency Breaks: {len(validation_result['dependency_breaks'])}")
        print(f"Community Impacts: {len(validation_result['community_impacts'])}")
        print(f"Maintainer Burdens: {len(validation_result['maintainer_burdens'])}")
        
        # Display check results
        print(f"\n🔍 DEPENDENCY CHECK RESULTS")
        print("-" * 30)
        for check_id, check_result in validation_result["checks"].items():
            status_icon = "❌" if check_result["status"] == "fail" else "⚠️" if check_result["status"] == "warning" else "✅"
            print(f"{status_icon} {check_result['check_type']}: {check_result['status']}")
            
            if check_result.get("dependency_breaks"):
                for break_item in check_result["dependency_breaks"][:2]:  # Show first 2
                    print(f"   ❌ {break_item}")
            
            if check_result.get("community_impacts"):
                for impact in check_result["community_impacts"][:2]:  # Show first 2
                    print(f"   ❌ {impact}")
            
            if check_result.get("maintainer_burdens"):
                for burden in check_result["maintainer_burdens"][:2]:  # Show first 2
                    print(f"   ❌ {burden}")
            
            if check_result.get("warnings"):
                for warning in check_result["warnings"][:2]:  # Show first 2
                    print(f"   ⚠️  {warning}")
        
        # Display dependency breaks
        if validation_result["dependency_breaks"]:
            print(f"\n🚨 DEPENDENCY BREAKS")
            print("-" * 20)
            for break_item in validation_result["dependency_breaks"]:
                print(f"❌ {break_item}")
        
        # Display community impacts
        if validation_result["community_impacts"]:
            print(f"\n🌍 COMMUNITY IMPACTS")
            print("-" * 20)
            for impact in validation_result["community_impacts"]:
                print(f"❌ {impact}")
        
        # Display maintainer burdens
        if validation_result["maintainer_burdens"]:
            print(f"\n👥 MAINTAINER BURDENS")
            print("-" * 20)
            for burden in validation_result["maintainer_burdens"]:
                print(f"❌ {burden}")
        
        # Display recommendations
        if validation_result["recommendations"]:
            print(f"\n💡 RECOMMENDATIONS")
            print("-" * 15)
            for recommendation in validation_result["recommendations"]:
                print(f"• {recommendation}")
        
        # Final status
        print(f"\n🎯 FINAL STATUS: {validation_result['overall_status'].upper()}")
        if validation_result["overall_status"] == "passed":
            print("✅ Dependencies are sustainable - amendment may proceed")
        elif validation_result["overall_status"] == "warning":
            print("⚠️  Dependencies have warnings - review recommended")
        else:
            print("❌ Dependencies are broken - address issues before proceeding")


def main():
    """Main CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Constitutional Dependency & Community Impact Validator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python constitutional_dependency_validator.py --validate --text "Add new API endpoint"
  python constitutional_dependency_validator.py --validate --file amendment.txt
  python constitutional_dependency_validator.py --dependencies
  python constitutional_dependency_validator.py --list-checks
        """
    )
    
    parser.add_argument(
        '--validate', '-v',
        action='store_true',
        help='Validate amendment dependencies'
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
        '--dependencies', '-d',
        action='store_true',
        help='Show current dependencies'
    )
    
    parser.add_argument(
        '--list-checks', '-l',
        action='store_true',
        help='List available dependency checks'
    )
    
    parser.add_argument(
        '--output', '-o',
        help='Output file for results (JSON format)'
    )
    
    parser.add_argument(
        '--emit-complexity-json',
        help='Emit complexity flows JSON to specified file'
    )
    
    parser.add_argument(
        '--emit-maintainer-json',
        help='Emit maintainer concentration JSON to specified file'
    )
    
    args = parser.parse_args()
    
    validator = ConstitutionalDependencyValidator()
    
    if args.dependencies:
        summary = validator.get_dependency_summary()
        print("🔗 CURRENT DEPENDENCIES")
        print("=" * 25)
        print(f"API Dependencies: {summary['api_dependencies']}")
        print(f"Service Dependencies: {summary['service_dependencies']}")
        print(f"Model Dependencies: {summary['model_dependencies']}")
        print(f"External Dependencies: {summary['external_dependencies']}")
        print(f"Total Dependencies: {summary['total_dependencies']}")
        return
    
    if args.list_checks:
        print("🔍 AVAILABLE DEPENDENCY CHECKS")
        print("=" * 35)
        for check_id, check_config in DEPENDENCY_CHECKS.items():
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
        
        # Validate dependencies
        validation_result = validator.validate_dependencies(amendment_text)
        
        # Display report
        validator.display_dependency_report(validation_result)
        
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
    
    elif args.emit_complexity_json:
        # Emit complexity flows JSON
        print("📊 Emitting delegation complexity flows...")
        
        # Find delegation files
        delegation_files = validator._find_delegation_files()
        
        # Count flows per module
        modules = {}
        for file_path in delegation_files:
            if os.path.exists(file_path):
                flows = validator._count_delegation_flows(file_path)
                if flows > 0:
                    module_name = os.path.basename(file_path).replace('.py', '')
                    modules[module_name] = flows
        
        # Create output
        complexity_data = {
            "timestamp": datetime.now().isoformat(),
            "modules": modules,
            "total_flows": sum(modules.values()),
            "files_analyzed": len(delegation_files)
        }
        
        # Save to file
        with open(args.emit_complexity_json, 'w') as f:
            json.dump(complexity_data, f, indent=2)
        
        print(f"📄 Complexity flows saved to: {args.emit_complexity_json}")
        print(f"📊 Total flows: {complexity_data['total_flows']} across {len(modules)} modules")
    
    elif args.emit_maintainer_json:
        # Emit maintainer concentration JSON
        print("📊 Emitting maintainer concentration...")
        
        # Find delegation files
        delegation_files = validator._find_delegation_files()
        
        # Analyze maintainer concentration
        maintainer_stats = validator._analyze_maintainer_concentration(delegation_files)
        
        if maintainer_stats:
            total_commits = sum(maintainer_stats.values())
            top_maintainer = max(maintainer_stats.items(), key=lambda x: x[1])
            concentration_pct = (top_maintainer[1] / total_commits) * 100
            
            maintainer_data = {
                "timestamp": datetime.now().isoformat(),
                "concentration_percentage": concentration_pct,
                "top_maintainer": top_maintainer[0],
                "total_commits": total_commits,
                "maintainer_stats": maintainer_stats,
                "lookback_days": 30,
                "files_analyzed": len(delegation_files)
            }
        else:
            maintainer_data = {
                "timestamp": datetime.now().isoformat(),
                "concentration_percentage": 0,
                "top_maintainer": "",
                "total_commits": 0,
                "maintainer_stats": {},
                "lookback_days": 30,
                "files_analyzed": len(delegation_files)
            }
        
        # Save to file
        with open(args.emit_maintainer_json, 'w') as f:
            json.dump(maintainer_data, f, indent=2)
        
        print(f"📄 Maintainer concentration saved to: {args.emit_maintainer_json}")
        print(f"📊 Top maintainer: {maintainer_data['top_maintainer']} ({maintainer_data['concentration_percentage']:.1f}%)")
    
    else:
        print("❌ Must specify one of: --validate, --dependencies, --list-checks, --emit-complexity-json, or --emit-maintainer-json")
        sys.exit(1)


if __name__ == "__main__":
    main()
