# React + TypeScript + Vite

This template provides a minimal setup to get React working in Vite with HMR and some ESLint rules.

## Environment Setup

Create a `.env.local` file in the frontend directory with the following variables:

```bash
# API Configuration
VITE_API_BASE_URL=http://localhost:8000

# Feature Flags
VITE_COMPASS_ENABLED=true
VITE_PRINCIPLES_DOC_MODE=true  # Enable new living document UI
VITE_DELEGATION_ENABLED=true
VITE_USE_HARDCODED_DATA=true
VITE_USE_DEMO_CONTENT=true

# Debug
VITE_DEBUG_OVERLAY=false

# Development
NODE_ENV=development
```

### Quick Setup

```bash
# Copy and modify the example (if it exists)
cp .env.example .env.local

# Or create manually
echo "VITE_PRINCIPLES_DOC_MODE=true" > .env.local
echo "VITE_USE_HARDCODED_DATA=true" >> .env.local
echo "VITE_API_BASE_URL=http://localhost:8000" >> .env.local
```

### Feature Flags Explained

- `VITE_PRINCIPLES_DOC_MODE=true` - Enables the new living document UI for Level A principles
- `VITE_USE_HARDCODED_DATA=true` - Uses placeholder data instead of API calls (for development)
- `VITE_COMPASS_ENABLED=true` - Enables the compass feature
- `VITE_DELEGATION_ENABLED=true` - Enables delegation functionality

## Development

```bash
npm install
npm run dev
```

Visit `http://localhost:5173` and navigate to `/compass/hardcoded-1` to see the new living document UI.

Currently, two official plugins are available:

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react) uses [Babel](https://babeljs.io/) for Fast Refresh
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react-swc) uses [SWC](https://swc.rs/) for Fast Refresh

## Expanding the ESLint configuration

If you are developing a production application, we recommend updating the configuration to enable type-aware lint rules:

```js
export default tseslint.config([
  globalIgnores(['dist']),
  {
    files: ['**/*.{ts,tsx}'],
    extends: [
      // Other configs...

      // Remove tseslint.configs.recommended and replace with this
      ...tseslint.configs.recommendedTypeChecked,
      // Alternatively, use this for stricter rules
      ...tseslint.configs.strictTypeChecked,
      // Optionally, add this for stylistic rules
      ...tseslint.configs.stylisticTypeChecked,

      // Other configs...
    ],
    languageOptions: {
      parserOptions: {
        project: ['./tsconfig.node.json', './tsconfig.app.json'],
        tsconfigRootDir: import.meta.dirname,
      },
      // other options...
    },
  },
])
```

You can also install [eslint-plugin-react-x](https://github.com/Rel1cx/eslint-react/tree/main/packages/plugins/eslint-plugin-react-x) and [eslint-plugin-react-dom](https://github.com/Rel1cx/eslint-react/tree/main/packages/plugins/eslint-plugin-react-dom) for React-specific lint rules:

```js
// eslint.config.js
import reactX from 'eslint-plugin-react-x'
import reactDom from 'eslint-plugin-react-dom'

export default tseslint.config([
  globalIgnores(['dist']),
  {
    files: ['**/*.{ts,tsx}'],
    extends: [
      // Other configs...
      // Enable lint rules for React
      reactX.configs['recommended-typescript'],
      // Enable lint rules for React DOM
      reactDom.configs.recommended,
    ],
    languageOptions: {
      parserOptions: {
        project: ['./tsconfig.node.json', './tsconfig.app.json'],
        tsconfigRootDir: import.meta.dirname,
      },
      // other options...
    },
  },
])
```

## Features Pipeline

The landing page "Current Features" section is automatically synchronized with the features configuration.

### How it works:

1. **Edit features**: Modify `src/config/features.ts` to add, remove, or update features
2. **Auto-sync**: The development server watches for changes and regenerates `features.generated.json`
3. **Build integration**: Production builds sync features before bundling
4. **CI validation**: GitHub Actions ensures the generated file is always up to date
5. **Type safety**: Features are validated for correct structure (title, description, optional icon)

### Available commands:

- `npm run sync:features` - Manually sync features once
- `npm run sync:features:watch` - Watch for changes and auto-sync
- `npm run check:features` - Verify the generated file is up to date
- `npm run dev` - Development server with auto-sync enabled
- `npm run build` - Build with features sync

### File structure:

```
src/config/
├── features.ts              # Source features configuration
├── features.generated.json  # Generated manifest (committed)
└── types/json.d.ts         # TypeScript declarations
```

### Note on Git hooks:

Since Husky is not configured in this project, please manually run `npm run sync:features` before committing changes to `features.ts` to ensure the generated file is up to date.
