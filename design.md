# Software Debugging Agent — Design System

## 1. Design Philosophy

The Software Debugging Agent is a developer-focused AI platform for diagnosing, investigating, and explaining software issues.

The UI should feel:

* Professional
* Technical but approachable
* Fast and responsive
* AI-native rather than chatbot-like
* Suitable for long debugging sessions
* Dense enough for developers without becoming cluttered
* Consistent with modern tools such as VS Code, GitHub, Linear, and modern observability platforms

The design system must support **both Light Mode and Dark Mode**.

### Core principles

1. **Information density without visual noise**
2. **Code and logs are first-class UI elements**
3. **Agent actions should always be observable**
4. **Errors, warnings, success states must be immediately distinguishable**
5. **Never rely on color alone to communicate state**
6. **Theme colors must come from centralized design tokens**
7. **Components must work identically in Light and Dark Mode**
8. **The theme must be replaceable without modifying individual components**

---

# 2. Theme Architecture

The application must use semantic design tokens rather than hardcoded colors.

Components should reference semantic variables such as:

```text
--background
--surface
--surface-elevated
--primary
--secondary
--accent
--text-primary
--text-secondary
--text-muted
--border
--error
--warning
--success
--info
```

Never hardcode theme-specific colors inside components.

### Example

```css
background: var(--background);
color: var(--text-primary);
border-color: var(--border);
```

This allows the entire application to switch themes through a single theme configuration.

---

# 3. Theme Options

The application should initially support four visual themes.

The user can select one theme, and the system should allow switching between them later without requiring component redesign.

---

## Theme 1 — Midnight Indigo ⭐ Recommended Default

### Concept

A modern AI/developer-tool theme inspired by VS Code, GitHub, and contemporary AI interfaces.

It should be the default theme.

### Dark Mode

| Token            | Color     |
| ---------------- | --------- |
| Background       | `#0B1020` |
| Surface          | `#111827` |
| Surface Elevated | `#172033` |
| Primary          | `#6366F1` |
| Secondary        | `#8B5CF6` |
| Accent           | `#06B6D4` |
| Text Primary     | `#F8FAFC` |
| Text Secondary   | `#CBD5E1` |
| Text Muted       | `#94A3B8` |
| Border           | `#1E293B` |
| Error            | `#EF4444` |
| Warning          | `#F59E0B` |
| Success          | `#22C55E` |
| Info             | `#38BDF8` |

### Light Mode

| Token            | Color     |
| ---------------- | --------- |
| Background       | `#F8FAFC` |
| Surface          | `#FFFFFF` |
| Surface Elevated | `#F1F5F9` |
| Primary          | `#4F46E5` |
| Secondary        | `#7C3AED` |
| Accent           | `#0891B2` |
| Text Primary     | `#0F172A` |
| Text Secondary   | `#334155` |
| Text Muted       | `#64748B` |
| Border           | `#E2E8F0` |
| Error            | `#DC2626` |
| Warning          | `#D97706` |
| Success          | `#16A34A` |
| Info             | `#0284C7` |

### Personality

**Modern AI engineering platform**

Use this as the baseline design.

---

# 4. Theme 2 — Cyber Debugger

### Concept

A futuristic developer/security-oriented theme.

Ideal if the application should feel like an autonomous debugging and security investigation console.

### Dark Mode

| Token            | Color     |
| ---------------- | --------- |
| Background       | `#05070D` |
| Surface          | `#0D1117` |
| Surface Elevated | `#151B24` |
| Primary          | `#00E5FF` |
| Secondary        | `#7C3AED` |
| Accent           | `#00FF9C` |
| Text Primary     | `#E6EDF3` |
| Text Secondary   | `#A8B3C1` |
| Text Muted       | `#6B7785` |
| Border           | `#202936` |
| Error            | `#FF3B5C` |
| Warning          | `#FFB020` |
| Success          | `#00FF9C` |
| Info             | `#00E5FF` |

### Light Mode

Use:

* Very pale cyan/gray background
* White surfaces
* Dark navy text
* Cyan primary actions
* Emerald success states
* Violet secondary actions

### Personality

**Cybersecurity + autonomous agent + terminal**

