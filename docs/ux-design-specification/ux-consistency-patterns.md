# UX Consistency Patterns

## Feedback Patterns

**Success Feedback:**
- Visual: Green checkmark icon + green text + optional green border
- Tone: Calm, confirmative (not celebratory)
- Duration: Toast notifications auto-dismiss after 4 seconds
- Position: Top-right corner
- Examples: "3 files uploaded successfully" (Toast, 4 sec) • "API key created • Copy it now, won't show again" (Persistent alert)

**Error Feedback:**
- Visual: Red X icon + red text + red border
- Tone: Specific, actionable (never generic "Error")
- Duration: Persistent until dismissed
- Recovery: Always provide next step (Retry, Contact support, Check connection)
- Examples: "video.mp4 upload failed: File exceeds 5GB limit • Try compressing the video" (Persistent toast with Dismiss)

**Warning Feedback:**
- Visual: Amber triangle icon + amber text + amber border
- Tone: Informative, not alarming
- Duration: Persistent for important warnings, 6 seconds for minor
- Examples: "12 students have already accessed v1 • Creating v2 may confuse them" (Confirmation required)

**Info Feedback:**
- Visual: Blue info icon + blue text + blue border
- Tone: Neutral, educational
- Duration: 5 seconds for tips, persistent for onboarding
- Examples: "Tip: Drag files directly to this page for faster uploads" (Toast, 5 sec)

**Accessibility:** All feedback uses role="alert", color never sole indicator (icon + text), screen readers announce automatically

## Button Hierarchy

**Primary Actions:**
- Style: Solid blue background (bg-blue-500), white text, 2px rounded corners
- Usage: Main action user came to perform (Upload, Save, Assign, Generate API Key)
- Limit: Maximum one primary button per screen section
- Examples: "Upload Files", "Generate Presigned URL", "Assign to Students"

**Secondary Actions:**
- Style: Transparent background, blue border (border-blue-500), blue text
- Usage: Alternative or supporting actions (Cancel, Preview, Edit)
- Limit: 2-3 secondary buttons per section acceptable
- Examples: "Preview", "Cancel", "Edit Metadata"

**Tertiary Actions:**
- Style: Text-only button, blue text, no border, no background
- Usage: Low-priority actions, navigation links (View Details, Learn More)
- Examples: "Learn about presigned URLs", "View version history"

**Destructive Actions:**
- Style: Red background (bg-red-600), white text OR red outline with red text
- Usage: Irreversible actions (Delete, Revoke Access, Permanently Remove)
- Confirmation: Always require confirmation dialog
- Examples: "Delete 3 Files", "Revoke API Key", "Empty Trash"

**Icon Buttons:**
- Style: Icon only, no text, 44x44px minimum (touch target)
- Tooltip: Always show label on hover
- Examples: Play button (video card), Download button (asset row), Three-dot menu

**Button Placement:** Primary right-most, Cancel left of primary, Destructive left-most
**Accessibility:** All buttons keyboard accessible, 2px focus indicators, aria-label on icon buttons

## Loading & Empty States

**Short Operations (<3 seconds):**
- Visual: Spinner icon only, subtle animation
- Text: None (context already visible)
- Usage: Form submissions, quick API calls, thumbnail loads

**Medium Operations (3-30 seconds):**
- Visual: Spinner + descriptive text
- Text: "Uploading files...", "Loading assets..."
- Progress: Show percentage if calculable ("Uploading... 47%")

**Long Operations (>30 seconds):**
- Visual: Progress bar with percentage
- Text: Detailed status with time estimate
- Example: "Uploading 847 files... 234 complete • About 3 minutes remaining"
- Cancellation: Provide "Cancel" button

**Skeleton Loading:**
- Visual: Gray placeholder blocks matching content layout (shimmer animation)
- Usage: Asset grids, tables, documentation pages
- Benefit: Perceived performance improvement (no layout shift)

**First-Time Empty (Onboarding):**
- Visual: Illustration + headline + description + primary CTA
- Example: "No files yet • Upload your first file to get started • Drag files here or click Upload"

**No Results (Search/Filter):**
- Visual: Magnifying glass icon + headline + suggestion
- Example: "No videos found • Try different filters or search terms"
- CTA: "Clear Filters" or "Search All Assets"

**Permanent Empty (No Access):**
- Visual: Lock icon + headline + explanation
- Example: "No content assigned • Your teacher hasn't assigned materials yet"

**Accessibility:** Loading states use aria-live="polite", skeleton loaders include aria-label="Loading content"

## Form Patterns

**Form Layout:**
- Label Position: Above input field (better for mobile)
- Required Indicators: Red asterisk (*) after label text
- Help Text: Gray text below input with examples/constraints
- Spacing: 24px between form fields

