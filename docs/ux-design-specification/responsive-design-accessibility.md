# Responsive Design & Accessibility

## Responsive Strategy

**Platform Priorities:**
1. Desktop (1024px+) - Primary platform for all roles, full feature set
2. Tablet (768-1023px) - Secondary platform, touch-optimized, slightly simplified
3. Mobile (<768px) - Minimal scope for MVP (view-only features, not management)

**Desktop Strategy:**
- Persistent left sidebar navigation (240px, collapsible to 64px icons-only)
- Multi-column layouts (4-6 column asset grids, multi-column data tables)
- Desktop-specific features: Keyboard shortcuts (Cmd+K search), hover states, drag-drop everywhere, Shift+click multi-select
- Three-panel layouts for Publisher: Folders (left) + Assets (center) + Details (right)

**Tablet Strategy:**
- Collapsible sidebar (icons-only by default, expands on tap, overlays content)
- 2-3 column asset grids, stacked forms, single-column content
- Touch-optimized: 44x44px minimum touch targets, larger tap areas (56px table rows), touch gestures (swipe to delete, pull-to-refresh)
- No hover dependencies (quick actions always visible, not hover-only)

**Mobile Strategy:**
- Top bar + hamburger menu (full-screen slide-in menu)
- Single column everything (stacked asset cards, full-width components)
- Cards replace tables (tables don't work on small screens)
- Critical information only: Student (assignments + download), Teacher (my content), Developer (API status), Publisher (not optimized)

## Breakpoint Strategy

**Tailwind CSS Default Breakpoints (Mobile-First):**
- **Base (320-639px):** Single column, stacked layouts, minimal chrome
- **sm (640-767px):** Large phones, still mostly mobile layout
- **md (768-1023px):** Tablet, collapsible sidebar, 2-3 columns, touch-optimized
- **lg (1024-1279px):** Desktop, full sidebar, 3-4 columns, desktop features enabled
- **xl (1280-1535px):** Optimal desktop, 4-6 columns, full metadata
- **2xl (1536px+):** Large desktop, max content width 1440px

**Responsive Principles:**
- Mobile-first approach (base styles for mobile, enhance for larger screens)
- Content over chrome (navigation/sidebars collapse on smaller screens)
- Touch-friendly everywhere (44px targets even on desktop benefit both mouse and touch users)
- Performance-first (mobile gets smaller images, lazy-loaded components, reduced bundles)

## Accessibility Strategy

**Compliance Level: WCAG 2.1 Level AA (Required)**

**Rationale:**
- EdTech product subject to Section 508 and ADA requirements
- Enterprise customers demand AA compliance for procurement
- European Accessibility Act (2025) mandates AA for digital services
- Student population includes people with disabilities

**Key Requirements:**

**1. Color Contrast (WCAG 1.4.3, Level AA)**
- Normal text (16px+): 4.5:1 minimum ✅ All colors tested and documented
- Large text (24px+): 3:1 minimum ✅
- UI components: 3:1 for focus indicators, borders, icons ✅
- Color never sole indicator (always pair with icon + text)

**2. Keyboard Navigation (WCAG 2.1.1, Level A)**
- All functionality keyboard accessible (Tab, Enter, Space, Escape, Arrow keys)
- Visible focus indicators (2px solid blue outline on all interactive elements)
- Skip links ("Skip to main content" at page top, hidden until focused)
- Keyboard shortcuts: Cmd+K (search), Cmd+U (upload), ? (show shortcuts)

**3. Screen Reader Compatibility (WCAG 4.1.2, Level A)**
- Semantic HTML structure (proper heading hierarchy, lists, tables)
- ARIA labels on all buttons, links, form inputs
- ARIA landmarks (nav, main, aside, role="search")
- Live regions for dynamic content (upload progress, error announcements)
- Screen reader testing: VoiceOver (macOS), NVDA (Windows), JAWS (Windows)

**4. Touch Target Sizes (WCAG 2.5.5, Level AAA - Implemented as Baseline)**
- Minimum 44x44px for all interactive elements
- 8px spacing between touch targets
- 56px table row height for generous tap area
- 48px minimum form input height

**5. Motion and Animation (WCAG 2.3.3, Level AAA - Implemented as Best Practice)**
- Respect prefers-reduced-motion media query
- No flashing content (nothing flashes >3 times/second)
- Subtle, functional animations only (200ms transitions, 300ms page transitions)
- No critical content relies on animation

## Testing Strategy

**Automated Accessibility Testing:**
- axe DevTools (Chrome extension) - Scan every page/component
- Playwright + axe-core - Automated a11y tests in CI/CD pipeline
- Lighthouse CI - Accessibility score >95 required for production
- Run frequency: Pre-commit hooks, PR checks (blocks merge on violations), weekly production scans

**Manual Accessibility Testing:**
- Keyboard navigation - Tab through every page without mouse
- Screen reader testing - VoiceOver + Safari (macOS), NVDA + Firefox (Windows)
- Testing checklist: Alt text on images, labels on inputs, error announcements, descriptive link text, proper heading hierarchy

**Responsive Testing:**
- Real devices: MacBook Pro 16", iPad Pro 12.9", iPad 10.2", iPhone 14 Pro, Samsung Galaxy S23
- Browsers: Chrome (primary), Safari (secondary), Firefox, Edge
- Breakpoint testing: 320px, 640px, 768px, 1024px, 1280px, 1536px
- Network performance: Slow 3G simulation, offline behavior, large file handling on mobile

**Testing Checklist:**
- [ ] No horizontal scroll on any screen size
- [ ] Text readable without zoom (16px minimum)
- [ ] Touch targets 44x44px on tablet/mobile
- [ ] All interactive elements keyboard accessible
- [ ] Focus indicators visible on all focusable elements
- [ ] Color contrast ratios meet 4.5:1 (normal text) and 3:1 (large text/UI)
- [ ] Screen reader announces all content correctly
- [ ] Forms completable with keyboard only
- [ ] Videos play on all devices

## Implementation Guidelines

**Responsive Development:**
- Use mobile-first media queries: `className="grid-cols-1 md:grid-cols-2 lg:grid-cols-4"`
- Responsive typography: Minimum 16px body text, scale up on larger screens
- Conditional rendering (not hiding): Don't render heavy components on mobile
- Touch-optimized spacing: Increase gaps between tappable elements on mobile

**Accessibility Development:**
- Semantic HTML structure: Use nav, main, section, article, aside (not div soup)
- Form accessibility: Labels with htmlFor, aria-describedby for help text, aria-invalid for errors
- Focus management: Trap focus in modals, restore focus on close, skip links on every page
- ARIA live regions: aria-live="polite" for status updates, role="alert" for errors
- Reduced motion support: Disable animations when prefers-reduced-motion detected

**Code Examples:**
```javascript
// Mobile-first responsive grid
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">

// Touch-optimized button
<button className="h-11 md:h-12 px-4 md:px-6">

// Accessible form input
<label htmlFor="email">Email *</label>
<input
  id="email"
  aria-required="true"
  aria-describedby="email-help"
/>
<span id="email-help">We'll never share your email</span>

// Skip link (hidden until focused)
<a
  href="#main-content"
  className="sr-only focus:not-sr-only focus:absolute focus:top-4"
>
  Skip to main content
</a>
```