Use this theme when emphasizing the agent's investigation capabilities.

---

# 5. Theme 3 — Graphite + Electric Blue

### Concept

A highly professional developer SaaS interface.

Inspired by the visual simplicity of Linear, GitHub, and enterprise developer platforms.

### Dark Mode

| Token            | Color     |
| ---------------- | --------- |
| Background       | `#0F1115` |
| Surface          | `#181B21` |
| Surface Elevated | `#20242C` |
| Primary          | `#3B82F6` |
| Secondary        | `#60A5FA` |
| Accent           | `#14B8A6` |
| Text Primary     | `#F1F5F9` |
| Text Secondary   | `#CBD5E1` |
| Text Muted       | `#94A3B8` |
| Border           | `#272C35` |
| Error            | `#F43F5E` |
| Warning          | `#F59E0B` |
| Success          | `#22C55E` |
| Info             | `#38BDF8` |

### Light Mode

Use:

* White primary background
* Neutral gray surfaces
* Blue primary actions
* Teal secondary indicators
* Dark graphite typography
* Very subtle borders

### Personality

**Enterprise developer platform**

This should be the fallback if the Midnight Indigo theme feels too "AI-looking."

---

# 6. Theme 4 — Obsidian + Emerald

### Concept

A premium automation/infrastructure aesthetic.

The green palette represents automation, successful execution, system health, and agent autonomy.

### Dark Mode

| Token            | Color     |
| ---------------- | --------- |
| Background       | `#080C0A` |
| Surface          | `#111815` |
| Surface Elevated | `#19211D` |
| Primary          | `#10B981` |
| Secondary        | `#14B8A6` |
| Accent           | `#A3E635` |
| Text Primary     | `#ECFDF5` |
| Text Secondary   | `#C7D9D0` |
| Text Muted       | `#7F9489` |
| Border           | `#26332D` |
| Error            | `#F43F5E` |
| Warning          | `#FBBF24` |
| Success          | `#10B981` |
| Info             | `#2DD4BF` |

### Light Mode

Use:

* Warm white background
* Very light green-gray surfaces
* Emerald primary actions
* Teal secondary elements
* Dark green-gray typography

### Personality

**Intelligent automation + developer infrastructure**

---

# 7. Theme Switching

Theme switching should be implemented at the application level.

Supported modes:

```text
Light
Dark
System
```

Supported visual themes:

```text
Midnight Indigo
Cyber Debugger
Graphite + Electric Blue
Obsidian + Emerald
```

The theme system should conceptually work like:

```text
Theme
 ├── Midnight Indigo
 │    ├── Light
 │    └── Dark
 │
 ├── Cyber Debugger
 │    ├── Light
 │    └── Dark
 │
 ├── Graphite + Electric Blue
 │    ├── Light
 │    └── Dark
 │
 └── Obsidian + Emerald
      ├── Light
      └── Dark
```

Persist the user's selected theme locally so refreshing the application does not reset the preference.

---

# 8. Typography

Use a modern sans-serif font for the application UI.

Recommended:

```text
Inter
```

Fallback:

```text
system-ui
-apple-system
BlinkMacSystemFont
"Segoe UI"
sans-serif
```

For code:

```text
JetBrains Mono
```

Fallback:

```text
"Fira Code"
monospace
```

### Typography hierarchy

```text
Page Title       28–32px
Section Heading  20–24px
Card Heading     16–18px
Body             14–16px
Secondary        13–14px
Metadata         12–13px
Code             13–14px
```

Avoid excessively large typography because the application is primarily a developer workspace.

---

# 9. Layout

The primary application layout should be:

```text
┌──────────────────────────────────────────────────────────────┐
│                         Top Navigation                        │
├───────────────┬────────────────────────────────┬─────────────┤
│               │                                │             │
│   Sidebar     │       Main Workspace           │   Agent     │
│               │                                │   Panel     │
│               │                                │             │
│               │                                │             │
├───────────────┴────────────────────────────────┴─────────────┤
│                         Status Bar                            │
└──────────────────────────────────────────────────────────────┘
```

### Sidebar

Contains:

