# Component Strategy

## Design System Components

Dream Central Storage uses **shadcn/ui + Tailwind CSS** as the foundation design system (selected in Step 6). This provides 30+ production-ready components including Button, Input, Card, Dialog, Table, and more.

**Available Foundation Components:**
- Form controls: Button, Input, Textarea, Checkbox, Radio, Select, Switch
- Layout: Card, Dialog, Sheet, Popover, Tabs, Accordion, Separator
- Data display: Table, DataTable, Badge, Avatar, Progress, Skeleton
- Navigation: Dropdown Menu, Command Palette, Search
- Feedback: Toast, Alert

**Foundation Strengths:**
- Built on Radix UI primitives (accessibility by default)
- Fully customizable with Tailwind (no CSS conflicts)
- Copy-paste architecture (no npm dependencies, full control)
- TypeScript support with prop typing
- WCAG 2.1 Level AA compliant out of box

## Custom Components

Based on user journey analysis, 6 custom components needed to complete the Dream Central Storage experience:

### 1. Asset Upload Zone

**Purpose:** Drag-drop file upload with visual feedback and multi-file support
**Usage:** Developer API testing, Publisher bulk upload
**Key Features:**
- Drag-over highlighting with visual feedback
- Multi-file selection and preview
- Per-file progress tracking and error handling
- File type and size validation with clear error messages
- Cancel and retry capabilities per file

**States:** Default, Drag Over, Uploading (with progress), Complete, Error, Disabled
**Accessibility:** Keyboard file selection, ARIA live progress announcements, focus indicators
**Implementation:** Wraps native file input with custom drop zone using React dropzone patterns

### 2. Video Stream Player

**Purpose:** Stream videos with instant playback (<1 second) and smooth seeking
**Usage:** Teacher content preview, Student content viewing
**Key Features:**
- HTML5 video with custom controls styled to match design system
- Timeline scrubber with hover preview
- Keyboard shortcuts (Space, Arrow keys, F, M)
- Captions support (.vtt files)
- Fullscreen mode

**States:** Loading, Ready, Playing (controls auto-hide), Buffering, Error, Ended
**Accessibility:** Full keyboard control, ARIA labels, captions toggle, progress announcements
**Implementation:** HTML5 `<video>` element with custom React control components

### 3. Asset Card

**Purpose:** Display asset preview with metadata and quick actions
**Usage:** Teacher browsing, Publisher management
**Key Features:**
- Thumbnail preview (video poster, PDF page, file icon)
- Metadata display (type, size, date, version)
- Quick action buttons (Play, Download, Assign, Delete) on hover
- Selection checkbox for batch operations
- Context menu on right-click

**Variants:** Compact (small thumbnail), List (horizontal), Grid (square thumbnail)
**Accessibility:** Full keyboard navigation, clear focus indicators, descriptive ARIA labels
**Implementation:** Composes shadcn Card + Badge + Button with custom thumbnail logic

### 4. Multi-File Progress Tracker

**Purpose:** Real-time progress of bulk file operations (upload/download/delete)
**Usage:** Publisher bulk upload (847 files), batch operations
**Key Features:**
- Overall progress bar + percentage
- Scrollable list of individual file statuses
- Per-file progress, cancel, and retry
- Smart aggregation: "234 complete • 12 in progress • 601 queued"
- Time estimates for long operations

**Modes:** Compact (overall only), Full (individual list), Modal (overlay with minimize)
**Accessibility:** ARIA live regions announce progress milestones, keyboard retry/cancel
**Implementation:** shadcn Progress + ScrollArea with custom aggregation logic

### 5. Code Documentation Viewer

**Purpose:** Display API documentation with syntax-highlighted examples
**Usage:** Developer documentation pages
**Key Features:**
- Language tabs (Python, JavaScript, cURL, etc.)
- Syntax highlighting with theme matching design system
- One-click copy with success feedback
- Line numbers and line highlighting
- Horizontal scroll for long lines

