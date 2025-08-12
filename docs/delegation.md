# Delegation System

The delegation system allows users to trust others to vote on their behalf, making participation more accessible and flexible.

## Overview

Delegation is a core feature of The Commons that enables users to:
- Delegate their voting power to trusted community members
- Maintain control over their delegation at any time
- Choose between global (all polls) or poll-specific delegation
- See delegation chains to understand how their vote flows

## How It Works

### Global vs Poll-Specific Delegation

**Global Delegation**: When you delegate globally, the person you choose will vote on your behalf for ALL polls in The Commons. This is useful when you trust someone's judgment across all topics.

**Poll-Specific Delegation**: When you delegate to a specific poll, only that poll is affected. You maintain control over all other polls. This is useful when you want to delegate only for topics you're less familiar with.

### Delegation Chains

Delegation can form chains: if Alice delegates to Bob, and Bob delegates to Charlie, then Charlie's vote represents all three people. The system tracks these chains transparently.

## User Interface

### Header Status

The delegation status appears in the top-right corner of the header when you're logged in:

```
[👤 No delegation]  ← Click to manage
```

When you have an active delegation:

```
[👥 Delegating to Alice • 2-hop chain]  ← Click to manage
```

### Managing Delegation

1. **Click the delegation status** in the header or on a poll page
2. **Search for a user** you want to delegate to
3. **Select the user** from the search results
4. **Choose scope**: Global (all polls) or This poll only
5. **Click "Delegate"** to confirm

### Poll Pages

When you have an active delegation for a specific poll, you'll see a banner:

```
You are delegating this poll to Alice Smith
You can vote yourself or change your delegation.
```

This banner appears in the voting section of the poll page.

## First-Time Experience

New users see a helpful tooltip explaining delegation:

```
Trust someone to vote for you
If you're busy or unsure, you can delegate your vote to someone you trust. You're always in control.

[Got it] [Learn more]
```

This tooltip appears once per device and can be dismissed permanently.

## Revoking Delegation

To revoke your delegation:

1. **Click the delegation status** (shows current delegate)
2. **Click "Revoke delegation"** in the modal
3. **Confirm** the action

Your delegation is immediately revoked and you regain full voting control.

## Accessibility

The delegation system is fully accessible:

- **Keyboard navigation**: Use Tab to focus, Enter/Space to activate
- **Screen readers**: Proper ARIA labels and roles
- **High contrast**: Meets WCAG AA standards
- **Mobile friendly**: Responsive design with touch targets

## Feature Flags

The delegation system uses a clean flags configuration that automatically adapts to the environment:

### Development Environment
```bash
# .env.development or .env.local
VITE_DELEGATION_ENABLED=true
VITE_LOG_ANALYTICS=false
```

### Production Environment
```bash
# .env.production
VITE_DELEGATION_ENABLED=false
VITE_DELEGATION_BETA_ALLOWLIST=alice@example.com,bob@example.com
VITE_LOG_ANALYTICS=false
```

### Configuration Options

- `VITE_DELEGATION_ENABLED=true` - Enable delegation for all users
- `VITE_DELEGATION_ENABLED=false` - Disable delegation (default in production)
- `VITE_DELEGATION_BETA_ALLOWLIST=email1@example.com,email2@example.com` - Beta allowlist for production testing
- `VITE_LOG_ANALYTICS=true` - Enable console logging of delegation analytics events
- `VITE_LOG_ANALYTICS=false` - Disable analytics logging (default)

### Behavior by Environment

**Development**: Delegation is automatically enabled (`MODE === 'development'`)
**Production**: Delegation is disabled by default, but can be enabled for:
- All users (if `VITE_DELEGATION_ENABLED=true`)
- Beta allowlist users only (if `VITE_DELEGATION_BETA_ALLOWLIST` is set)

### Code Usage

