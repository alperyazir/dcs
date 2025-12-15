# User Journey Flows

## Foundation: PRD User Journeys

The PRD provides three detailed user journey narratives that inform our flow design:

1. **Deniz (Integration Developer):** Evaluates and integrates DCS API into edtech applications
2. **Elif (Publisher Content Manager):** Manages thousands of digital assets for distribution to schools
3. **Ayşe (Primary School Teacher):** Accesses publisher materials and shares custom content with students

These journeys tell us **who** users are and **why** they take actions. This section designs **how** those journeys work through detailed interaction flows.

## Journey 1: Developer API Integration (Deniz)

**Journey Goal:** Integrate DCS storage APIs into a new edtech application within hours

**Entry Points:**
- Marketing website → "Get Started" → API Documentation
- Direct search: "DCS API docs" → Documentation homepage
- Referral: Colleague recommendation → Quick Start guide

**Detailed Flow:**

**Step 1: Discovery & Evaluation (5-10 minutes)**
- **Entry:** Lands on API documentation homepage
- **Information Needed:** What DCS does, pricing, technical requirements
- **Key Decision:** "Can this solve my storage problem?"
- **UI Elements:** Hero section with value proposition, Quick Start button prominent, example code visible
- **Success Criterion:** Developer understands DCS capabilities and decides to try integration

**Step 2: Authentication Setup (10-15 minutes)**
- **Trigger:** Clicks "Quick Start" button
- **Actions:**
  1. Reads authentication overview (JWT-based)
  2. Generates API key from admin panel
  3. Copies example authentication code
  4. Tests authentication with curl command
- **Information Needed:** How to get API key, authentication format, test endpoint
- **UI Elements:** Step-by-step authentication guide, "Copy Code" buttons, test endpoint to verify auth
- **Success Criterion:** Authentication returns 200 OK with valid JWT token
- **Error Handling:** Invalid key shows specific error: "Authentication failed: Invalid API key format. Ensure you copied the complete key."

**Step 3: First Upload Test (15-20 minutes)**
- **Trigger:** Authentication successful
- **Actions:**
  1. Copies file upload example code (Python/JavaScript)
  2. Modifies with actual file path
  3. Runs code, uploads test PDF
  4. Receives asset_id and presigned download URL
  5. Tests download URL in browser
- **Information Needed:** Upload endpoint, request format, response structure
- **UI Elements:** Code examples in multiple languages, interactive API explorer (optional), response schema documentation
- **Success Criterion:** File uploads successfully, presigned URL downloads file
- **Error Handling:** File too large shows: "Upload failed: File exceeds 10GB limit (12.4GB provided). Try compressing or splitting the file. [Learn more]"

**Step 4: Streaming Implementation (20-30 minutes)**
- **Trigger:** Basic upload working, needs video streaming
- **Actions:**
  1. Reads streaming documentation (HTTP Range support)
  2. Implements video player with presigned URL
  3. Tests seeking to middle of video (Range request)
  4. Verifies no rebuffering
- **Information Needed:** How presigned URLs work, HTTP Range support, CORS configuration
- **UI Elements:** Streaming guide with video player example, troubleshooting section for common issues
- **Success Criterion:** Video streams smoothly with instant seeking
- **Error Handling:** CORS error shows: "CORS blocked: Add your domain to allowed origins in DCS admin panel. [Configuration Guide]"

**Step 5: Production Integration (1-2 hours)**
- **Trigger:** Tests successful, ready for production code
- **Actions:**
  1. Implements multipart upload for large files
  2. Adds progress tracking
  3. Implements error handling and retry logic
  4. Deploys to production environment
- **Information Needed:** Multipart upload endpoint, progress tracking, production best practices
- **UI Elements:** Advanced integration guide, best practices checklist, production readiness guide
- **Success Criterion:** Production app successfully uploads, streams, and downloads files
- **Completion Indicator:** Developer marks integration complete, app in production

**Journey Exit Points:**
- **Success:** Integration complete in < 4 hours, app uses DCS in production
- **Partial Success:** Integration working but needs additional features (versioning, bulk operations)
- **Abandonment:** Too complex, poor documentation, technical blockers

## Journey 2: Publisher Bulk Upload (Elif)

**Journey Goal:** Upload 847 files (3.2GB) for distribution to 80 schools