**Input States:**
- Default: Gray border (border-gray-300), black text, white background
- Focus: Blue border (border-blue-500), 2px blue outline
- Error: Red border (border-red-500), red text below with error message, red X icon
- Success: Green checkmark icon (only for critical validations)
- Disabled: Gray background (bg-gray-100), 50% opacity, tooltip explains why

**Validation Timing:**
- On Blur: Validate field after user leaves it
- On Submit: Validate all fields, show inline errors, focus first error
- Real-Time: Only for username availability, character counts (non-critical)

**Error Messages:**
- Tone: Specific, actionable, no jargon
- Format: "Field name: Error description • Suggested fix"
- Examples:
  - "Email: Must be valid email format • Example: name@example.com"
  - "File: Exceeds 5GB limit • Try compressing or splitting the file"
  - "API Key: Invalid format • Keys start with 'dcs_' and are 32 characters"

**Form Actions:**
- Submit Button: Primary button, right-aligned, disabled until required fields filled
- Cancel Button: Secondary button, left of submit, always enabled
- Destructive Forms: Submit button red if action is destructive

**Accessibility:** Labels use `<label for>`, error messages via aria-describedby, required fields marked aria-required="true"

## Navigation Patterns

**Desktop Navigation (>1024px):**
- Layout: Left sidebar (240px) + main content area
- Sidebar: Persistent, collapsible to icons-only (64px)
- Current Page: Blue background, bold text, left border accent

**Tablet (768-1023px):**
- Layout: Collapsed sidebar (icons-only) by default
- Expansion: Sidebar expands on hover or tap, overlays content

**Mobile (<768px):**
- Layout: Top bar + hamburger menu
- Menu: Full-screen overlay when opened

**Role-Specific Navigation:**
- Developer: API Docs, API Keys, Testing, Usage, Support (5 items)
- Publisher: Library, Upload, Versions, Access Control, Analytics, Settings (6 items)
- Teacher: My Content, Assignments, Students, Browse, Settings (5 items)
- Student: My Assignments, Completed Work, Help (3 items)

**Navigation Behavior:**
- Current Page: Blue background + left border accent
- Hover: Light blue background (hover:bg-blue-50)
- Badges: Red notification counts on relevant items

**Breadcrumbs:** Used for multi-level pages (Publisher: Library > Folder > Asset Detail)

**Accessibility:** Navigation in `<nav>` landmark, current page marked aria-current="page", keyboard navigable

## Modal & Overlay Patterns

**Confirmation Dialogs (Destructive Actions):**
- Icon: Red warning triangle (centered)
- Title: "Delete 3 files?" (question format)
- Body: Specific details + "This action cannot be undone"
- Actions: "Cancel" (secondary, left, default focus) + "Delete Files" (destructive red, right)

**Form Dialogs (Create/Edit):**
- Title: "Assign Video to Students" (action format)
- Body: Form fields (class selector, due date, instructions)
- Actions: "Cancel" (secondary, left) + "Assign" (primary blue, right)
- Default Focus: First input field

**Information Dialogs (Read-Only):**
- Icon: Blue info icon
- Title: Descriptive (e.g., "About Presigned URLs")
- Body: Explanatory content, code examples
- Actions: "Close" or "Got It" (primary blue, centered)

**Full-Screen Overlays:**
- Usage: Video player, image viewer, asset preview
- Background: 95% opacity black
- Close: X button (top-right) OR Escape key

**Behavior Rules:**
- Single Modal: Only one modal visible at a time
- Body Scroll: Locked when modal open
- Restore Focus: Focus returns to trigger element on close

**Accessibility:** role="dialog", aria-modal="true", focus trapped, Escape closes, screen reader announces opening

## Search & Filtering Patterns

**Search Bar:**
- Position: Top-right of content area
- Size: 320px (desktop), full-width (mobile)
- Placeholder: "Search assets by name, type, or tag..."
- Behavior: Debounced search after 300ms of no typing
- Results: Show "127 results for 'video'" above results
- Clear: X button appears when text entered

**Filters:**

**Checkbox Filters (Multi-Select):**
- Usage: File types, tags, categories
- Behavior: Multiple selections allowed, OR logic
- Example: "[x] Video [x] PDF" → Shows PDFs OR Videos

**Radio Filters (Single-Select):**
- Usage: Sort order, date ranges, ownership
- Example: "(•) Newest (◦) Oldest (◦) Name A-Z"

**Range Filters:**
- Usage: File size, date ranges, duration
- Example: "Size: [Min: 0 MB] [Max: 500 MB]"

**Filter Behavior:**
- Application: Filters apply immediately (no Apply button)
- Active Filters: Blue badges above results "Type: Video (x)"
- Clear All: "Clear All Filters" button when filters active
- Count Indicators: "Video (234) PDF (89)"

**Combined Search + Filters:**
- Logic: Search AND filters (narrow results)
- Active State: Show search term + filter badges

**Accessibility:** Search has role="search", results count via aria-live, filters keyboard accessible