```typescript
import { canUseDelegation } from '../lib/featureAccess';
import { useCurrentUser } from '../hooks/useCurrentUser';

// In a React component
function MyComponent() {
  const { user } = useCurrentUser();
  
  const allowed = canUseDelegation(user?.email);
  return allowed ? <DelegationStatus .../> : null;
}

// Direct usage with user email
const hasAccess = canUseDelegation('user@example.com');
```

### Feature Access Utility

The `canUseDelegation()` function provides a clean API for checking delegation access:

- **Development**: Always returns `true`
- **Production**: Returns `true` if:
  - `VITE_DELEGATION_ENABLED=true`, OR
  - User email is in `VITE_DELEGATION_BETA_ALLOWLIST`
- **No user email**: Returns `false`

### Analytics Tracking

The delegation system includes analytics tracking for key user interactions:

```typescript
import { 
  trackDelegationViewed,
  trackDelegationOpened,
  trackDelegationCreated,
  trackDelegationRevoked,
  trackOnboardingSeen
} from '../lib/analytics';

// Track when delegation UI is viewed
trackDelegationViewed();

// Track when delegation modal is opened
trackDelegationOpened();

// Track delegation creation (global or poll-specific)
trackDelegationCreated('global');

// Track delegation revocation
trackDelegationRevoked('poll');

// Track onboarding tooltip interaction
trackOnboardingSeen();
```

**Analytics Logging**: Set `VITE_LOG_ANALYTICS=true` to enable console logging of analytics events for debugging.

## Beta Rollout

When rolling out the delegation feature to production, follow this controlled approach to ensure a smooth launch.

### Initial Beta Configuration

Set up the beta environment with restricted access:

```bash
# .env.production
VITE_DELEGATION_ENABLED=false
VITE_DELEGATION_BETA_ALLOWLIST=alice@example.com,bob@example.com,charlie@example.com
VITE_LOG_ANALYTICS=true
```

**Key Settings:**
- `VITE_DELEGATION_ENABLED=false` - Keeps delegation hidden from general users
- `VITE_DELEGATION_BETA_ALLOWLIST` - Comma-separated list of beta tester emails
- `VITE_LOG_ANALYTICS=true` - Enables analytics logging for monitoring

### Beta Allowlist Management

The `VITE_DELEGATION_BETA_ALLOWLIST` accepts a simple comma-separated list of email addresses:

```bash
# Single user
VITE_DELEGATION_BETA_ALLOWLIST=alice@example.com

# Multiple users
VITE_DELEGATION_BETA_ALLOWLIST=alice@example.com,bob@example.com,charlie@example.com

# No spaces around commas
VITE_DELEGATION_BETA_ALLOWLIST=alice@example.com,bob@example.com
```

**Note**: Only users with emails in this list will see the delegation interface in production.

### Monitoring User Behavior

Enable analytics logging in staging for 1–2 days to observe how beta users interact with the feature:

```bash
# .env.staging (or .env.production during beta)
VITE_LOG_ANALYTICS=true
```

**Key Analytics Events to Monitor:**

1. **`delegation_opened`** - How often users open the delegation modal
2. **`delegation_created`** - Success rate of delegation creation
3. **`delegation_revoked`** - How often users revoke delegations
4. **`delegation_viewed`** - General engagement with delegation UI

### Beta Testing Timeline

**Week 1**: Deploy with beta allowlist, monitor analytics
**Week 2**: Gather feedback, fix any issues
**Week 3**: Expand allowlist if needed, continue monitoring
**Week 4**: Evaluate readiness for full rollout

### Full Rollout

When ready for general availability:

```bash
# .env.production
VITE_DELEGATION_ENABLED=true
VITE_DELEGATION_BETA_ALLOWLIST=
VITE_LOG_ANALYTICS=false
```

This enables delegation for all users while removing the allowlist restriction.

## UX Validation

Before full rollout, conduct user experience validation to ensure the delegation interface is intuitive and accessible.

### Validation Goals