**Entry Points:**
- Admin panel login → Publisher Dashboard → Content Library
- Email notification: "Your account is ready" → Login → Dashboard
- Existing publisher returning: Direct bookmark to /publisher/library

**Detailed Flow:**

**Step 1: Access Content Library (1-2 minutes)**
- **Entry:** Logs in with publisher credentials
- **Actions:**
  1. Views dashboard showing current library stats (files, size, schools served)
  2. Navigates to "Content Library" section
  3. Sees existing files organized by folder structure
- **Information Needed:** Current library state, available storage quota, recent uploads
- **UI Elements:** Dashboard cards showing stats, sidebar navigation, library table view
- **Success Criterion:** Publisher sees organized library, understands current state

**Step 2: Prepare Bulk Upload (5 minutes)**
- **Trigger:** Clicks "Upload" button with dropdown
- **Actions:**
  1. Selects "Upload ZIP Archive" option (vs. single file)
  2. Reads tooltip: "Upload ZIP to extract multiple files automatically"
  3. Drags ZIP file (3.2GB, 847 files) to drop zone
  4. Drop zone highlights blue, shows file name and size
- **Information Needed:** ZIP upload supported, size limits, what happens during extraction
- **UI Elements:** Upload dropdown menu, drag-drop zone with visual feedback, file size/count display
- **Success Criterion:** ZIP file selected, ready to upload
- **Error Handling:** If ZIP > 5GB: "Large ZIP detected (6.2GB). Upload will take approximately 8 minutes. Continue?"

**Step 3: Monitor Upload Progress (5-8 minutes)**
- **Trigger:** Confirms upload
- **Actions:**
  1. Watches progress bar: "Uploading: 24% • 780MB / 3.2GB • 3.1 MB/s • 7 minutes remaining"
  2. Sees transition to extraction: "Extracting: 0 of 847 files"
  3. Watches file count increment in real-time
  4. Sees files appearing in library table as they extract
- **Information Needed:** Upload speed, time remaining, extraction progress, which file currently processing
- **UI Elements:** Progress modal with detailed stats, currently processing file name visible, background option
- **Success Criterion:** All 847 files extract successfully
- **Error Handling:** Extraction fails on corrupt file: "File 'chapter03/image.png' corrupted. Skipped. Continuing extraction (842/847 files successful)."

**Step 4: Verify Upload & Organize (2-3 minutes)**
- **Trigger:** Extraction completes
- **Actions:**
  1. Sees success message: "Successfully uploaded 847 files (3.2 GB)" with checksum verified badge
  2. Clicks "View Uploaded Files" button
  3. Navigates to folder containing extracted files
  4. Verifies file organization matches ZIP structure
  5. Checks random file thumbnails/metadata for accuracy
- **Information Needed:** Upload summary, where files are located, verification status
- **UI Elements:** Success toast, navigation button to uploaded files, folder tree view, checksum badges
- **Success Criterion:** All files verified, organized correctly, ready for distribution

**Step 5: Distribute to Schools (3-5 minutes)**
- **Trigger:** Files verified
- **Actions:**
  1. Selects all 847 files (bulk select checkbox)
  2. Clicks "Assign to Schools" button
  3. Selects schools from list (80 schools)
  4. Confirms distribution: "Assign 847 files to 80 schools?"
  5. Receives confirmation: "Files assigned. Teachers will see materials in their LMS."
- **Information Needed:** Which schools, assignment confirmation, what teachers see
- **UI Elements:** Bulk selection checkboxes, school picker (search + select), confirmation dialog
- **Success Criterion:** Files assigned, schools/teachers can access
- **Completion Indicator:** "847 files distributed to 80 schools • Teachers notified via LMS"

**Journey Exit Points:**
- **Success:** All files uploaded, verified, distributed to schools
- **Partial Success:** Most files uploaded but some corrupted/skipped
- **Abandonment:** Upload timeout, quota exceeded, network failure

## Journey 3: Teacher Video Streaming (Ayşe)

**Journey Goal:** Preview and assign video lesson to students for tomorrow's class

**Entry Points:**
- LMS assignment creation → "Add Material" → DCS material browser
- Direct link from publisher email: "New materials available"
- Teacher dashboard → "Assigned Materials" → Browse

**Detailed Flow:**

