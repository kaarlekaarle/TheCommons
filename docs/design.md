# Civic UI Design System

The Commons uses a trustworthy, accessible "Civic UI" visual language inspired by USWDS/GOV.UK design principles. This system prioritizes readability, restraint, and accessibility over visual flair.

## Color Palette

### Core Semantic Colors
- **`civic-ink`** (`#1b1b1b`) - Primary text color
- **`civic-muted-ink`** (`#4b5563`) - Secondary text color  
- **`civic-canvas`** (`#f7f7f7`) - Page background
- **`civic-surface`** (`#ffffff`) - Card background
- **`civic-border`** (`#e5e7eb`) - Lines and borders
- **`civic-brand`** (`#0b6fbf`) - Actions and links
- **`civic-brand-hover`** (`#095b99`) - Brand hover state

### Status Colors
- **`civic-success`** (`#2e7d32`) - Success green
- **`civic-warning`** (`#c77700`) - Warning orange
- **`civic-danger`** (`#b3261e`) - Danger red

### Level-Specific Colors
- **`civic-levelA`** (`#0b6fbf`) - Blue for Level A (Principles)
- **`civic-levelB`** (`#1b7f5f`) - Teal/green for Level B (Actions)

## Typography

### Type Scale (USWDS-like)
- **`xs`** (12px) - Small labels, captions
- **`sm`** (14px) - Secondary text, metadata
- **`base`** (16px) - Body text (minimum readable size)
- **`lg`** (18px) - Large body text
- **`xl`** (20px) - Small headings
- **`2xl`** (24px) - H3 headings
- **`3xl`** (30px) - H2 headings  
- **`4xl`** (36px) - H1 headings
- **`5xl`** (48px) - Large display text
- **`6xl`** (60px) - Hero text

### Line Heights
- Body text: ≥ 1.45 (AA contrast)
- Headings: ≥ 1.25 (AAA contrast)

## Utility Classes

### Cards
```css
.c-card {
  background-color: var(--civic-surface);
  border: 1px solid var(--civic-border);
  border-radius: 6px;
  box-shadow: var(--shadow-civic);
  transition: box-shadow 0.2s ease;
}
```

### Panels
```css
.c-panel {
  background-color: rgba(11, 111, 191, 0.06); /* levelA at 6% */
  border: 1px solid rgba(11, 111, 191, 0.2);
  border-radius: 6px;
  padding: 1rem;
  color: var(--civic-ink);
}
```

**Variants:**
- `.c-panel--levelA` - Blue tint for Principles
- `.c-panel--levelB` - Teal tint for Actions

### Badges
```css
.c-badge {
  display: inline-flex;
  align-items: center;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 500;
  border: 1px solid;
  background-color: rgba(255, 255, 255, 0.8);
}
```

**Variants:**
- `.c-badge--levelA` - Blue for Principles
- `.c-badge--levelB` - Teal for Actions
- `.c-badge--success` - Green for success states
- `.c-badge--warning` - Orange for warnings
- `.c-badge--danger` - Red for errors

### Links
```css
.c-link {
  color: var(--civic-brand);
  text-decoration: none;
  transition: color 0.2s ease;
}
```

## When to Use Level A vs Level B Colors

### Level A (Blue - `#0b6fbf`)
Use for **Principles** - long-term direction and foundational decisions:
- Page headers for `/principles` route
- Cards containing Level A proposals
- Direction choice chips in proposal details
- Informational panels about long-term strategy
- Navigation items when on principles pages

### Level B (Teal - `#1b7f5f`) 
Use for **Actions** - concrete, immediate decisions:
- Page headers for `/actions` route
- Cards containing Level B proposals
- Vote status indicators
- Action-oriented buttons and CTAs
- Navigation items when on actions pages

## Accessibility Requirements

### Contrast Ratios
- **AA Standard**: 4.5:1 for normal text, 3:1 for large text
- **AAA Standard**: 7:1 for normal text, 4.5:1 for large text
- All text colors meet AA standards; headings meet AAA

### Focus States
- 2px outline in `civic-brand` color
- 2px offset from element
- Visible on all interactive elements

### Touch Targets
- Minimum 44px height for buttons
- Minimum 16px font size for body text
- Adequate spacing between interactive elements

## Shadows

### Civic UI Shadows (Ultra-subtle)
- **`shadow-civic`** - `0 1px 2px rgba(0, 0, 0, 0.05)`
- **`shadow-civic-md`** - `0 2px 4px rgba(0, 0, 0, 0.08)`
- **`shadow-civic-lg`** - `0 4px 8px rgba(0, 0, 0, 0.1)`
- **`shadow-civic-xl`** - `0 8px 16px rgba(0, 0, 0, 0.12)`

## Border Radius

### Civic UI Radius Scale
- **`md`** (6px) - Primary card radius
- **`lg`** (10px) - Secondary card radius
- No pill shapes (avoid full rounded corners)

## Implementation Guidelines

1. **Use semantic color names** - `civic-ink` not `text-black`
2. **Maintain contrast ratios** - Test with color contrast tools
3. **Use utility classes** - `.c-card`, `.c-panel`, `.c-badge` for consistency
4. **Respect level colors** - Blue for Principles, Teal for Actions
5. **Keep shadows subtle** - Avoid heavy drop shadows
6. **Test accessibility** - Ensure keyboard navigation and screen reader compatibility

## Migration from Legacy Colors

The system maintains backward compatibility with legacy `gov-*` colors while encouraging migration to the new `civic-*` tokens. When updating components:

1. Replace `gov-primary` → `civic-brand`
2. Replace `gov-text` → `civic-ink`
3. Replace `gov-text-muted` → `civic-muted-ink`
4. Replace `gov-background` → `civic-canvas`
5. Replace `gov-surface` → `civic-surface`
6. Replace `gov-border` → `civic-border`
