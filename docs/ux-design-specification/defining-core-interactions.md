# Defining Core Interactions

## Defining Experience

**The Paradox of Infrastructure UX:**

Dream Central Storage's defining experience is fundamentally different from consumer products. While Tinder's defining experience is "swipe to match" and Spotify's is "play any song instantly," DCS's defining experience is:

**"File operations that always work, never slow you down, and become invisible through reliability."**

This manifests differently for each persona:

**For Publishers (Elif - Content Manager):**
- **Defining Moment:** Drag 3.2GB ZIP with 847 files → watch smooth extraction progress → see organized library appear
- **User Description:** "I can upload thousands of files at once and it just handles it"
- **Success Feeling:** Confidence in managing scale without manual intervention

**For Teachers (Ayşe - Educator):**
- **Defining Moment:** Click video lesson link in LMS → video plays within 1 second → seek to any point without buffering
- **User Description:** "Videos just play like YouTube - I never worry about streaming problems during class"
- **Success Feeling:** Calm trust that materials will be accessible when needed

**For Developers (Deniz - Integration Engineer):**
- **Defining Moment:** Make first API call → auth works → presigned URL returns → file downloads successfully
- **User Description:** "The API docs were clear, authentication worked first try, and it's been rock-solid since"
- **Success Feeling:** Relief that storage won't be source of bugs in their application

**For Students:**
- **Defining Moment:** Open assignment in LMS → materials appear instantly → stream or download without issues
- **User Description:** "I just click and my stuff is there"
- **Success Feeling:** System is invisible - no conscious thought about storage

**The Meta Defining Experience:**

Across all personas, the unifying core interaction is: **"Operations complete successfully without requiring user attention or intervention."**

This is measured by:
- Upload success rate: 99.9%+
- Streaming works like YouTube (instant playback, no buffering)
- API calls return predictable results
- System never appears in bug trackers or support tickets

## User Mental Model

**Current Solutions and Expectations:**

**Publishers (Content Managers):**
- **Current Mental Model:** Google Drive folders + Dropbox sharing + manual email distribution
- **Pain Points:** Version chaos ("which file did I send to which school?"), no bulk operations, manual permission management
- **Expectations:** "Should work like AWS S3 but without the technical complexity"
- **Confusion Risk:** Cross-tenant permissions (how do schools access my content?)

**Teachers (Educators):**
- **Current Mental Model:** "Download from Google Drive link, manually organize on computer, upload to LMS"
- **Pain Points:** Broken links, outdated versions, can't tell if content is current
- **Expectations:** "Should work like Google Classroom - materials assigned to me just appear"
- **Confusion Risk:** Difference between "my materials" vs. "publisher materials assigned to me"

**Developers (Integration Teams):**
- **Current Mental Model:** AWS S3 API patterns, REST conventions, signed URL paradigm
- **Pain Points:** Custom storage solutions require building auth, streaming, versioning from scratch
- **Expectations:** "Should be S3-compatible with FastAPI conventions"
- **Confusion Risk:** Multi-tenant isolation model (how permissions work across tenants)

**Students:**
- **Current Mental Model:** "Click link teacher sent, hope it works"
- **Pain Points:** Permission errors, broken links, confusing interfaces
- **Expectations:** "Should work like downloading files from any website - just click and it opens"
- **Confusion Risk:** Any complexity beyond "click → content appears"

**Established Patterns DCS Leverages:**
- **Drag-and-drop upload** (Dropbox mental model) - universally understood
- **Video streaming** (YouTube mental model) - click and play, seek anywhere
- **Folder organization** (File system mental model) - hierarchical structure
- **Trash/restore** (Desktop OS mental model) - deleted items recoverable from trash

**Workarounds to Eliminate:**
- Publishers manually emailing files to schools
- Teachers downloading from Google Drive, then re-uploading to LMS
- Developers building custom storage solutions for each app
- Students dealing with broken permission links

## Success Criteria

**What Makes Users Say "This Just Works":**

**For Publishers:**
- **Success Indicator 1:** Upload 1000+ files without timeout or failure
- **Success Indicator 2:** See real-time progress with file count and size transferred
- **Success Indicator 3:** Files appear organized exactly as expected after extraction
- **Success Indicator 4:** Schools can access assigned content immediately without publisher intervention
- **Feeling:** "I can manage 80 schools worth of content and never manually email files"

**For Teachers:**
- **Success Indicator 1:** Video streams within 1 second of clicking play
- **Success Indicator 2:** Seeking to any point in video works instantly
- **Success Indicator 3:** Assigned publisher materials appear in "my materials" automatically
- **Success Indicator 4:** Upload custom teaching materials with drag-and-drop
- **Feeling:** "Storage never interrupts my teaching - materials just work"

