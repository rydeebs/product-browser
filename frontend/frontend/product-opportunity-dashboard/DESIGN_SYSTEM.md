# Design System Documentation

## Overview
This document outlines the design system for the Product Opportunity Dashboard. Follow these guidelines to maintain visual consistency across all pages and components.

---

## Color Palette

### Background Colors
- **Primary Background**: `#0a0a0a` to `#1a1a1a` (gradient)
- **Card Background**: `#1f1f1f`
- **Sidebar Background**: `#0a0a0a`

### Accent Colors
- **Primary Blue**: `#444df6`
- **Secondary Blue**: `#010df0`
- **Blue Gradient**: `from-white via-blue-400 to-[#444df6]`

### Text Colors
- **Primary Text**: `#ffffff`
- **Secondary Text**: `#a0a0a0` / `text-muted-foreground`
- **Heading Gradient**: `bg-gradient-to-r from-white via-blue-400 to-[#444df6]` (for H1 titles)

### UI Elements
- **Border**: `#2a2a2a` / `border`
- **Hover State**: Blue glow effect with `shadow-lg shadow-blue-500/20`

### Badge Colors
- **Category Badges**: `bg-blue-500/20 text-blue-400 border-blue-500/30`
- **Timing Badges**: `bg-purple-500/20 text-purple-400 border-purple-500/30`
- **Pain Level Badges**: `bg-orange-500/20 text-orange-400 border-orange-500/30`
- **Active Category**: `bg-gradient-to-r from-purple-600 to-blue-600`

---

## Typography

### Font Families
- **Display Font (H1, H2)**: `Marcellus` - Use class `font-display`
  - For major headings and titles
  - Elegant serif font for editorial feel
  
- **Headings Font (H3-H6)**: `Newsreader` - Use class `font-serif`
  - For card titles and subheadings
  - Used in opportunity cards
  
- **Body Font**: `Geist` - Use class `font-sans`
  - For all body text, descriptions, labels
  - Default font for most UI elements
  
- **Monospace Font**: `Geist Mono` - Use class `font-mono`
  - For code, metrics, technical data

### Font Sizes & Weights
- **H1**: `text-5xl md:text-6xl font-bold` (Product of the Day)
- **H2**: `text-2xl font-bold` (Section headings)
- **H3**: `text-3xl font-bold` (Card titles in featured section)
- **H4**: `text-xl font-semibold` (Card titles in carousel)
- **Body Large**: `text-base`
- **Body Regular**: `text-sm`
- **Small Text**: `text-xs`

### Text Styling
- **Gradient Text**: Apply `bg-gradient-to-r from-white via-blue-400 to-[#444df6] bg-clip-text text-transparent` for hero headings
- **Muted Text**: Use `text-muted-foreground` for secondary information
- **Line Height**: `leading-relaxed` for body text

---

## Spacing & Layout

### Container Widths
- **Sidebar**: `w-60` (240px fixed width)
- **Main Content**: `flex-1` with `max-w-7xl mx-auto`
- **Cards**: Full width with padding

### Padding & Margins
- **Section Padding**: `p-8`
- **Card Padding**: `p-6`
- **Card Gap**: `gap-4` or `gap-6`
- **Sidebar Item Padding**: `px-4 py-2.5`

### Border Radius
- **Cards**: `rounded-lg`
- **Buttons**: `rounded-md`
- **Badges**: `rounded-full`
- **Inputs**: `rounded-md`

---

## Components

### Sidebar Navigation
- Fixed width: 240px (`w-60`)
- Category items with hover state
- Active state: Blue/purple gradient background
- Count badges: Muted background, small text
- Icons from `lucide-react` library

### Opportunity Cards

#### Featured Card (Product of the Day)
- Large format with `p-6` padding
- Title: `font-serif text-3xl font-bold`
- 3-4 colored badges at top
- Problem summary: 2-3 lines, `text-muted-foreground`
- Metrics with gradient progress bars
- Charts section with visualizations

