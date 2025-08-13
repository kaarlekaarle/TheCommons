from typing import List, Dict, Any
from uuid import UUID
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.poll import Poll
from backend.models.option import Option
from backend.models.vote import Vote
from backend.models.delegation import Delegation
from backend.models.label import Label
from backend.schemas.poll import PollResult
from backend.core.logging_config import get_logger

logger = get_logger(__name__)


async def get_poll_results(poll_id: UUID, db: AsyncSession) -> List[PollResult]:
    """
    Get poll results with delegation support.
    
    Args:
        poll_id: ID of the poll
        db: Database session
        
    Returns:
        List[PollResult]: List of poll results with vote counts
    """
    # First, verify the poll exists
    poll_result = await db.execute(
        select(Poll).where(
            and_(
                Poll.id == poll_id,
                Poll.is_deleted == False
            )
        )
    )
    poll = poll_result.scalar_one_or_none()
    if not poll:
        raise ValueError(f"Poll with id {poll_id} not found")
    
    # Get all options for the poll
    options_result = await db.execute(
        select(Option).where(
            and_(
                Option.poll_id == poll_id,
                Option.is_deleted == False
            )
        )
    )
    options = options_result.scalars().all()
    
    if not options:
        return []
    
    # Get all direct votes for this poll
    votes_result = await db.execute(
        select(Vote).where(
            and_(
                Vote.poll_id == poll_id,
                Vote.is_deleted == False
            )
        )
    )
    direct_votes = votes_result.scalars().all()
    
    # Get all active delegations (global and label-specific)
    delegations_result = await db.execute(
        select(Delegation).where(
            and_(
                Delegation.is_deleted == False
            )
        )
    )
    delegations = delegations_result.scalars().all()
    
    # Get poll labels for label-specific delegation matching
    poll_labels_result = await db.execute(
        select(Poll.labels).where(Poll.id == poll_id)
    )
    poll_labels = poll_labels_result.scalar_one_or_none() or []
    
    # Create a mapping of option_id to vote counts
    option_votes: Dict[UUID, Dict[str, int]] = {}
    
    # Initialize all options with zero votes
    for option in options:
        option_votes[option.id] = {
            "direct_votes": 0,
            "delegated_votes": 0,
            "total_votes": 0
        }
    
    # Count direct votes
    for vote in direct_votes:
        weight = vote.weight or 1
        option_votes[vote.option_id]["direct_votes"] += weight
        option_votes[vote.option_id]["total_votes"] += weight
    
    # Process delegations and add delegated votes
    for delegation in delegations:
        try:
            # Check if delegator has voted directly
            delegator_vote_result = await db.execute(
                select(Vote).where(
                    and_(
                        Vote.user_id == delegation.delegator_id,
                        Vote.poll_id == poll_id,
                        Vote.is_deleted == False
                    )
                )
            )
            delegator_vote = delegator_vote_result.scalar_one_or_none()
            
            # If delegator hasn't voted directly, check their delegate's vote
            if not delegator_vote:
                # Determine if this delegation applies to this poll
                delegation_applies = False
                
                if delegation.label_id:
                    # Label-specific delegation - check if poll has matching label
                    for poll_label in poll_labels:
                        if poll_label.id == delegation.label_id:
                            delegation_applies = True
                            break
                else:
                    # Global delegation - always applies
                    delegation_applies = True
                
                if delegation_applies:
                    # Find the delegate's vote
                    delegate_vote_result = await db.execute(
                        select(Vote).where(
                            and_(
                                Vote.user_id == delegation.delegatee_id,
                                Vote.poll_id == poll_id,
                                Vote.is_deleted == False
                            )
                        )
                    )
                    delegate_vote = delegate_vote_result.scalar_one_or_none()
                    
                    if delegate_vote:
                        # Add the delegation weight to the delegate's chosen option
                        delegation_weight = 1  # Default weight for delegation
                        option_votes[delegate_vote.option_id]["delegated_votes"] += delegation_weight
                        option_votes[delegate_vote.option_id]["total_votes"] += delegation_weight
                    
        except Exception as e:
            logger.warning(
                "Failed to process delegation for vote counting",
                extra={
                    "poll_id": poll_id,
                    "delegator_id": delegation.delegator_id,
                    "error": str(e)
                }
            )
            continue
    
    # Create PollResult objects
    results = []
    for option in options:
        votes = option_votes[option.id]
        result = PollResult(
            option_id=option.id,
            text=option.text,
            direct_votes=votes["direct_votes"],
            delegated_votes=votes["delegated_votes"],
            total_votes=votes["total_votes"]
        )
        results.append(result)
    
    # Sort by total votes (descending)
    results.sort(key=lambda x: x.total_votes, reverse=True)
    
    logger.info(
        "Calculated poll results",
        extra={
            "poll_id": poll_id,
            "options_count": len(options),
            "direct_votes_count": len(direct_votes),
            "delegations_count": len(delegations)
        }
    )
    
    return results
