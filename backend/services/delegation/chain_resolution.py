"""Pure chain resolution logic for delegation chains.

This module contains pure functions for resolving delegation chains
without any side effects (no database queries, no caching, no logging).
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID

from backend.models.delegation import Delegation, DelegationMode


class ChainResolutionCore:
    """Pure chain resolution logic with no side effects."""
    
    @staticmethod
    def resolve_chain_from_delegations(
        user_id: UUID,
        available_delegations: List[Delegation],
        poll_id: Optional[UUID] = None,
        label_id: Optional[UUID] = None,
        field_id: Optional[UUID] = None,
        institution_id: Optional[UUID] = None,
        value_id: Optional[UUID] = None,
        idea_id: Optional[UUID] = None,
        max_depth: int = 10,
    ) -> List[Delegation]:
        """Resolve delegation chain from available delegations (pure function).
        
        Args:
            user_id: ID of the user to resolve chain for
            available_delegations: List of all available delegations to consider
            poll_id: Optional poll ID for poll-specific resolution
            label_id: Optional label ID for label-specific resolution
            field_id: Optional field ID for field-specific resolution
            institution_id: Optional institution ID for institution-specific resolution
            value_id: Optional value ID for value-specific resolution
            idea_id: Optional idea ID for idea-specific resolution
            max_depth: Maximum chain depth to prevent infinite loops
            
        Returns:
            List[Delegation]: Chain of delegations ending at the final delegatee
        """
        chain = []
        current_user_id = user_id
        depth = 0
        
        # Create lookup map for fast delegation access
        delegation_map = ChainResolutionCore._build_delegation_map(available_delegations)
        
        while depth < max_depth:
            # Find active delegation for current user
            delegation = ChainResolutionCore._find_active_delegation(
                current_user_id,
                delegation_map,
                poll_id, label_id, field_id, institution_id, value_id, idea_id
            )
            
            if not delegation:
                break  # No active delegation found
                
            chain.append(delegation)
            
            # Check if this delegation is expired (legacy mode)
            if ChainResolutionCore._is_delegation_expired(delegation):
                break  # Stop at expired delegation
                
            # Move to next delegatee
            current_user_id = delegation.delegatee_id
            depth += 1
            
            # Constitutional protection: stop immediately on user override
            # This would be checked by the caller with side effects
            if ChainResolutionCore._has_user_override_placeholder(current_user_id, poll_id, label_id, field_id, institution_id, value_id, idea_id):
                break
        
        if depth >= max_depth:
            # Return chain but note that depth limit was reached
            pass
            
        return chain
    
    @staticmethod
    def _build_delegation_map(delegations: List[Delegation]) -> Dict[UUID, List[Delegation]]:
        """Build a map of delegator_id -> list of delegations for fast lookup."""
        delegation_map = {}
        for delegation in delegations:
            if delegation.delegator_id not in delegation_map:
                delegation_map[delegation.delegator_id] = []
            delegation_map[delegation.delegator_id].append(delegation)
        return delegation_map
    
    @staticmethod
    def _find_active_delegation(
        user_id: UUID,
        delegation_map: Dict[UUID, List[Delegation]],
        poll_id: Optional[UUID] = None,
        label_id: Optional[UUID] = None,
        field_id: Optional[UUID] = None,
        institution_id: Optional[UUID] = None,
        value_id: Optional[UUID] = None,
        idea_id: Optional[UUID] = None,
    ) -> Optional[Delegation]:
        """Find active delegation for a user from the delegation map."""
        if user_id not in delegation_map:
            return None
        
        user_delegations = delegation_map[user_id]
        now = datetime.utcnow()
        
        # Filter active delegations
        active_delegations = []
        for delegation in user_delegations:
            if ChainResolutionCore._is_delegation_active(delegation, now):
                active_delegations.append(delegation)
        
        if not active_delegations:
            return None
        
        # Filter by target scope
        target_delegations = []
        for delegation in active_delegations:
            if ChainResolutionCore._matches_target_scope(
                delegation, poll_id, label_id, field_id, institution_id, value_id, idea_id
            ):
                target_delegations.append(delegation)
        
        if not target_delegations:
            return None
        
        # Order by mode priority: hybrid_seed (global fallback) first, then specific
        target_delegations.sort(
            key=lambda d: (d.mode != DelegationMode.HYBRID_SEED, d.created_at)
        )
        
        return target_delegations[0] if target_delegations else None
    
    @staticmethod
    def _is_delegation_active(delegation: Delegation, now: datetime) -> bool:
        """Check if delegation is currently active."""
        if delegation.is_deleted or delegation.revoked_at is not None:
            return False
        
        # Check start date
        if delegation.start_date and now < delegation.start_date:
            return False
        
        # Check end date
        if delegation.end_date and now > delegation.end_date:
            return False
        
        # Check legacy term expiry
        if (delegation.is_legacy_fixed_term and 
            delegation.legacy_term_ends_at and 
            now > delegation.legacy_term_ends_at):
            return False
        
        return True
    
    @staticmethod
    def _matches_target_scope(
        delegation: Delegation,
        poll_id: Optional[UUID] = None,
        label_id: Optional[UUID] = None,
        field_id: Optional[UUID] = None,
        institution_id: Optional[UUID] = None,
        value_id: Optional[UUID] = None,
        idea_id: Optional[UUID] = None,
    ) -> bool:
        """Check if delegation matches the target scope."""
        if poll_id is not None:
            return delegation.poll_id == poll_id
        elif label_id is not None:
            return delegation.label_id == label_id
        elif field_id is not None:
            return delegation.field_id == field_id
        elif institution_id is not None:
            return delegation.institution_id == institution_id
        elif value_id is not None:
            return delegation.value_id == value_id
        elif idea_id is not None:
            return delegation.idea_id == idea_id
        else:
            # Global delegation (no specific target)
            return (delegation.poll_id is None and
                   delegation.label_id is None and
                   delegation.field_id is None and
                   delegation.institution_id is None and
                   delegation.value_id is None and
                   delegation.idea_id is None)
    
    @staticmethod
    def _is_delegation_expired(delegation: Delegation) -> bool:
        """Check if legacy delegation has expired."""
        if not delegation.is_legacy_fixed_term or not delegation.legacy_term_ends_at:
            return False
        return datetime.utcnow() > delegation.legacy_term_ends_at
    
    @staticmethod
    def _has_user_override_placeholder(
        user_id: UUID,
        poll_id: Optional[UUID] = None,
        label_id: Optional[UUID] = None,
        field_id: Optional[UUID] = None,
        institution_id: Optional[UUID] = None,
        value_id: Optional[UUID] = None,
        idea_id: Optional[UUID] = None,
    ) -> bool:
        """Placeholder for user override check (pure function).
        
        This is a placeholder that always returns False.
        The actual override check would be implemented by the caller
        with side effects (database queries, etc.).
        """
        return False
    
    @staticmethod
    def serialize_chain(chain: List[Delegation]) -> List[Dict[str, Any]]:
        """Serialize delegation chain to JSON-serializable format."""
        chain_data = []
        for delegation in chain:
            chain_data.append({
                "id": str(delegation.id),
                "delegator_id": str(delegation.delegator_id),
                "delegatee_id": str(delegation.delegatee_id),
                "mode": delegation.mode,
                "poll_id": str(delegation.poll_id) if delegation.poll_id else None,
                "label_id": str(delegation.label_id) if delegation.label_id else None,
                "field_id": str(delegation.field_id) if delegation.field_id else None,
                "institution_id": str(delegation.institution_id) if delegation.institution_id else None,
                "value_id": str(delegation.value_id) if delegation.value_id else None,
                "idea_id": str(delegation.idea_id) if delegation.idea_id else None,
                "start_date": delegation.start_date.isoformat() if delegation.start_date else None,
                "end_date": delegation.end_date.isoformat() if delegation.end_date else None,
                "legacy_term_ends_at": delegation.legacy_term_ends_at.isoformat() if delegation.legacy_term_ends_at else None,
                "created_at": delegation.created_at.isoformat() if delegation.created_at else None,
            })
        return chain_data
    
    @staticmethod
    def deserialize_chain(chain_data: List[Dict[str, Any]]) -> List[Delegation]:
        """Deserialize cached chain data to Delegation objects."""
        chain = []
        for delegation_data in chain_data:
            delegation = Delegation()
            delegation.id = UUID(delegation_data["id"])
            delegation.delegator_id = UUID(delegation_data["delegator_id"])
            delegation.delegatee_id = UUID(delegation_data["delegatee_id"])
            delegation.mode = delegation_data["mode"]
            delegation.poll_id = UUID(delegation_data["poll_id"]) if delegation_data["poll_id"] else None
            delegation.label_id = UUID(delegation_data["label_id"]) if delegation_data["label_id"] else None
            delegation.field_id = UUID(delegation_data["field_id"]) if delegation_data["field_id"] else None
            delegation.institution_id = UUID(delegation_data["institution_id"]) if delegation_data["institution_id"] else None
            delegation.value_id = UUID(delegation_data["value_id"]) if delegation_data["value_id"] else None
            delegation.idea_id = UUID(delegation_data["idea_id"]) if delegation_data["idea_id"] else None
            delegation.start_date = datetime.fromisoformat(delegation_data["start_date"]) if delegation_data["start_date"] else None
            delegation.end_date = datetime.fromisoformat(delegation_data["end_date"]) if delegation_data["end_date"] else None
            delegation.legacy_term_ends_at = datetime.fromisoformat(delegation_data["legacy_term_ends_at"]) if delegation_data["legacy_term_ends_at"] else None
            delegation.created_at = datetime.fromisoformat(delegation_data["created_at"]) if delegation_data["created_at"] else None
            chain.append(delegation)
        return chain
