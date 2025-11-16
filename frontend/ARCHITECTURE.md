# Architecture Documentation

## Project Structure

```
src/
├── components/
│   ├── ui/              # Reusable UI primitives
│   │   ├── Button.tsx
│   │   ├── Card.tsx
│   │   ├── Section.tsx
│   │   ├── Container.tsx
│   │   ├── Heading.tsx
│   │   ├── Badge.tsx
│   │   ├── Modal.tsx
│   │   └── index.ts     # Barrel export
│   ├── sections/        # Page sections
│   │   ├── Hero.tsx
│   │   ├── Problem.tsx
│   │   ├── Product.tsx
│   │   ├── Roadmap.tsx
│   │   ├── TargetUsers.tsx
│   │   ├── SocialProof.tsx
│   │   ├── TechnicalDepth.tsx
│   │   ├── Founders.tsx
│   │   ├── CTA.tsx
│   │   └── index.ts     # Barrel export
│   └── layout/          # Layout components
│       ├── Navbar.tsx
│       ├── Footer.tsx
│       └── InvestorModal.tsx
├── hooks/               # Custom React hooks
│   ├── useScroll.ts
│   └── useIntersectionObserver.ts
├── lib/                 # Core utilities and config
│   ├── constants.ts     # App-wide constants
│   ├── types.ts         # TypeScript types
│   ├── design-tokens.ts # Design system tokens
│   └── utils.ts         # Utility functions
├── App.tsx              # Main app component
├── main.tsx            # Entry point
└── index.css           # Global styles
```

## Design Principles

### 1. **Modularity**
- Each component is self-contained and reusable
- Clear separation between UI primitives, sections, and layout
- Barrel exports for clean imports

### 2. **Type Safety**
- All components are fully typed with TypeScript
- Centralized type definitions in `lib/types.ts`
- Props interfaces exported for external use

### 3. **Single Source of Truth**
- Constants in `lib/constants.ts`
- Design tokens in `lib/design-tokens.ts`
- No hardcoded values in components

### 4. **Composability**
- Small, focused components
- Components can be combined to build complex UIs
- Props-based customization

### 5. **Scalability**
- Easy to add new sections/components
- Consistent patterns across codebase
- Path aliases for clean imports (`@/`)

## Component Categories

### UI Primitives (`components/ui/`)
Reusable building blocks:
- **Button**: Multiple variants (primary, secondary, ghost) and sizes
- **Card**: Container with variants and hover states
- **Section**: Page section wrapper with variants
- **Container**: Responsive container with size options
- **Heading**: Typography component with size and gradient options
- **Badge**: Small label component
- **Modal**: Accessible modal dialog

### Sections (`components/sections/`)
Page-specific sections:
- Each section is self-contained
- Uses UI primitives for consistency
- Imports constants from `lib/constants.ts`
- Uses intersection observer for animations

### Layout (`components/layout/`)
Site-wide layout components:
- **Navbar**: Fixed navigation with scroll behavior
- **Footer**: Site footer with links
- **InvestorModal**: Modal for investor content

## Hooks

### `useScroll(threshold)`
Tracks scroll position and returns boolean when scrolled past threshold.

### `useIntersectionObserver(options)`
Observes element intersection with viewport for scroll animations.

## Constants & Configuration

### `lib/constants.ts`
All app content:
- `APP_CONFIG`: App name, tagline, description
- `NAV_LINKS`: Navigation links
- `BADGES`: Hero badges
- `PROBLEM_STATS`: Problem section stats
- `PRODUCT_STEPS`: Product workflow steps
- `TARGET_USERS`: User personas
- `SOCIAL_PROOF_ITEMS`: Credibility badges
- `TECH_STACK`: Technology stack
- `FOUNDERS`: Founder information
- `INVESTOR_CONTENT`: Investor section content

### `lib/design-tokens.ts`
Design system values:
- Colors (neon-teal, electric-orange, dark theme)
- Spacing scale
- Typography (fonts, sizes, weights)
- Breakpoints
- Animations (duration, easing)
- Shadows
- Z-index scale

## Adding New Components

### 1. Create Component File
```tsx
// src/components/ui/NewComponent.tsx
import { forwardRef } from 'react'
import { cn } from '@/lib/utils'

export interface NewComponentProps {
  // Props here
}

const NewComponent = forwardRef<HTMLDivElement, NewComponentProps>(
  ({ className, ...props }, ref) => {
    return (
      <div ref={ref} className={cn('base-styles', className)} {...props}>
        {/* Component content */}
      </div>
    )
  }
)

NewComponent.displayName = 'NewComponent'
export default NewComponent
```

### 2. Export from Barrel File
```tsx
// src/components/ui/index.ts
export { default as NewComponent } from './NewComponent'
export type { NewComponentProps } from './NewComponent'
```

### 3. Use in Sections
```tsx
import { NewComponent } from '@/components/ui'

export default function MySection() {
  return <NewComponent />
}
```

## Adding New Sections

1. Create section file in `components/sections/`
2. Import UI primitives and constants
3. Use intersection observer for animations
4. Export from `components/sections/index.ts`
5. Add to `App.tsx`

## Updating Content

### Text Content
Edit `lib/constants.ts` - all text content is centralized here.

### Colors
Edit `tailwind.config.js` or `lib/design-tokens.ts` for design tokens.

### Styling
- Global styles: `src/index.css`
- Component styles: Use Tailwind classes with `cn()` utility
- Design tokens: Reference `lib/design-tokens.ts`

## Best Practices

1. **Always use TypeScript** - No `any` types, proper interfaces
2. **Use path aliases** - `@/components/ui` not `../../components/ui`
3. **Compose components** - Build complex UIs from primitives
4. **Keep constants centralized** - No hardcoded strings/numbers
5. **Use intersection observer** - For scroll animations
6. **Export types** - Make component props reusable
7. **Barrel exports** - Clean import statements
8. **Consistent naming** - PascalCase for components, camelCase for functions

## Performance Considerations

- Components use `forwardRef` for ref forwarding
- Intersection observer for efficient scroll animations
- Framer Motion for performant animations
- Lazy loading ready (can add React.lazy if needed)

## Future Enhancements

- Add Storybook for component documentation
- Add unit tests with Vitest
- Add E2E tests with Playwright
- Add i18n support for internationalization
- Add theme switching (light/dark)
- Add component variants system
- Add animation presets