Run short 10-minute sessions with 5–7 beta users to validate that the delegation system is self-explanatory and usable without guidance.

### Test Tasks

Ask users to complete these three tasks without any help or explanation:

1. **Understand "delegation" from UI copy** - Can they explain what delegation means based on the interface text alone?

2. **Set a global delegate, then revoke it** - Can they successfully:
   - Find and open the delegation interface
   - Search for and select a user
   - Create a global delegation
   - Locate and revoke the delegation

3. **Change a delegate on a poll with an active delegation** - Can they:
   - Navigate to a poll page
   - Understand the delegation banner
   - Modify their delegation for that specific poll

### Success Criteria

**Target**: 80% or more of users complete all three tasks without assistance.

If fewer than 80% succeed, the interface needs refinement before full rollout.

### Iterating Based on Results

After each validation session:

1. **Note confusion points** - What terms, buttons, or flows caused hesitation?
2. **Update copy** - Modify text in `frontend/src/i18n/en/delegation.ts` to address common misunderstandings
3. **Refine interactions** - Adjust button placement, modal flow, or visual hierarchy as needed
4. **Re-test** - Run another validation session with the updated interface

### Post-Validation Updates

Once validation is complete:

1. **Replace screenshot placeholders** in this documentation with actual interface screenshots
2. **Update user-facing copy** based on validation feedback
3. **Document any final UX decisions** for future reference

## Gradual Ramp

After successful UX validation, gradually expand access to the delegation feature using a controlled rollout approach.

### Weekly Expansion Strategy

Start with your validated beta users and systematically increase access:

**Week 1**: Initial beta allowlist (5–7 users)
**Week 2**: Double the allowlist size (10–14 users)
**Week 3**: Double again (20–28 users)
**Week 4**: Double again (40–56 users)

Monitor for issues after each expansion before proceeding to the next week.

### Full Launch Configuration

If no major errors or negative feedback emerge during the gradual ramp:

```bash
# .env.production
VITE_DELEGATION_ENABLED=true
VITE_DELEGATION_BETA_ALLOWLIST=
```

**Key Points:**
- `VITE_DELEGATION_ENABLED=true` - Enables delegation for all users
- `VITE_DELEGATION_BETA_ALLOWLIST=` - Empty allowlist (no restrictions)
- Feature flag code remains in place for potential rollback

### Rollback Strategy

Keep the feature flag infrastructure intact even after full launch:

```typescript
// This code should remain in the codebase
if (!canUseDelegation(user?.email)) {
  return null; // Hide delegation UI
}
```

If issues arise, you can quickly disable the feature by setting:
```bash
VITE_DELEGATION_ENABLED=false
```

### Monitoring During Ramp

Track these metrics during each expansion phase:
- Error rates in delegation-related API calls
- User support tickets mentioning delegation
- Analytics events for delegation interactions
- Performance impact on the application

### Final State

When fully launched, the allowlist should be empty:
```bash
VITE_DELEGATION_BETA_ALLOWLIST=
```

This ensures no user restrictions remain in production.

## Post-Launch Hygiene

After the delegation feature is fully launched, maintain these ongoing tasks to ensure quality and accessibility.

### Frontend Maintenance

1. **Delegation Status Enhancement**
   - ✅ Added "delegation since" information to DelegationStatus component
   - Format: "Delegating to Alice since May 3, 2025"
   - Shows in both compact and full status modes
   - Updates automatically when delegation data includes `created_at`

2. **Accessibility Compliance**
   - ✅ Added axe-core accessibility tests for delegation components
   - Tests run in CI to prevent new accessibility violations
   - Covers delegation status, modal, and poll banner components
   - Enforces WCAG 2.0/2.1 AA standards

### Backend Monitoring

3. **Usage Metrics Tracking**
   - ✅ Added daily counter metrics for delegation events
   - Tracks: `delegation_created`, `delegation_revoked`
   - Logs metrics with user context for analysis
   - Simple in-memory storage (upgrade to Redis in production)

