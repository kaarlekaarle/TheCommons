# Frontend Quality Gates

This document outlines the quality gates and processes for maintaining code quality in the frontend codebase.

## Quality Gates

### 1. TypeScript Compilation
- **Command**: `npm run typecheck`
- **Requirement**: 0 errors
- **Purpose**: Ensures type safety across the codebase

### 2. ESLint Linting
- **Command**: `npm run lint`
- **Requirement**: ≤25 warnings (with grace window)
- **Purpose**: Enforces code style and catches common issues

### 3. CI/CD Integration
- **Workflow**: `.github/workflows/frontend-quality.yml`
- **Triggers**: Push to main, PRs with frontend changes
- **Requirements**: Both typecheck and lint must pass

## Pre-commit Hooks

### Husky + lint-staged
- **Setup**: `npm run prepare` (installs husky)
- **Hook**: `.husky/pre-commit`
- **Action**: Runs `eslint --fix` on staged TypeScript/React files
- **Purpose**: Catch issues before they reach the repository

## React Hooks Dependencies

### Handling Dependency Warnings

For intentional one-shot effects, use:
```typescript
// eslint-disable-next-line react-hooks/exhaustive-deps -- intentional one-time initialization
useEffect(() => {
  // Effect logic
}, []);
```

For data loaders, wrap in useCallback:
```typescript
const fetchData = useCallback(async () => {
  // Fetch logic
}, [dependencies]);

useEffect(() => {
  fetchData();
}, [fetchData]);
```

### Common Patterns

1. **Initialization effects**: Use eslint-disable with reason
2. **Data fetching**: Wrap in useCallback and include in deps
3. **Event listeners**: Include cleanup in return function
4. **Form validation**: Use useCallback for validation functions

## Test File Overrides

Test files are configured with relaxed rules in `eslint.config.js`:
- `@typescript-eslint/no-explicit-any`: off
- `@typescript-eslint/no-unused-vars`: warn only
- `react-hooks/exhaustive-deps`: off

## Scripts Reference

```bash
# Type checking
npm run typecheck

# Linting
npm run lint
npm run lint:fix

# Pre-commit (automatic)
git commit  # Runs lint-staged automatically

# Manual pre-commit check
npx lint-staged
```

## Current Baseline

- **TypeScript errors**: 0
- **ESLint warnings**: 21 (target: ≤25)
- **Test files**: Quarantined with overrides

## Maintenance

1. **Weekly**: Review and address new warnings
2. **Monthly**: Update baseline if needed
3. **On major changes**: Adjust warning limits

## Troubleshooting

### Common Issues

1. **Pre-commit fails**: Run `npm run lint:fix` manually
2. **Type errors**: Check imports and type definitions
3. **Hook warnings**: Add eslint-disable or fix dependencies

### Getting Help

- Check existing patterns in the codebase
- Review this document for common solutions
- Ask team for guidance on complex cases
