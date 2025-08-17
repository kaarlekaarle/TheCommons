# Constitutional Cascade Rules

## Overview

The constitutional cascade rules enforce the core principles of The Commons by monitoring for patterns that could lead to hierarchy, opacity, or concentration of power.

## Rule A: Formal + Informal Hierarchy

**Trigger**: Detection of formal or informal hierarchy patterns
**Mode**: ENFORCE
**Action**: BLOCK

## Rule B: Opacity + Complexity

**Trigger**: High complexity combined with opacity in delegation systems
**Mode**: ENFORCE  
**Action**: BLOCK

### Complexity Remediation

The delegation system has been refactored to reduce complexity by splitting the monolithic `delegation.py` into focused modules:

**Old Structure:**
- `backend/services/delegation.py` (1000+ lines, 18+ flows)

**New Structure:**
- `backend/services/delegation/chain_resolution.py` (pure functions, ≤5 flows)
- `backend/services/delegation/repository.py` (data access, ≤5 flows)  
- `backend/services/delegation/cache.py` (caching logic, ≤5 flows)
- `backend/services/delegation/telemetry.py` (monitoring, ≤5 flows)
- `backend/services/delegation/dispatch.py` (orchestration, ≤5 flows)
- `backend/services/delegation/__init__.py` (façade for compatibility)

**Complexity Thresholds:**
- **Warning**: 3+ flows per module
- **High**: 5+ flows per module  
- **Max**: 5 flows per module (reduced from 7)

**Migration Path:**
- Existing imports continue to work via the thin façade
- New code can import specific modules for advanced usage
- All constitutional guarantees preserved during refactoring

## Rule C: Knowledge Silos

**Trigger**: Concentration of knowledge in single maintainers
**Mode**: ENFORCE
**Action**: BLOCK

## Rule D: Unresponsive + Concentrated

**Trigger**: High maintainer concentration with unresponsiveness
**Mode**: ENFORCE
**Action**: BLOCK