**Step 1: Browse Assigned Materials (1-2 minutes)**
- **Entry:** Opens material browser from LMS
- **Actions:**
  1. Views "Assigned Materials" section (publisher content)
  2. Sees card grid with thumbnails for textbooks, videos, quizzes
  3. Filters by subject: "Math" and type: "Video"
  4. Finds "Lesson 3: Linear Equations" video
- **Information Needed:** What materials are assigned to me, how to filter, video metadata
- **UI Elements:** Card grid with thumbnails, filter sidebar (subject, type, grade), search box
- **Success Criterion:** Teacher locates the video lesson needed

**Step 2: Preview Video (2-3 minutes)**
- **Trigger:** Clicks video card thumbnail or "Play" icon
- **Actions:**
  1. Video player modal opens full-screen
  2. Video starts playing within 1 second
  3. Teacher watches first minute to verify content
  4. Seeks to middle (6:00 / 12:18) to check specific section
  5. Pauses, sees file metadata: "Video • 340MB • Uploaded 2 days ago"
- **Information Needed:** Video content (is this the right lesson?), video quality, length
- **UI Elements:** Full-screen video player modal, YouTube-style controls, metadata below player
- **Success Criterion:** Video streams smoothly, seeking works instantly, content verified
- **Error Handling:** Video fails to load: "Video unavailable. Contact your school admin or try again later. Error code: VIDEO_NOT_FOUND"

**Step 3: Assign to Students (1-2 minutes)**
- **Trigger:** Video verified, ready to assign
- **Actions:**
  1. Clicks "Assign to Students" button in video player
  2. Selects class: "Grade 8 Math - Period 3"
  3. Sets due date: "Tomorrow" (auto-fills next school day)
  4. Adds optional instructions: "Watch before tomorrow's quiz"
  5. Clicks "Assign"
- **Information Needed:** Which class, when is it due, can I add instructions
- **UI Elements:** Assignment dialog with class picker, date picker (defaults to next day), instructions text area
- **Success Criterion:** Assignment created
- **Completion Indicator:** "Video assigned to Grade 8 Math (24 students) • Due tomorrow"

**Step 4: Verify Student Access (Optional, 1 minute)**
- **Trigger:** Wants to confirm students can see assignment
- **Actions:**
  1. Switches to student view preview (if LMS supports)
  2. Sees assignment appears in "Upcoming" section
  3. Verifies video link works from student perspective
  4. Returns to teacher view
- **Information Needed:** What do students see, is video accessible
- **UI Elements:** "Preview as Student" toggle (LMS feature, not DCS), student view UI
- **Success Criterion:** Video appears in student assignments, plays correctly
- **Completion Indicator:** Teacher confident students can access video

**Journey Exit Points:**
- **Success:** Video assigned to students, accessible tomorrow
- **Partial Success:** Video assigned but teacher unsure if students can access
- **Abandonment:** Video won't play, technical issues, content not what teacher expected

## Cross-Journey Patterns

**Common Success Patterns:**
1. **Fast Time to First Success:** Deniz uploads file in 20 min, Elif uploads 847 files in <10 min, Ayşe previews video in <1 second
2. **Visible Progress:** All journeys show real-time progress (API response time, upload %, video playback)
3. **Clear Completion:** All journeys have unambiguous success indicators (200 OK + presigned URL, checksum badges, "Assigned to 24 students")
4. **Minimal Steps:** No journey requires more than 5 major steps to complete core goal

**Common Failure Patterns:**
1. **Ambiguous Errors:** Generic "Error" messages destroy trust - all errors must be specific and actionable
2. **Missing Progress Indicators:** Unknown state creates anxiety - always show what's happening
3. **Unexpected Delays:** No indication of time remaining frustrates users - always estimate duration
4. **Dead Ends:** Failure with no recovery path causes abandonment - every error has a next step

**Design Principles Validated by Journeys:**
- **Invisible Infrastructure:** DCS never becomes the focus - users focus on their actual goal (integrate app, distribute content, teach lesson)
- **Role-Specific Simplicity:** Developer sees technical documentation, publisher sees data-dense tables, teacher sees visual cards, student sees simple list
- **Progressive Disclosure:** All journeys start simple (one file, one video) and reveal complexity only when needed (multipart upload, bulk distribution)
