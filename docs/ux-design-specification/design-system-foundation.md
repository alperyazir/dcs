# Design System Foundation

## Design System Choice

**Selected System: shadcn/ui + Tailwind CSS**

Dream Central Storage will use **shadcn/ui** as the component library foundation, built on **Tailwind CSS** for utility-first styling. This represents a modern, themeable approach that balances development speed with visual customization.

**System Characteristics:**
- **Component Library:** shadcn/ui (copy-paste, customizable components)
- **Styling Foundation:** Tailwind CSS (utility-first CSS framework)
- **Component Architecture:** Radix UI primitives (accessible, unstyled foundation)
- **Type Safety:** TypeScript-first with full type definitions
- **Accessibility:** WCAG 2.1 Level AA compliance built-in

## Rationale for Selection

**1. Architectural Alignment**

The architecture document selected shadcn/ui as part of the FastAPI Full Stack Template evaluation. This choice aligns with:
- **React 18+** frontend framework (shadcn/ui is React-native)
- **TypeScript** strict mode (shadcn/ui provides full type safety)
- **Vite** build tooling (optimized for modern frameworks)
- **Modern development practices** (composition over configuration)

**2. Customization Without Constraints**

Unlike traditional component libraries (Material UI, Ant Design), shadcn/ui uses a **copy-paste model**:
- Components are copied into your codebase, not installed as dependencies
- Full ownership of component code enables deep customization
- No version lock-in or upgrade conflicts
- Modify components to match exact brand requirements

**Benefit for DCS:** Publishers, teachers, and students see interfaces tailored to their role without fighting framework constraints.

**3. Invisible Infrastructure Design Philosophy**

shadcn/ui's minimal, unstyled approach aligns perfectly with DCS's "invisible infrastructure" principle:
- Clean, functional aesthetics that don't draw attention
- Subtle interactions that feel "right" without being memorable
- Focus on content (files, videos, materials) rather than UI chrome
- Avoids opinionated design language (Material's bold colors, Ant's business aesthetic)

**4. Accessibility by Default**

Built on Radix UI primitives, shadcn/ui provides:
- WCAG 2.1 Level AA compliance out of the box
- Keyboard navigation for all interactive elements
- Screen reader support with proper ARIA attributes
- Focus management and visual indicators

**Benefit for DCS:** EdTech compliance requirements (educational institutions need accessibility) met by default.

**5. Performance and Bundle Size**

Tailwind CSS + shadcn/ui optimization benefits:
- **Tree-shaking:** Only CSS classes actually used are included in production build
- **No runtime:** Tailwind generates static CSS at build time
- **Component flexibility:** Import only components needed, no monolithic library bundle
- **Fast development:** Utility classes eliminate context-switching between HTML and CSS

**Benefit for DCS:** Fast load times support "instant playback" streaming experience and metadata query responsiveness.

**6. Developer Experience for Integration Teams**

For Deniz (developer persona) integrating DCS into consuming applications:
- Familiar patterns if team already uses React + Tailwind
- Well-documented components with clear examples
- Active community and extensive third-party resources
- Easy to extend with custom components following same patterns

**7. Role-Specific Interface Support**

shadcn/ui's composition model enables role-based UI implementation:
- **Publisher Dashboard:** Data-dense tables, bulk operation controls, analytics charts
- **Teacher View:** Card-based material browsing, drag-and-drop assignment creation
- **Student View:** Simple list-based file access, minimal navigation
- **Admin Panel:** System monitoring, user management, configuration forms

Same components, different compositions - aligns with "role-specific simplicity" principle.

## Implementation Approach

**Phase 1: Foundation Setup**

**1. Install Core Dependencies**
```bash
# Tailwind CSS + PostCSS + Autoprefixer
npm install -D tailwindcss postcss autoprefixer

# shadcn/ui CLI for component installation
npx shadcn-ui@latest init
```

**2. Configure Design Tokens**

Establish design tokens in `tailwind.config.js`:
```javascript
module.exports = {
  theme: {
    extend: {
      colors: {
        // DCS Brand Colors (to be defined)
        primary: {...},
        secondary: {...},

        // Semantic Colors
        success: {...},  // Upload complete, verification passed
        warning: {...},  // File approaching size limit
        error: {...},    // Upload failed, permission denied

        // Role-Based Colors
        publisher: {...},
        teacher: {...},
        student: {...},
      },

      // Trust-building feedback states
      animation: {
        'progress-pulse': '...',  // Upload progress indicator
        'checkmark': '...',       // Verification complete
      },
    },
  },
}
```