* Dashboard
* Projects
* Debug Sessions
* Issues
* Repository
* History
* Settings

### Main Workspace

Primary debugging content.

### Agent Panel

Displays:

* Agent reasoning summary
* Current action
* Tool execution
* Findings
* Suggested fixes
* Confidence
* Investigation timeline

The agent panel should never expose private chain-of-thought. Display concise **action summaries and evidence**, not hidden reasoning.

---

# 10. Dashboard

The dashboard should provide a high-level overview.

### Components

* Total debugging sessions
* Active investigations
* Resolved issues
* Critical issues
* Recent repositories
* Recent debugging sessions
* Agent activity
* System health

Example:

```text
Good morning

Your debugging overview

┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐
│ Sessions   │ │ Active     │ │ Resolved   │ │ Critical   │
│ 128        │ │ 4          │ │ 96         │ │ 3          │
└────────────┘ └────────────┘ └────────────┘ └────────────┘

Recent Debugging Sessions
────────────────────────────────────────────

Repository       Issue              Status
api-server       NullPointerError   Resolved
frontend         Build Failure      Investigating
worker           Timeout            Resolved
```

---

# 11. Debugging Workspace

This is the core screen of the application.

It should provide a unified debugging environment.

### Recommended structure

```text
┌────────────────────────────────────────────────────────────┐
│ Repository / Branch / Session Status                       │
├──────────────────────────────┬─────────────────────────────┤
│                              │                             │
│ Code / Error / Logs          │ AI Debugging Agent          │
│                              │                             │
│                              │                             │
├──────────────────────────────┴─────────────────────────────┤
│ Investigation Timeline / Tool Activity                     │
└────────────────────────────────────────────────────────────┘
```

### Tabs

```text
Overview
Error
Code
Logs
Git
Agent Activity
Evidence
```

---

# 12. Error Display

Errors should be visually prominent but not overwhelming.

Display:

* Error type
* Error message
* File
* Line number
* Stack trace
* Timestamp
* Environment
* Severity

Example:

```text
CRITICAL

TypeError
Cannot read properties of undefined

src/services/auth.ts:142

Stack Trace
────────────────────────────
...
```

Severity levels:

```text
Critical
Error
Warning
Info
```

Do not use color as the only indicator.

Include icons and text labels.

---

# 13. Code Viewer

The code viewer should support:

* Syntax highlighting
* Line numbers
* Highlighted error line
* Highlighted relevant lines
* Expand/collapse context
* Copy code
* Jump to line
* Diff visualization

Example:

```text
138 │ const user = await getUser(id);
139 │
140 │ if (!user) {
141 │     throw new Error("User not found");
142 │ }
143 │
```

The problematic line should have a clear visual indicator.

---

# 14. Git Investigation

Git should be presented as an investigation tool rather than a source-control management interface.

Display:

* Current branch
* Commit history
* Recent commits
* Changed files
* Diff
* Blame information where available
* Commit metadata

The agent should clearly distinguish:

```text
Repository Observation
Agent Finding
User Action
```

Git operations should respect the project's configured read-only restrictions.

No destructive Git actions should be exposed through the debugging UI unless explicitly implemented and authorized.

---

# 15. Agent Activity Panel

The AI agent should feel observable and trustworthy.

Example:

```text
AI DEBUGGER

● Analyzing exception
✓ Located failure point
✓ Inspected call stack
✓ Checked related files
● Inspecting recent Git changes
○ Preparing diagnosis
```

Each activity should include:

* Tool/action name
* Status
* Timestamp
* Relevant result
* Evidence/source

Avoid showing raw hidden reasoning.

Instead show concise explanations such as:

> "I found that `user` can be undefined before this function accesses `user.id`."

---

# 16. Investigation Timeline

Display debugging actions chronologically.

Example:

```text
11:32:04  Session started
11:32:05  Error parsed
11:32:07  Stack trace analyzed
11:32:09  Repository inspected
11:32:12  Relevant commit identified
11:32:15  Root cause identified
11:32:18  Fix suggested
```

Use timeline indicators instead of large cards to conserve space.

---

# 17. Evidence System

Every important agent conclusion should be traceable to evidence.