#### Carousel Cards
- Compact format: `min-w-[380px]`
- Title: `font-serif text-xl font-semibold`
- Hover effect: `hover:-translate-y-1 hover:shadow-lg hover:shadow-blue-500/20`
- Transition: `transition-all duration-300`

### Progress Bars
- Background: `bg-gray-800`
- Fill: `bg-gradient-to-r from-white via-blue-400 to-[#444df6]`
- Height: `h-2` (8px)
- Rounded: `rounded-full`

### Badges
- Style: `rounded-full px-3 py-1 text-xs font-medium border`
- Variants:
  - Blue (category): `bg-blue-500/20 text-blue-400 border-blue-500/30`
  - Purple (timing): `bg-purple-500/20 text-purple-400 border-purple-500/30`
  - Orange (pain): `bg-orange-500/20 text-orange-400 border-orange-500/30`

### Buttons
- Primary: Blue background with hover effects
- Ghost: Transparent with border, blue on hover
- Icon buttons: Circular, centered icon
- Transition: `transition-colors`

### Charts & Metrics
- Bar charts: Blue gradient bars
- Circular gauges: Blue stroke color
- Text labels: Muted foreground color
- Chart containers: Dark background with subtle border

---

## Animations & Transitions

### Hover Effects
- **Cards**: `hover:-translate-y-1` + `hover:shadow-lg hover:shadow-blue-500/20`
- **Buttons**: `hover:bg-blue-600` or `hover:bg-accent`
- **Sidebar Items**: `hover:bg-gray-800/50`
- **Duration**: `transition-all duration-300`

### Scroll Behavior
- Horizontal carousel: `scroll-smooth`
- Hide scrollbar: `scrollbar-hide` class

### Loading States
- Use subtle animations for skeleton loaders
- Fade-in for content appearance

---

## Iconography

### Icon Library
- **Primary**: `lucide-react`
- **Size**: Usually `h-4 w-4` or `h-5 w-5`
- **Color**: Match text color or use explicit color classes

### Common Icons
- Home: `Home`
- Categories: `Sparkles`, `PawPrint`, `Heart`, `Baby`, `UtensilsCrossed`, `Cpu`, `Mountain`
- Navigation: `ChevronLeft`, `ChevronRight`
- Metrics: `TrendingUp`, `BarChart3`, `Activity`
- UI: `Search`, `SlidersHorizontal`

---

## Responsive Design

### Breakpoints
- **Mobile**: Base styles (< 768px)
- **Tablet**: `md:` prefix (≥ 768px)
- **Desktop**: `lg:` prefix (≥ 1024px)

### Layout Adjustments
- Sidebar: Hidden on mobile (implement hamburger menu if needed)
- Grid: 1 column mobile, 2 columns desktop
- Carousel: Scrollable on all screen sizes
- Typography: Scale down on mobile (`text-5xl md:text-6xl`)

---

## Best Practices

1. **Always use design tokens**: Reference color variables from `globals.css`
2. **Consistent spacing**: Use Tailwind's spacing scale (4px increments)
3. **Maintain contrast**: Ensure text is readable on dark backgrounds
4. **Use semantic HTML**: Proper heading hierarchy, landmarks
5. **Smooth transitions**: Apply `transition-all duration-300` to interactive elements
6. **Gradient usage**: Reserve gradients for primary headings and progress bars
7. **Icon consistency**: Use lucide-react icons consistently, same sizing
8. **Whitespace**: Don't be afraid of generous padding and margins

---

## Theme Configuration

The theme is configured in `app/globals.css` using Tailwind CSS v4:

```css
@theme inline {
  --font-sans: 'Geist', sans-serif;
  --font-mono: 'Geist Mono', monospace;
  --font-serif: 'Newsreader', serif;
  --font-display: 'Marcellus', serif;
}
```

---

## Design Inspiration

This design system is inspired by:
- **IdeaBrowser**: Clean, editorial layout with serif typography
- **Modern SaaS Dashboards**: Dark mode, metric-driven interfaces
- **Data Visualization Tools**: Clear, accessible charts and progress indicators
- **Premium Feel**: Gradients, smooth animations, generous whitespace