**3. Install Core Components**

Initial component set based on DCS requirements:
```bash
# Layout Components
npx shadcn-ui@latest add button card dialog sheet

# Form Components
npx shadcn-ui@latest add input select checkbox radio

# Data Display
npx shadcn-ui@latest add table badge avatar progress

# Feedback Components
npx shadcn-ui@latest add toast alert dropdown-menu

# Navigation
npx shadcn-ui@latest add tabs breadcrumb
```

**Phase 2: Custom Component Development**

**DCS-Specific Components** (built on shadcn/ui foundation):

**1. FileUploadZone**
- Drag-and-drop area with visual feedback
- Progress indicator with checksum verification
- File type and size validation feedback
- Support for single file + bulk ZIP upload

**2. AssetLibraryTable**
- Metadata-rich file listing (name, size, type, date, owner)
- Bulk selection and batch operations
- Inline preview for images/videos
- Sort and filter capabilities

**3. StreamingVideoPlayer**
- YouTube-style minimal video player
- HTTP Range support (invisible to user)
- Seek anywhere instantly, no rebuffering
- Hover-to-show controls

**4. RoleDashboard**
- Adaptive layout based on user role
- Publisher: Content library view with analytics
- Teacher: Material browser with assignment tools
- Student: Simple file list with assigned materials

**5. TrashManager**
- Deleted file browser with preview
- Restore confirmation with destination preview
- Retention period indicator
- Batch restore capabilities

**6. VersionHistory**
- Timeline view of file versions
- Diff preview (for supported file types)
- One-click rollback to previous version
- Version metadata (date, user, size)

## Customization Strategy

**1. Brand Alignment**

**Color Palette:**
- Define DCS brand colors aligned with "trust, calm, confidence" emotional goals
- Avoid bright, attention-grabbing colors (conflicts with invisible infrastructure)
- Use subtle blues/greens for success states (calm, reliable)
- Reserve red only for critical errors requiring immediate action

**Typography:**
- System font stack for performance (no custom web fonts initially)
- Clear hierarchy: headlines, body, metadata, code
- Readable sizes for accessibility (minimum 16px body text)

**2. Component Theming**

**Confidence-Building Elements:**
- Progress bars show detailed state (files uploaded, size transferred, time remaining)
- Checksum verification badges appear after successful upload
- Version indicators on all file cards
- "Last verified" timestamps for critical files

**Calm Interactions:**
- Smooth, predictable transitions (300ms standard easing)
- Soft shadows and borders (avoid harsh contrasts)
- Hover states that feel responsive but not jarring
- Loading states that indicate progress (no ambiguous spinners)

**Role-Specific Customization:**
- Color-coded role badges (subtle, not overwhelming)
- Publisher dashboard uses data-dense tables
- Teacher view uses card-based layouts for visual scanning
- Student view uses simplified list layouts

**3. Accessibility Enhancements**

**Beyond Default Compliance:**
- High contrast mode support for visually impaired users
- Keyboard shortcut system for power users (teachers managing many files)
- Screen reader announcements for upload progress and completion
- Focus indicators that are visible but not distracting

**4. Performance Optimization**

**Tailwind Production Build:**
- PurgeCSS configuration to remove unused utility classes
- Target: <50KB CSS bundle size (critical for fast load times)
- Component lazy loading for role-specific dashboards

**Component Optimization:**
- Virtualized lists for publishers managing 1000+ assets
- Lazy image loading with placeholder blur
- Video player lazy-loads until user initiates playback

**5. Responsive Design Strategy**

**Desktop-First (Primary Platform):**
- Optimized for desktop/laptop use (primary use case per architecture)
- Responsive down to tablet (secondary platform)
- Mobile: Read-only views only (not primary use case)

**Breakpoints:**
- Desktop: 1280px+ (primary)
- Tablet: 768px-1279px (responsive support)
- Mobile: <768px (view-only, simplified)

**6. Dark Mode Consideration**

**Future Enhancement:**
- Architecture supports Tailwind dark mode utilities
- Not implemented in V1.0 (focus on stability over features)
- Foundation prepared for future dark mode toggle
