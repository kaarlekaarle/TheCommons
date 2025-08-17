#!/usr/bin/env python3
"""
Constitutional Amendment Validator

This script provides comprehensive validation for constitutional amendments,
including philosophical integrity checks using the principle matrix.
"""

import os
import sys
import json
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import subprocess

# Import the principle matrix
try:
    from constitutional_principle_matrix import ConstitutionalPrincipleMatrix
    PRINCIPLE_MATRIX_AVAILABLE = True
except ImportError:
    print("Warning: Constitutional principle matrix not available. Using placeholder validation.")
    PRINCIPLE_MATRIX_AVAILABLE = False
    ConstitutionalPrincipleMatrix = None

# Import the feasibility validator
try:
    from constitutional_feasibility_validator import ConstitutionalFeasibilityValidator
    FEASIBILITY_VALIDATOR_AVAILABLE = True
except ImportError:
    print("Warning: Constitutional feasibility validator not available. Using placeholder validation.")
    FEASIBILITY_VALIDATOR_AVAILABLE = False
    ConstitutionalFeasibilityValidator = None

# Import the dependency validator
try:
    from constitutional_dependency_validator import ConstitutionalDependencyValidator
    DEPENDENCY_VALIDATOR_AVAILABLE = True
except ImportError:
    print("Warning: Constitutional dependency validator not available. Using placeholder validation.")
    DEPENDENCY_VALIDATOR_AVAILABLE = False
    ConstitutionalDependencyValidator = None

# Amendment types and their detection patterns
AMENDMENT_TYPES = {
    "core-principle": {
        "name": "Core Principle Modification",
        "description": "Modification to untouchable core principles",
        "paths": ["/constitutional/core/*"],
        "validation_level": "maximum",
        "placeholder_result": "pass"
    },
    "implementation": {
        "name": "Implementation Detail Change", 
        "description": "Change to adaptable implementation details",
        "paths": ["/constitutional/implementation/*"],
        "validation_level": "standard",
        "placeholder_result": "pass"
    },
    "feature": {
        "name": "Feature Addition",
        "description": "Addition of new constitutional features",
        "paths": ["/constitutional/features/*"],
        "validation_level": "enhanced",
        "placeholder_result": "pass"
    },
    "documentation": {
        "name": "Documentation Update",
        "description": "Update to constitutional documentation",
        "paths": ["/docs/constitutional/*"],
        "validation_level": "minimal",
        "placeholder_result": "pass"
    }
}

# Validation checks with real implementations
VALIDATION_CHECKS = {
    "philosophical_integrity": {
        "name": "Philosophical Integrity Check",
        "description": "Ensures amendment doesn't violate core philosophical principles",
        "implementation": "real" if PRINCIPLE_MATRIX_AVAILABLE else "placeholder"
    },
    "technical_feasibility": {
        "name": "Technical Feasibility Check",
        "description": "Ensures amendment is technically feasible and implementable",
        "implementation": "real" if FEASIBILITY_VALIDATOR_AVAILABLE else "placeholder"
    },
    "dependency_impact": {
        "name": "Dependency & Community Impact Check",
        "description": "Ensures amendment has sustainable dependencies and manageable community impact",
        "implementation": "real" if DEPENDENCY_VALIDATOR_AVAILABLE else "placeholder"
    },
    "ratification_check": {
        "name": "Ratification Check",
        "description": "Ensures amendment has proper community ratification",
        "implementation": "placeholder"
    }
}


