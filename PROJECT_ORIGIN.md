# PROJECT_ORIGIN.md

## The Commons – Everyday Democracy for Everyone

---

### 1. Problem Statement

Modern democracies are slow, centralized, and largely inaccessible between elections. Citizens have little real-time influence on decisions, and participation is often reduced to a vote every few years.

**Key problems:**
- Low responsiveness: Decisions take months or years, even for urgent issues.
- Limited access: Participation requires time, connections, or insider knowledge.
- Representation gap: Elected representatives act as gatekeepers, often disconnected from the people they serve.
- Spectator politics: People watch politics happen rather than directly shaping outcomes.

**The Commons** aims to turn democracy into an everyday practice — fast, transparent, and open to all.

---

### 2. Core Principles
- **Fluid Delegation**: People can vote directly or delegate their vote to someone they trust — permanently, temporarily, or issue-by-issue.
- **Transparency by Default**: All proposals, votes, and delegations are public and traceable. No hidden deals or closed-door decisions.
- **Participation as a Right**: Everyone affected by a decision should be able to influence it. No barriers like party membership or bureaucratic hurdles.
- **Layered Scope**: Works at any scale — neighborhood, city, organization, or nation.
- **Reversibility**: Delegations and votes can be changed at any time, keeping power fluid rather than locked.

---

### 3. Proposed Model

#### Chain of Decision
1. **Proposal**: Any participant can propose an idea, policy, or action.
2. **Discussion**: Open comment period for feedback and refinement.
3. **Voting**: Options include:
   - Direct vote (Yes/No/Abstain or ranked choice).
   - Delegated vote (automatically follows your chosen delegate’s vote).
4. **Execution**: Approved proposals move directly into implementation (or are passed to the responsible authority with no further gatekeeping).

#### Delegation System
- **Per-issue**: Delegate for one specific topic (e.g., transport policy).
- **Per-category**: Delegate for a category of issues (e.g., environment).
- **Full delegation**: Delegate all votes to someone until changed.

#### Trust Networks
- Every delegate’s track record is public.
- Participants can follow trusted decision-makers and change delegates instantly if trust is lost.

---

### 4. Intended Impact
- Faster decisions without sacrificing inclusivity.
- Higher engagement because people can participate at the level they want — directly or through trusted delegates.
- Reduced polarization by focusing on proposals and solutions rather than political theatre.
- Transparent governance with decisions traceable from proposal to execution.

---

### 5. Design Implications
- **UI simplicity**: Proposing and voting must be as easy as posting on social media.
- **Clear delegation controls**: Change or revoke delegations in a single click.
- **Public ledgers**: Every vote and delegation is visible, searchable, and time-stamped.
- **Scalable architecture**: Support both small, local decision groups and large-scale governance.
- **Real-time updates**: Results and changes should be visible instantly.

---

### 6. Why Now
- Erosion of trust in traditional politics is at historic highs.
- Technology is mature enough to allow secure, real-time, large-scale decision-making.
- Global challenges (climate, inequality, urban planning) require faster collective action than current systems allow.
- Civic disengagement can be reversed if participation is made habitual, convenient, and rewarding.

**The Commons** is not about replacing existing systems overnight — it’s an upgrade path that can run alongside current governance, proving itself in small contexts before scaling up.

---

## 7. Technical Translation (Backend & Frontend Mapping)

| Principle / Feature          | Implementation (Backend) | Implementation (Frontend) |
|------------------------------|---------------------------|----------------------------|
| Fluid Delegation              | `delegations` table with revocable links; API endpoints for create/update/delete delegation | Delegation management UI with simple/advanced modes |
| Transparency by Default       | `activity_log` table & public API endpoints | Public activity feed and proposal history views |
| Participation as a Right      | Public registration API; minimal onboarding | Quick signup/login; mobile-friendly voting interface |
| Layered Scope                  | Scoped proposal & vote models with group IDs | UI filters by group/community |
| Reversibility                  | Updateable vote and delegation records; timestamped changes | One-click “change vote” / “revoke delegation” buttons |
| Proposal → Discussion → Vote → Execution | API routes for each stage; real-time updates via websockets/Redis pub-sub | Step-by-step UI flow for proposal creation, discussion, voting |
| Trust Networks                 | `delegation_stats` table tracking delegation patterns | Visual trust network graphs |

---

## 8. MVP Scope

The first public-facing version will include:
- **User Registration & Login** (JWT authentication)
- **Create a Proposal** (title, description, category)
- **Vote Directly** (Yes/No/Abstain)
- **Basic Delegation** (choose a delegate for all votes; no per-issue yet)
- **View Results** (simple list + basic chart)
- **Public Activity Feed** (latest proposals, votes, delegations)
- **Mobile-Responsive UI**

**Out of Scope for MVP**:
- Advanced delegation (per-issue, per-category)
- Full trust network visualization
- Federation between multiple Commons instances
- Granular permission settings

---