**States:** Default, Copy Success (checkmark + tooltip), Wrap Enabled/Disabled
**Accessibility:** Code readable by screen readers line-by-line, keyboard copy, high contrast
**Implementation:** Prism.js or Shiki for highlighting + shadcn Button for copy

### 6. Asset Browser Table

**Purpose:** Data table for managing large asset libraries (1000+ files)
**Usage:** Publisher asset management dashboard
**Key Features:**
- Sortable columns (Name, Type, Size, Date, Version, Actions)
- Checkbox column for batch selection
- Inline action menus per row
- Pagination with "showing X of Y" indicator
- Search/filter bar above table
- Bulk action toolbar (appears when items selected)

**States:** Default, Row Hover, Row Selected, Sorting, Loading (skeleton), Empty
**Accessibility:** Full keyboard navigation with arrow keys, sort announcements, selection counts
**Implementation:** Extends shadcn DataTable with custom columns and batch selection logic

## Component Implementation Strategy

**Build Approach:**
- Compose custom components using shadcn/ui primitives where possible (Dialog, Popover, Button)
- Style exclusively with Tailwind CSS utility classes (no custom CSS files)
- Use design tokens from Visual Foundation (colors, spacing, typography)
- Implement with React + TypeScript with strict prop typing
- Follow shadcn copy-paste pattern (components live in project, not node_modules)

**Accessibility Standards:**
- All components WCAG 2.1 Level AA compliant minimum
- Keyboard navigation for every interaction
- Visible focus indicators (2px blue outline)
- ARIA labels, roles, and live regions where appropriate
- Color never sole indicator of state (always icon + text)
- Support for `prefers-reduced-motion` media query

**Performance Considerations:**
- Lazy load heavy components (Video Player, Code Viewer)
- Virtualize long lists in Asset Browser Table (React Virtuoso)
- Debounce real-time search inputs (300ms)
- Optimize thumbnail images (WebP format, responsive sizes)
- Tree-shake unused shadcn components with Vite

**Testing Strategy:**
- Unit tests for component logic (Vitest + React Testing Library)
- Accessibility audits with axe-devtools on all components
- Manual keyboard navigation testing on Chrome, Firefox, Safari
- Screen reader testing (VoiceOver on macOS, NVDA on Windows)
- Visual regression tests for all states (Chromatic or Percy)

## Implementation Roadmap

**Phase 1 - Critical Path Components (Sprint 1-2):**
1. **Asset Upload Zone** - Unblocks Developer API testing journey and Publisher bulk upload
2. **Video Stream Player** - Unblocks Teacher preview journey and Student viewing journey
3. **Asset Card** - Unblocks Teacher browsing interface (card grid layout)

**Why Phase 1:** These 3 components are required for all critical user journeys. Without them, the product cannot deliver core value to any persona.

**Phase 2 - Core Experience Components (Sprint 3-4):**
4. **Multi-File Progress Tracker** - Reduces anxiety for Publisher bulk uploads (visible progress)
5. **Asset Browser Table** - Publisher primary interface for managing 1000+ assets efficiently
6. **Code Documentation Viewer** - Developer documentation experience (API integration clarity)

**Why Phase 2:** These components are required for production-ready, professional experience. Product is functional without them (Phase 1 gets MVPs working), but UX feels incomplete.

**Phase 3 - Enhancement & Refinement (Sprint 5+):**
- Component variants based on user feedback (compact vs. detailed views)
- Advanced features (video timeline thumbnail previews, drag-to-reorder tables, etc.)
- Performance optimizations (virtualization, caching strategies)
- Accessibility improvements based on audit findings
- Responsive refinements for tablet breakpoints

**Why Phase 3:** These enhancements improve UX incrementally but product is fully functional and accessible without them. Implement based on user feedback and analytics.

**Prioritization Principles:**
- Functionality before polish (Phase 1 is functional, Phase 3 is polish)
- Accessibility non-negotiable (AA compliance in every phase)
- User journey criticality (components blocking journeys built first)
- Progressive enhancement (product works at each phase, gets better with each)
