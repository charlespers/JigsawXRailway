# Quick Start Guide

## Installation

```bash
cd frontend
npm install
```

## Development

```bash
npm run dev
```

The landing page will be available at `http://localhost:5173`

## Build for Production

```bash
npm run build
```

The production build will be in the `dist/` directory.

## Features Implemented

✅ **All 11 Sections:**
1. Hero section with email signup
2. Problem section ("Why PCB design is broken")
3. Product section (4-step workflow)
4. Roadmap section (Today/Next)
5. Target users (4 user types)
6. Social proof & credibility
7. Technical depth ("Under the hood")
8. Founders section
9. Primary CTA
10. Footer with investor section
11. Navbar with smooth scrolling

✅ **Design System:**
- Dark theme with neon teal (#00ffd1) and electric orange (#ff6b35)
- Circuit trace motifs and grid backgrounds
- Subtle animations with Framer Motion
- Responsive layout (mobile-first)
- Clean, spacious layout like Figma/Cursor/IDE

✅ **Technical:**
- React 18 + TypeScript
- Vite for fast development
- Tailwind CSS for styling
- Framer Motion for animations
- Lucide React for icons

## Customization

### Colors
Edit `tailwind.config.js` to change accent colors:
- `neon-teal`: Primary accent color
- `electric-orange`: Secondary accent color

### Content
Each section is a separate component in `src/components/`:
- Edit component files to update copy
- All text is easily editable in the component files

### Fonts
Fonts are loaded from Google Fonts in `index.html`:
- Headings: Space Grotesk
- Body: Inter

## Deployment

### Vercel (Recommended)
1. Push to GitHub
2. Import project in Vercel
3. Build command: `npm run build`
4. Output directory: `dist`
5. Deploy!

### Netlify
1. Push to GitHub
2. Connect repo in Netlify
3. Build command: `npm run build`
4. Publish directory: `dist`
5. Deploy!

### Static Hosting
After running `npm run build`, upload the `dist/` folder to any static hosting service.