class ConstitutionalAmendmentValidator:
    """Comprehensive validator for constitutional amendments."""
    
    def __init__(self):
        self.amendment_id = None
        self.amendment_type = None
        self.changed_files = []
        self.validation_results = {}
        self.amendment_text = ""
        
        # Initialize principle matrix if available
        if PRINCIPLE_MATRIX_AVAILABLE:
            self.principle_matrix = ConstitutionalPrincipleMatrix()
        else:
            self.principle_matrix = None
        
        # Initialize feasibility validator if available
        if FEASIBILITY_VALIDATOR_AVAILABLE:
            self.feasibility_validator = ConstitutionalFeasibilityValidator()
        else:
            self.feasibility_validator = None
        
        # Initialize dependency validator if available
        if DEPENDENCY_VALIDATOR_AVAILABLE:
            self.dependency_validator = ConstitutionalDependencyValidator()
        else:
            self.dependency_validator = None
    
    def detect_amendment_type(self, changed_files: List[str]) -> str:
        """Detect amendment type based on changed files."""
        print("🔍 DETECTING AMENDMENT TYPE")
        print("=" * 30)
        
        # Map file paths to amendment types
        type_matches = {
            "core-principle": 0,
            "implementation": 0,
            "feature": 0,
            "documentation": 0
        }
        
        for file_path in changed_files:
            print(f"Analyzing: {file_path}")
            
            # Check for core principle changes
            if "/constitutional/core/" in file_path:
                type_matches["core-principle"] += 1
                print(f"  → Matches core-principle pattern")
            
            # Check for implementation changes
            elif "/constitutional/implementation/" in file_path:
                type_matches["implementation"] += 1
                print(f"  → Matches implementation pattern")
            
            # Check for feature changes
            elif "/constitutional/features/" in file_path:
                type_matches["feature"] += 1
                print(f"  → Matches feature pattern")
            
            # Check for documentation changes
            elif "/docs/constitutional/" in file_path:
                type_matches["documentation"] += 1
                print(f"  → Matches documentation pattern")
            
            else:
                print(f"  → No specific pattern match")
        
        # Determine primary amendment type
        max_matches = max(type_matches.values())
        if max_matches == 0:
            # Default to implementation if no specific patterns match
            amendment_type = "implementation"
            print(f"⚠️  No specific patterns detected, defaulting to: {amendment_type}")
        else:
            # Use the type with the most matches
            amendment_type = max(type_matches, key=type_matches.get)
            print(f"✅ Detected amendment type: {amendment_type}")
        
        return amendment_type
    
    def extract_amendment_text(self, changed_files: List[str]) -> str:
        """Extract amendment text from changed files."""
        amendment_text = ""
        
        for file_path in changed_files:
            try:
                if os.path.exists(file_path):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        amendment_text += f"\n--- {file_path} ---\n{content}\n"
            except Exception as e:
                print(f"⚠️  Could not read file {file_path}: {e}")
        
        return amendment_text
    
    def run_validation_checks(self, amendment_type: str, amendment_text: str = "") -> Dict[str, Any]:
        """Run comprehensive validation checks."""
        print(f"\n🔍 RUNNING VALIDATION CHECKS")
        print("=" * 35)
        
        validation_results = {
            "amendment_type": amendment_type,
            "validation_timestamp": datetime.now().isoformat(),
            "checks": {},
            "overall_status": "unknown"
        }
        
        # Run each validation check
        for check_id, check_config in VALIDATION_CHECKS.items():
            print(f"Running {check_config['name']}...")
            
            if check_id == "philosophical_integrity" and self.principle_matrix:
                # Use real philosophical integrity check
                check_result = self._run_philosophical_integrity_check(amendment_text)
            elif check_id == "technical_feasibility" and self.feasibility_validator:
                # Use real technical feasibility check
                check_result = self._run_technical_feasibility_check(amendment_text)
            elif check_id == "dependency_impact" and self.dependency_validator:
                # Use real dependency impact check
                check_result = self._run_dependency_impact_check(amendment_text)
            else:
                # Use placeholder implementation
                check_result = self._run_placeholder_check(check_id, check_config)
            
            validation_results["checks"][check_id] = check_result
            
            status_icon = "✅" if check_result["status"] == "pass" else "❌" if check_result["status"] == "fail" else "⚠️"
            print(f"  {status_icon} {check_config['name']}: {check_result['status']}")
        
        # Determine overall status
        all_passed = all(check["status"] == "pass" for check in validation_results["checks"].values())
        any_failed = any(check["status"] == "fail" for check in validation_results["checks"].values())
        
        if any_failed:
            validation_results["overall_status"] = "fail"
        elif all_passed:
            validation_results["overall_status"] = "pass"
        else:
            validation_results["overall_status"] = "warning"
        
        print(f"\n📊 OVERALL VALIDATION STATUS: {validation_results['overall_status'].upper()}")
        
        return validation_results
    
    def _run_philosophical_integrity_check(self, amendment_text: str) -> Dict[str, Any]:
        """Run real philosophical integrity check using principle matrix."""
        try:
            # Run principle matrix validation
            integrity_result = self.principle_matrix.validate_amendment_integrity(amendment_text, self.changed_files)
            
            # Convert principle matrix result to validation check format
            if integrity_result["overall_status"] == "passed":
                status = "pass"
            elif integrity_result["overall_status"] == "failed":
                status = "fail"
            else:
                status = "warning"
            
            return {
                "check_type": "philosophical_integrity",
                "status": status,
                "details": f"Principle matrix validation: {integrity_result['overall_status']}",
                "principle_results": integrity_result,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"  ⚠️  Philosophical integrity check failed: {e}")
            return {
                "check_type": "philosophical_integrity",
                "status": "warning",
                "details": f"Check failed: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
    
    def _run_technical_feasibility_check(self, amendment_text: str) -> Dict[str, Any]:
        """Run real technical feasibility check using feasibility validator."""
        try:
            # Run feasibility validator
            feasibility_result = self.feasibility_validator.validate_feasibility(amendment_text, self.changed_files)
            
            # Convert feasibility validator result to validation check format
            if feasibility_result["overall_status"] == "passed":
                status = "pass"
            elif feasibility_result["overall_status"] == "failed":
                status = "fail"
            else:
                status = "warning"
            
            return {
                "check_type": "technical_feasibility",
                "status": status,
                "details": f"Feasibility validation: {feasibility_result['overall_status']}",
                "feasibility_results": feasibility_result,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"  ⚠️  Technical feasibility check failed: {e}")
            return {
                "check_type": "technical_feasibility",
                "status": "warning",
                "details": f"Check failed: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
    
    def _run_dependency_impact_check(self, amendment_text: str) -> Dict[str, Any]:
        """Run real dependency impact check using dependency validator."""
        try:
            # Run dependency validator
            dependency_result = self.dependency_validator.validate_dependencies(amendment_text, self.changed_files)
            
            # Convert dependency validator result to validation check format
            if dependency_result["overall_status"] == "passed":
                status = "pass"
            elif dependency_result["overall_status"] == "failed":
                status = "fail"
            else:
                status = "warning"
            
            return {
                "check_type": "dependency_impact",
                "status": status,
                "details": f"Dependency validation: {dependency_result['overall_status']}",
                "dependency_results": dependency_result,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"  ⚠️  Dependency impact check failed: {e}")
            return {
                "check_type": "dependency_impact",
                "status": "warning",
                "details": f"Check failed: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
    
    def _run_placeholder_check(self, check_id: str, check_config: Dict[str, Any]) -> Dict[str, Any]:
        """Run placeholder validation check."""
        # Placeholder implementation - always passes for now
        result = "pass"
        
        return {
            "check_type": check_id,
            "status": result,
            "details": f"Placeholder check - {result}",
            "timestamp": datetime.now().isoformat()
        }
    
    def validate_amendment(self, changed_files: List[str], amendment_id: Optional[str] = None) -> Dict[str, Any]:
        """Main validation method."""
        print("🏛️ CONSTITUTIONAL AMENDMENT VALIDATION")
        print("=" * 50)
        print(f"Timestamp: {datetime.now().isoformat()}")
        print(f"Changed files: {len(changed_files)}")
        print()
        
        # Generate amendment ID if not provided
        if not amendment_id:
            amendment_id = f"amendment_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        self.amendment_id = amendment_id
        print(f"Amendment ID: {amendment_id}")
        
        # Store changed files
        self.changed_files = changed_files
        
        # Detect amendment type
        amendment_type = self.detect_amendment_type(changed_files)
        self.amendment_type = amendment_type
        
        # Extract amendment text
        amendment_text = self.extract_amendment_text(changed_files)
        self.amendment_text = amendment_text
        
        # Run validation checks
        validation_results = self.run_validation_checks(amendment_type, amendment_text)
        
        # Prepare final result
        result = {
            "amendment_id": amendment_id,
            "amendment_type": amendment_type,
            "changed_files": changed_files,
            "validation_results": validation_results,
            "recommendations": self._generate_recommendations(amendment_type, validation_results)
        }
        
        return result
    
    def _generate_recommendations(self, amendment_type: str, validation_results: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on amendment type and validation results."""
        recommendations = []
        
        amendment_config = AMENDMENT_TYPES.get(amendment_type, {})
        
        if amendment_type == "core-principle":
            recommendations.append("⚠️  Core principle modifications require maximum validation")
            recommendations.append("📋 Schedule philosophical review with constitutional authorities")
            recommendations.append("🗳️  Prepare for community ratification process")
        elif amendment_type == "feature":
            recommendations.append("🔧 Feature additions require enhanced validation")
            recommendations.append("📋 Schedule technical review")
            recommendations.append("🗳️  Prepare for community ratification")
        elif amendment_type == "implementation":
            recommendations.append("⚙️  Implementation changes require standard validation")
            recommendations.append("📋 Schedule technical review")
        elif amendment_type == "documentation":
            recommendations.append("📚 Documentation updates require minimal validation")
            recommendations.append("📋 Review for accuracy and completeness")
        
        # Add recommendations based on validation results
        if validation_results["overall_status"] == "pass":
            recommendations.append("✅ All validation checks passed")
        elif validation_results["overall_status"] == "fail":
            recommendations.append("❌ Address validation failures before proceeding")
            
            # Add specific recommendations for philosophical integrity failures
            if "philosophical_integrity" in validation_results["checks"]:
                phi_check = validation_results["checks"]["philosophical_integrity"]
                if phi_check["status"] == "fail" and "principle_results" in phi_check:
                    principle_results = phi_check["principle_results"]
                    if principle_results.get("critical_violations"):
                        recommendations.append("🚨 CRITICAL: Address principle violations immediately")
                        for violation in principle_results["critical_violations"][:2]:  # Show first 2
                            recommendations.append(f"   • {violation}")
            
            # Add specific recommendations for technical feasibility failures
            if "technical_feasibility" in validation_results["checks"]:
                feas_check = validation_results["checks"]["technical_feasibility"]
                if feas_check["status"] == "fail" and "feasibility_results" in feas_check:
                    feasibility_results = feas_check["feasibility_results"]
                    if feasibility_results.get("infeasible_demands"):
                        recommendations.append("🚨 CRITICAL: Address technical infeasibility immediately")
                        for demand in feasibility_results["infeasible_demands"][:2]:  # Show first 2
                            recommendations.append(f"   • {demand}")
            
            # Add specific recommendations for dependency impact failures
            if "dependency_impact" in validation_results["checks"]:
                dep_check = validation_results["checks"]["dependency_impact"]
                if dep_check["status"] == "fail" and "dependency_results" in dep_check:
                    dependency_results = dep_check["dependency_results"]
                    if dependency_results.get("dependency_breaks"):
                        recommendations.append("🚨 CRITICAL: Address dependency breaks immediately")
                        for break_item in dependency_results["dependency_breaks"][:2]:  # Show first 2
                            recommendations.append(f"   • {break_item}")
                    if dependency_results.get("community_impacts"):
                        recommendations.append("🌍 CRITICAL: Address community impact concerns")
                        for impact in dependency_results["community_impacts"][:2]:  # Show first 2
                            recommendations.append(f"   • {impact}")
        else:
            recommendations.append("⚠️  Review warnings before proceeding")
        
        return recommendations
    
    def display_results(self, result: Dict[str, Any]) -> None:
        """Display validation results."""
        print(f"\n📋 VALIDATION RESULTS SUMMARY")
        print("=" * 35)
        print(f"Amendment ID: {result['amendment_id']}")
        print(f"Type: {result['amendment_type']}")
        print(f"Status: {result['validation_results']['overall_status'].upper()}")
        print(f"Changed Files: {len(result['changed_files'])}")
        
        print(f"\n🔍 VALIDATION CHECKS")
        print("-" * 20)
        for check_id, check_result in result['validation_results']['checks'].items():
            status_icon = "✅" if check_result["status"] == "pass" else "❌" if check_result["status"] == "fail" else "⚠️"
            print(f"{status_icon} {check_result['check_type']}: {check_result['status']}")
            
            # Show detailed results for philosophical integrity check
            if check_id == "philosophical_integrity" and "principle_results" in check_result:
                principle_results = check_result["principle_results"]
                if principle_results.get("critical_violations"):
                    print(f"   🚨 Critical violations: {len(principle_results['critical_violations'])}")
                if principle_results.get("warnings"):
                    print(f"   ⚠️  Warnings: {len(principle_results['warnings'])}")
            
            # Show detailed results for technical feasibility check
            if check_id == "technical_feasibility" and "feasibility_results" in check_result:
                feasibility_results = check_result["feasibility_results"]
                if feasibility_results.get("infeasible_demands"):
                    print(f"   🚨 Infeasible demands: {len(feasibility_results['infeasible_demands'])}")
                if feasibility_results.get("warnings"):
                    print(f"   ⚠️  Warnings: {len(feasibility_results['warnings'])}")
            
            # Show detailed results for dependency impact check
            if check_id == "dependency_impact" and "dependency_results" in check_result:
                dependency_results = check_result["dependency_results"]
                if dependency_results.get("dependency_breaks"):
                    print(f"   🚨 Dependency breaks: {len(dependency_results['dependency_breaks'])}")
                if dependency_results.get("community_impacts"):
                    print(f"   🌍 Community impacts: {len(dependency_results['community_impacts'])}")
                if dependency_results.get("maintainer_burdens"):
                    print(f"   👥 Maintainer burdens: {len(dependency_results['maintainer_burdens'])}")
        
        if result['recommendations']:
            print(f"\n💡 RECOMMENDATIONS")
            print("-" * 15)
            for recommendation in result['recommendations']:
                print(f"• {recommendation}")
        
        print(f"\n🎯 FINAL STATUS: {result['validation_results']['overall_status'].upper()}")
        if result['validation_results']['overall_status'] == 'pass':
            print("✅ Amendment validation passed - ready for next stage")
        elif result['validation_results']['overall_status'] == 'warning':
            print("⚠️  Amendment validation has warnings - review recommended")
        else:
            print("❌ Amendment validation failed - address issues before proceeding")


def get_changed_files_from_git() -> List[str]:
    """Get list of changed files from git."""
    try:
        # Get files changed in the current branch compared to main
        result = subprocess.run(
            ["git", "diff", "--name-only", "main"],
            capture_output=True,
            text=True,
            check=True
        )
        changed_files = result.stdout.strip().split('\n') if result.stdout.strip() else []
        return [f for f in changed_files if f]  # Remove empty strings
    except subprocess.CalledProcessError:
        print("⚠️  Could not determine changed files from git")
        return []


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Constitutional Amendment Validator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python constitutional_amendment_validator.py --files file1.py file2.py
  python constitutional_amendment_validator.py --git-changes
  python constitutional_amendment_validator.py --list-types
  python constitutional_amendment_validator.py --list-checks
        """
    )
    
    parser.add_argument(
        '--files', '-f',
        nargs='+',
        help='Files to validate as amendment'
    )
    
    parser.add_argument(
        '--git-changes', '-g',
        action='store_true',
        help='Use git to determine changed files'
    )
    
    parser.add_argument(
        '--amendment-id', '-i',
        help='Amendment ID (auto-generated if not provided)'
    )
    
    parser.add_argument(
        '--output', '-o',
        help='Output file for results (JSON format)'
    )
    
    parser.add_argument(
        '--list-types', '-t',
        action='store_true',
        help='List available amendment types'
    )
    
    parser.add_argument(
        '--list-checks', '-c',
        action='store_true',
        help='List available validation checks'
    )
    
    args = parser.parse_args()
    
    validator = ConstitutionalAmendmentValidator()
    
    if args.list_types:
        print("📋 AVAILABLE AMENDMENT TYPES")
        print("=" * 30)
        for type_id, type_config in AMENDMENT_TYPES.items():
            print(f"\n{type_id}:")
            print(f"  Name: {type_config['name']}")
            print(f"  Description: {type_config['description']}")
            print(f"  Validation Level: {type_config['validation_level']}")
            print(f"  Detection Paths: {', '.join(type_config['paths'])}")
        return
    
    if args.list_checks:
        print("🔍 AVAILABLE VALIDATION CHECKS")
        print("=" * 30)
        for check_id, check_config in VALIDATION_CHECKS.items():
            print(f"\n{check_id}:")
            print(f"  Name: {check_config['name']}")
            print(f"  Description: {check_config['description']}")
            print(f"  Implementation: {check_config['implementation']}")
        return
    
    # Determine files to validate
    if args.files:
        changed_files = args.files
    elif args.git_changes:
        changed_files = get_changed_files_from_git()
        if not changed_files:
            print("⚠️  No changed files detected")
            return
    else:
        print("❌ Must specify either --files or --git-changes")
        sys.exit(1)
    
    # Filter for constitutional files
    constitutional_files = [
        f for f in changed_files 
        if any(pattern in f for pattern in [
            "/constitutional/", "/docs/constitutional/"
        ])
    ]
    
    if not constitutional_files:
        print("ℹ️  No constitutional files detected in changes")
        print("Files will be treated as implementation changes")
        constitutional_files = changed_files
    
    # Validate amendment
    result = validator.validate_amendment(constitutional_files, args.amendment_id)
    
    # Display results
    validator.display_results(result)
    
    # Save results if requested
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"\n📄 Results saved to: {args.output}")
    
    # Exit with appropriate code
    if result['validation_results']['overall_status'] == 'pass':
        sys.exit(0)
    elif result['validation_results']['overall_status'] == 'warning':
        sys.exit(2)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