Evidence can include:

* Error logs
* Stack traces
* Source code
* Git commits
* Diffs
* Test results
* Configuration
* Runtime information

Example:

```text
Root Cause

Authentication middleware returns `None`
when the token is expired.

Evidence
├── auth/middleware.py:87
├── Error log #1842
└── Commit 8f31c2a
```

---

# 18. Suggested Fix

The suggested fix should be visually separated from the diagnosis.

Structure:

```text
Suggested Fix

Problem
────────────────────────

The middleware does not handle
expired tokens correctly.

Recommendation
────────────────────────

Return an HTTP 401 response
instead of continuing execution.

Affected File
────────────────────────

auth/middleware.py

Confidence
████████░░ 82%

Evidence
2 code references
1 Git commit
3 log entries
```

The UI should distinguish:

```text
Diagnosis
Recommendation
Evidence
```

---

# 19. Status System

Use consistent semantic states.

### Success

```text
Success
Resolved
Passed
Healthy
```

### Warning

```text
Warning
Needs Review
Potential Issue
```

### Error

```text
Error
Failed
Blocked
```

### Critical

```text
Critical
System Failure
High Risk
```

### Neutral

```text
Pending
Queued
Not Started
```

Every state should have:

* Color
* Icon
* Text label

Never rely exclusively on color.

---

# 20. Cards

Cards should be used selectively.

Avoid excessive card nesting.

Preferred:

```text
Page
 ├── Section
 │    ├── Card
 │    └── Card
 └── Section
      └── Table
```

Avoid:

```text
Card
 └── Card
      └── Card
           └── Card
```

Cards should have:

* Subtle border
* Small radius
* Consistent padding
* Clear hierarchy

Recommended radius:

```text
6px – 10px
```

Avoid excessive rounded/pill UI.

---

# 21. Buttons

Primary actions:

```text
Start Debugging
Analyze Error
Investigate
View Fix
```

Secondary actions:

```text
View Evidence
Open File
View Diff
Copy
```

Destructive actions should be visually separated.

Buttons should have:

* Clear hover state
* Focus state
* Disabled state
* Loading state

Loading buttons should not change dimensions unexpectedly.

---

# 22. Tables

Tables are preferred for structured debugging information.

Use them for:

* Sessions
* Issues
* Commits
* Files
* Agent activities
* Logs

Tables should support:

* Sorting
* Filtering
* Pagination where necessary
* Row selection
* Status indicators

---

# 23. Logs

Logs should use a terminal-inspired visual style.

Example:

```text
11:42:03 INFO     Server started
11:42:05 WARNING  Database connection slow
11:42:07 ERROR    Request failed
11:42:07 ERROR    TypeError at auth.ts:142
```

Use monospace typography.

Support:

* Search
* Filter by level
* Copy
* Expand
* Timestamp visibility
* Context expansion

---

# 24. Empty States

Empty states should explain what the user can do next.

Bad:

```text
No data.
```

Good:

```text
No debugging sessions yet.

Connect a repository and start your first
debugging investigation.
```

---

# 25. Loading States

Use skeleton loaders for page-level content.

For agent activity, use meaningful progress indicators.

Example:

```text
Analyzing repository...
✓ Repository loaded
✓ Error identified
● Inspecting relevant files
○ Checking Git history
```

Avoid generic infinite spinners for long-running agent operations.

---

# 26. Responsive Design

### Desktop

Primary target.

Use:

```text
Sidebar + Main Workspace + Agent Panel
```

### Tablet

Collapse:

```text
Sidebar → Drawer
Agent Panel → Collapsible panel
```

### Mobile

Use:

```text
Top Navigation
Main Workspace
Bottom/Drawer Agent Panel
```

Code and log viewers should support horizontal scrolling rather than breaking code formatting.

---

# 27. Accessibility

The application should target WCAG 2.2 AA principles.

Requirements:

* Keyboard navigation
* Visible focus indicators
* Semantic HTML
* Accessible labels
* Sufficient contrast
* Screen-reader-friendly status messages
* Reduced-motion support
* No color-only state indicators

Focus states must remain visible in both Light and Dark Mode.