4. **Analytics Integration**
   - Monitor key events: `delegation_opened`, `delegation_created`, `delegation_revoked`
   - Set `VITE_LOG_ANALYTICS=true` in staging for 1–2 days
   - Review user behavior patterns and conversion rates

### Quality Assurance

5. **Accessibility Testing**
   - Run `npm run test:e2e:accessibility` to check delegation components
   - CI automatically fails if new accessibility violations are introduced
   - Test covers ARIA attributes, keyboard navigation, and screen reader compatibility

6. **Copy Updates**
   - Update `frontend/src/i18n/en/delegation.ts` based on user feedback
   - Address confusion points identified in UX validation
   - Maintain clear, accessible language throughout

### Ongoing Tasks

7. **Screenshot Updates**
   - Replace placeholder screenshots in this documentation
   - Capture actual delegation interface states
   - Update after any significant UI changes

8. **Performance Monitoring**
   - Monitor delegation API response times
   - Track delegation-related database query performance
   - Alert on any degradation in delegation functionality

9. **User Support**
   - Monitor delegation-related support tickets
   - Update FAQ and help documentation based on common issues
   - Provide clear guidance for delegation best practices

### Maintenance Schedule

**Weekly:**
- Review delegation metrics and usage patterns
- Check accessibility test results
- Monitor for any delegation-related errors

**Monthly:**
- Update delegation copy based on user feedback
- Review and optimize delegation-related database queries
- Update documentation with any interface changes

**Quarterly:**
- Conduct accessibility audit of delegation components
- Review delegation feature usage analytics
- Plan any major delegation feature improvements

## Technical Details

### API Endpoints

- `GET /api/delegations/me` - Get current delegation status
- `POST /api/delegations/` - Create new delegation
- `DELETE /api/delegations/` - Revoke delegation
- `GET /api/users/search?q=query` - Search for users to delegate to

### Data Structure

```typescript
interface DelegationInfo {
  global?: GlobalDelegation;
  poll?: PollDelegation;
}

interface GlobalDelegation {
  to_user_id: string;
  to_user_name?: string;
  active: boolean;
  chain: DelegationChain[];
}
```

### Analytics

The system tracks delegation interactions for understanding usage:

- `trackDelegationViewed()` - When delegation status is viewed
- `trackDelegationOpened()` - When modal is opened
- `trackDelegationCreated(scope)` - When delegation is created
- `trackDelegationRevoked(scope)` - When delegation is revoked
- `trackOnboardingSeen()` - When onboarding tooltip is seen

## Best Practices

### For Users

1. **Choose wisely**: Delegate to people whose judgment you trust
2. **Stay informed**: You can revoke delegation at any time
3. **Consider scope**: Use poll-specific delegation for unfamiliar topics
4. **Check chains**: Understand how your vote flows through the system

### For Developers

1. **Feature flags**: Always check `delegationEnabled` before rendering
2. **Optimistic updates**: Provide immediate feedback for better UX
3. **Error handling**: Gracefully handle API failures
4. **Accessibility**: Test with screen readers and keyboard navigation

## Troubleshooting

### Common Issues

**"I can't see the delegation status"**
- Check if you're logged in
- Verify the feature flag is enabled
- Clear browser cache and reload

**"Search isn't working"**
- Ensure you're typing at least 2 characters
- Check your internet connection
- Try refreshing the page

**"I can't revoke my delegation"**
- Make sure you're clicking the correct button
- Check if there are any network errors
- Try logging out and back in

### Support

If you encounter issues with the delegation system:

1. Check the browser console for error messages
2. Try refreshing the page
3. Contact the development team with specific error details

## Screenshots

*Note: Screenshots would be added here showing:*
- Header delegation status (compact mode)
- Delegation modal with search results
- Poll page with delegation banner
- Onboarding tooltip
