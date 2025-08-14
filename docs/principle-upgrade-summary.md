# Principle Proposal Upgrade Summary

## Overview

We have successfully upgraded principle proposal pages to follow a clear, structured, and high-level format modeled after the "Complete Streets Policy" example. This upgrade transforms basic principle descriptions into comprehensive, engaging decision frameworks.

## What Was Implemented

### 1. **New Structured Content Format**

Each principle now follows this consistent structure:

1. **Title + Compass Framing**
   - Example: "Open Data & Transparency Policy – A foundational compass that guides government accountability and public trust."

2. **The Question**
   - Clear binary choice presenting the central trade-off
   - Example: "Should Riverbend publish all public datasets openly by default, or maintain selective disclosure with controlled access?"

3. **Direction 1 & Direction 2**
   - Short description (one line)
   - **Why choose this direction?** – 4–6 rationale bullets
   - **Counterarguments** – 3–5 bullets, fairly expressed

4. **Community Alignment (so far)**
   - Visual alignment bar and counts
   - Shows current voting results

5. **Community Reasoning (examples)**
   - 3–4 short quotes, tagged with perspective (equity, business, etc.)
   - Balanced to show different worldviews

6. **Background (with Read More)**
   - Short contextual overview
   - Expandable with additional details

### 2. **New Components Created**

- **`PrincipleProposal.tsx`**: Main component that renders the structured format
- **`principles.ts`**: Content file containing all upgraded principle copy
- **Integration with existing components**: Reuses `DirectionCard`, `Expandable`, and other Compass components

### 3. **Upgraded Principles**

We've created structured content for 6 key principles:

1. **Open Data & Transparency Policy**
   - Trade-off: Open by default vs. controlled access
   - Focus: Government accountability and public trust

2. **Vision Zero Safety Commitment**
   - Trade-off: Vision Zero vs. incremental improvements
   - Focus: Transportation safety and human life

3. **Climate Equity Action Plan**
   - Trade-off: Net-zero by 2040 vs. gradual improvements
   - Focus: Climate justice and equitable benefits

4. **Affordable Housing Priority**
   - Trade-off: Strong policies vs. market-driven development
   - Focus: Housing justice and community diversity

5. **Participatory Budgeting Program**
   - Trade-off: Direct democracy vs. traditional processes
   - Focus: Democratic engagement and budget allocation

6. **Digital Inclusion & Access**
   - Trade-off: Universal access vs. market-driven development
   - Focus: Technology equity and digital divide

### 4. **Content Guidelines Followed**

✅ **Concise, declarative sentences**
✅ **Avoided advocacy tone** - each side presented with equal clarity
✅ **Highlighted core trade-offs** - safety vs. congestion, cost vs. long-term savings, etc.
✅ **Concrete rationale bullets** - not abstract concepts
✅ **Short, expandable background** with "Read more" functionality

### 5. **Technical Implementation**

- **Dynamic loading**: Principle proposals automatically use the new format when structured content exists
- **Fallback support**: Proposals without structured content show a basic format with upgrade notice
- **Reusable components**: Leverages existing Compass page components for consistency
- **Type safety**: Full TypeScript support with proper interfaces

## Key Features

### **Binary Choice Framework**
Each principle presents a clear either/or choice that fundamentally shapes the community's approach to that issue.

### **Balanced Perspectives**
Both directions are presented fairly with:
- Strong rationale for each choice
- Honest counterarguments from the opposing view
- Community examples showing diverse perspectives

### **Accessibility & UX**
- Proper ARIA roles and keyboard navigation
- Expandable sections for detailed content
- Visual progress bars for community alignment
- Responsive design for all screen sizes

### **Community Engagement**
- Real voting results displayed
- Community reasoning examples
- Background context for informed decisions

## Benefits

1. **Clarity**: Complex policy decisions are broken down into clear binary choices
2. **Engagement**: Structured format makes principles more accessible and engaging
3. **Balance**: Fair presentation of both sides encourages thoughtful consideration
4. **Context**: Background information helps residents understand the broader implications
5. **Consistency**: All principles follow the same proven format

## Usage

When users visit a principle proposal page:

1. **Level A proposals** automatically use the new structured format
2. **Level B proposals** continue to use the existing action format
3. **Fallback handling** ensures all proposals display properly

## Future Expansion

The system is designed to easily add more principles:

1. Add new principle copy to `principles.ts`
2. Follow the established structure and guidelines
3. The component automatically picks up new content

## Files Modified/Created

### New Files
- `frontend/src/copy/principles.ts` - Structured principle content
- `frontend/src/components/principle/PrincipleProposal.tsx` - Main component
- `docs/principle-upgrade-summary.md` - This documentation

### Modified Files
- `frontend/src/pages/ProposalDetail.tsx` - Integration with new component

## Conclusion

This upgrade transforms principle proposals from simple descriptions into engaging decision frameworks that:
- Present clear choices
- Provide balanced perspectives
- Include community context
- Maintain accessibility standards
- Follow proven UX patterns

The structured format makes complex policy decisions more accessible and engaging for all residents, while maintaining the warm, inclusive, and hopeful tone that defines The Commons platform.