**For Developers:**
- **Success Indicator 1:** First API integration completed in hours, not days
- **Success Indicator 2:** Error messages are specific and actionable with documentation links
- **Success Indicator 3:** Authentication works first try with JWT token
- **Success Indicator 4:** Presigned URLs enable direct client downloads without proxy
- **Feeling:** "I built three apps on this API and it's never been a problem"

**For Students:**
- **Success Indicator 1:** Click assigned material → it opens/streams immediately
- **Success Indicator 2:** No permission errors or "access denied" messages
- **Success Indicator 3:** Upload homework submission with simple drag-and-drop
- **Success Indicator 4:** Never need to contact teacher or help desk about accessing files
- **Feeling:** "I just click and my stuff is there - I don't think about it"

**Speed Requirements:**
- Metadata operations: P95 response time under 500ms (NFR-P1)
- Signed URL generation: Under 100ms (NFR-P2)
- Video streaming: Playback starts within 1 second
- Upload feedback: Progress indicator appears immediately on file selection

**Automatic Operations:**
- Checksum verification happens without user initiating
- Version incrementing on file update (no manual "save as v2")
- Trash retention policy enforcement (automated permanent deletion after retention period)
- Permission enforcement based on JWT claims (no manual permission configuration)

## Novel vs. Established Patterns

**Established Patterns (Leverage User Familiarity):**

**1. Drag-and-Drop Upload (Dropbox Pattern)**
- **Why Established:** Users understand "drag file to browser = upload"
- **DCS Implementation:** All upload interfaces use drag-and-drop as primary interaction
- **Unique Twist:** Support both single files AND bulk ZIP extraction in same interface

**2. Folder Hierarchy (File System Pattern)**
- **Why Established:** Decades of desktop OS training (folders → subfolders → files)
- **DCS Implementation:** Publishers organize content with familiar folder structure
- **Unique Twist:** Hide technical concepts (no "buckets"), just "Your Library" → folders

**3. Video Streaming (YouTube Pattern)**
- **Why Established:** Users expect click → instant playback, seek anywhere
- **DCS Implementation:** Video player matches YouTube simplicity and responsiveness
- **Unique Twist:** Presigned URLs + HTTP Range support completely invisible to user

**4. Trash/Restore (Desktop OS Pattern)**
- **Why Established:** Users understand "deleted → moves to trash → restore or permanent delete"
- **DCS Implementation:** Soft delete to trash with configurable retention period
- **Unique Twist:** Preview file content before restoring (reduce anxiety)

**Novel Patterns (Require User Education):**

**1. Cross-Tenant Read Access (Unique to DCS Multi-Tenant Model)**
- **What's Novel:** Teachers see publisher content, but permissions are managed by LMS, not DCS
- **Why Novel:** Most file systems have explicit "share" actions; DCS permissions are granted by consuming application
- **Education Strategy:**
  - Clear visual distinction: "Your Files" vs. "Assigned Materials"
  - Tooltips explain: "Publisher assigned this content to you via LMS"
  - No technical jargon about cross-tenant access or permission grants

**2. Zero-Proxy Streaming (Presigned URLs)**
- **What's Novel:** File doesn't stream through API server, goes directly from MinIO to client
- **Why Novel:** Most platforms proxy files through backend (users see "loading from server")
- **Education Strategy:**
  - Don't educate - make it invisible! Users don't need to know about presigned URLs
  - They just experience: click video → instant playback
  - Developer docs explain technical architecture; end users never see it

**3. Streaming ZIP Extraction**
- **What's Novel:** Large ZIP files extract without downloading entire file to server RAM/disk first
- **Why Novel:** Most systems download full ZIP, then extract (causes timeouts on large files)
- **Education Strategy:**
  - Progress bar shows "Extracting file X of Y" with running file count
  - No technical explanation of streaming vs. buffering
  - Users just experience: upload giant ZIP → see files appearing in real-time

**Pattern Decision Framework:**
- **Use established patterns** for all primary interactions (upload, browse, play, delete)
- **Innovate invisibly** on technical implementation (streaming ZIP, presigned URLs)
- **Educate gently** when novel patterns affect user behavior (cross-tenant access)

## Experience Mechanics

**Core Experience 1: Bulk Upload (Publisher Defining Moment)**

**1. Initiation:**
- **Trigger:** Publisher clicks "Upload" button or drags file over browser window
- **Visual Invitation:** Drop zone highlights with blue border and "Drop files or ZIP archives here" message
- **Entry Points:** Upload button in toolbar, drag-and-drop anywhere in library view

**2. Interaction:**
- **User Action:** Drops 3.2GB ZIP file containing 847 files
- **System Response - Immediate:** Progress modal appears showing "Uploading archive: 0% complete"
- **System Response - During:** Progress bar updates with:
  - Percentage complete (0% → 100%)
  - Upload speed (e.g., "3.2 MB/s")
  - Time remaining estimate ("About 5 minutes remaining")
- **System Response - After Upload:** Transition to extraction phase:
  - "Extracting files: 0 of 847 files processed"
  - Real-time file count increment ("1 of 847", "2 of 847", etc.)
  - No "frozen" state - always shows progress