---

# 28. Motion

Animations should be subtle and purposeful.

Use animation for:

* Panel transitions
* Agent activity updates
* Loading states
* Toasts
* Theme transitions

Avoid:

* Excessive bouncing
* Large transitions
* Decorative animations
* Continuous movement

Recommended transition duration:

```text
120ms – 250ms
```

---

# 29. Iconography

Use a consistent icon library.

Recommended:

```text
Lucide Icons
```

Icons should communicate meaning rather than decoration.

Examples:

```text
Bug       → Bug
Repository → GitBranch
Commit    → GitCommit
Logs      → Terminal
Agent     → Bot
Settings  → Settings
Success   → CheckCircle
Error     → XCircle
Warning   → AlertTriangle
```

---

# 30. Notifications

Use toast notifications for short-lived feedback.

Examples:

```text
Repository connected successfully.

Debug session started.

Analysis completed.

Failed to load repository.
```

Persistent important errors should appear inside the relevant workspace rather than only as a toast.

---

# 31. Theme Selector

Settings should include a visual theme selector.

Example:

```text
Appearance

Color Theme

○ Midnight Indigo
○ Cyber Debugger
○ Graphite + Electric Blue
○ Obsidian + Emerald

Mode

○ Light
○ Dark
○ System
```

Each theme option should display a small preview containing:

* Background
* Surface
* Primary
* Accent
* Success/Error indicators

This makes switching themes intuitive.

---

# 32. Design Tokens

The implementation should maintain a centralized token system.

Example:

```text
tokens/
├── colors
│   ├── midnight-indigo
│   ├── cyber-debugger
│   ├── graphite-blue
│   └── obsidian-emerald
│
├── typography
├── spacing
├── radius
├── shadows
└── transitions
```

Components should consume semantic tokens rather than directly consuming theme palettes.

---

# 33. Spacing System

Use a consistent spacing scale.

```text
4px
8px
12px
16px
20px
24px
32px
40px
48px
64px
```

Default component spacing:

```text
Small:  8px
Medium: 16px
Large:  24px
Section: 32px
```

---

# 34. Border Radius

Use restrained rounding.

```text
Small controls: 6px
Cards:           8px
Dialogs:         10px
Large panels:    12px
Pills:           999px
```

Pill-shaped components should primarily be used for:

* Status badges
* Tags
* Filters

---

# 35. Shadows

Prefer borders over heavy shadows.

Dark mode:

```text
Use subtle elevation through
surface color + border.
```

Light mode:

```text
Use very subtle shadows only
for elevated elements.
```

Avoid large glowing shadows except for intentional AI activity indicators.

---

# 36. Overall Visual Direction

The final product should feel closer to:

```text
VS Code
    +
GitHub
    +
Linear
    +
Modern AI Agent UI
```

rather than:

```text
Generic SaaS Dashboard
```

The debugging workspace should be the visual centerpiece.

The interface should communicate:

> "This is an intelligent developer tool that is actively investigating my software."

not:

> "This is a chatbot with some debugging features."

---

# 37. Theme Selection Rule

The application should start with:

**Midnight Indigo + Dark Mode**

because it provides the strongest balance between:

* AI identity
* Developer tooling
* Readability
* Professional appearance
* Long debugging sessions

However, **all four themes must remain fully supported**.

Changing themes should require changing only the active theme configuration, not rewriting components.

---

# 38. Definition of Done

The design implementation is considered complete when:

* [ ] Light Mode works across the entire application
* [ ] Dark Mode works across the entire application
* [ ] All four themes are implemented
* [ ] Theme switching works without page redesign
* [ ] User theme preference persists
* [ ] No component contains hardcoded theme colors
* [ ] Code viewer supports both modes
* [ ] Logs remain readable in both modes
* [ ] Agent activity remains clearly visible
* [ ] Error/warning/success states remain distinguishable
* [ ] Keyboard navigation works
* [ ] Focus states are visible
* [ ] Responsive layouts work on desktop, tablet, and mobile
* [ ] Contrast meets accessibility requirements
* [ ] Theme previews are available in Settings
* [ ] The debugging workspace remains the primary visual focus