**3. Feedback:**
- **Success Indicators:**
  - Checksum verification badge appears: "Upload verified ✓"
  - Files appear in library as they're extracted (real-time population)
  - Final success message: "Successfully uploaded 847 files (3.2 GB)"
- **In-Progress Indicators:**
  - Progress bar with smooth animation (not jerky)
  - File count incrementing (shows system is working)
  - Estimated time remaining (manages expectations)
- **Error Handling:**
  - Specific errors: "Failed to extract file X: unsupported format"
  - Allow continuation: "Skipping unsupported files, continuing extraction"
  - Summary at end: "842 files uploaded successfully, 5 files skipped (details below)"

**4. Completion:**
- **Success Outcome:** Library view now shows all 842 uploaded files organized by folder structure from ZIP
- **Completion Indicator:** Success toast notification (dismissible) + final count in upload modal
- **What's Next:** "View uploaded files" button navigates to folder containing new files
- **Confidence Signal:** Each file shows checksum verification badge

**Core Experience 2: Video Streaming (Teacher Defining Moment)**

**1. Initiation:**
- **Trigger:** Teacher clicks video thumbnail or "Play" icon in material browser
- **Entry Points:** Material library card view, assignment creation modal, preview mode
- **Invitation:** Video thumbnail with play icon overlay (YouTube pattern)

**2. Interaction:**
- **User Action:** Single click on video thumbnail
- **System Response - Immediate:** Video player modal opens, playback starts within 1 second
- **System Response - During:**
  - Video plays smoothly with standard controls (play/pause, seek, volume, fullscreen)
  - Seek bar allows clicking anywhere to jump (HTTP Range support invisible)
  - Quality adjusts automatically based on connection (no user intervention)
- **Controls:** Minimal UI - controls appear on hover, fade during playback

**3. Feedback:**
- **Success Indicators:**
  - Video plays immediately (no "loading..." state longer than 1 second)
  - Seeking to any point works instantly (no rebuffering)
  - Buffer indicator only appears if network issue (rare)
- **In-Progress Indicators:**
  - Timeline progress bar shows current position
  - Hover over seek bar shows thumbnail preview (optional enhancement)
- **Error Handling:**
  - Network error: "Connection lost. Retrying..." with auto-resume
  - Invalid format: "This video format is not supported. Contact support."
  - Permission error: "You don't have access to this video." (shouldn't happen if UX is right)

**4. Completion:**
- **Success Outcome:** Teacher previews video, confirms it's correct material to assign to students
- **Completion Indicator:** Video plays to end, then pauses on final frame with "Replay" option
- **What's Next:** "Assign to Students" button appears in video player modal
- **Confidence Signal:** Smooth playback with zero buffering builds trust for classroom use

**Core Experience 3: API Integration (Developer Defining Moment)**

**1. Initiation:**
- **Trigger:** Developer reads documentation "Quick Start" guide
- **Entry Points:** API docs home page, getting started tutorial, example code
- **Invitation:** "Get your first asset in 5 minutes" quick start with copy-paste code

**2. Interaction:**
- **User Action:** Copies example code, adds JWT token, makes first API call
```python
# Example from docs
import requests

headers = {"Authorization": f"Bearer {jwt_token}"}
response = requests.post(
    "https://api.dcs.example.com/v1/assets/upload",
    headers=headers,
    files={"file": open("example.pdf", "rb")}
)
```
- **System Response - Immediate:** Returns 200 OK with asset metadata JSON
- **System Response - Data:**
```json
{
  "asset_id": "uuid-here",
  "download_url": "https://minio.dcs.example.com/...",  // Presigned URL
  "filename": "example.pdf",
  "size": 1024000,
  "checksum": "sha256:...",
  "expires_at": "2025-12-15T15:30:00Z"
}
```

**3. Feedback:**
- **Success Indicators:**
  - HTTP 200 response (not 500 or vague error)
  - JSON response matches schema in docs exactly
  - Presigned URL in response works when tested in browser
- **In-Progress Indicators:**
  - For large files: Optional webhook notification when upload completes
  - For multipart uploads: Progress tracking via separate status endpoint
- **Error Handling:**
  - Specific error with code and message:
```json
{
  "error_code": "FILE_TOO_LARGE",
  "message": "Upload failed: File exceeds 10GB limit. Try compressing or splitting the file.",
  "docs_url": "https://docs.dcs.example.com/errors/FILE_TOO_LARGE",
  "max_size_bytes": 10737418240
}
```

**4. Completion:**
- **Success Outcome:** Developer successfully uploads first file, gets presigned URL, downloads it
- **Completion Indicator:** File downloads from presigned URL without authentication (URL contains auth)
- **What's Next:** Developer integrates into their app, builds upload UI for end users
- **Confidence Signal:** "Most teams complete integration in under 4 hours" (set expectation, build confidence)
