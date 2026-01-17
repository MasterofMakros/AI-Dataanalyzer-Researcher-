# UI Architecture & Component Hierarchy

## 🏗️ Architecture Overview
The UI follows a **feature-based** directory structure within `src/components`. State is managed via React Context (`useChat`) and local component state, moving towards `zustand` for complex global preferences.

## 🌳 Component Tree

```
Page (Layout)
├── Sidebar (Navigation)
├── ChatWindow (Main Canvas)
│   ├── EmptyChat (Onboarding/Modes)
│   │   └── SearchModeSelector [NEW]
│   ├── MessageBox (Message Stream)
│   │   ├── UserMessage
│   │   └── AssistantMessage
│   │       ├── CollapsibleSection (Sources/Reasoning)
│   │       ├── MessageSources (Web Cards)
│   │       ├── LocalMessageSources (Neural Vault Cards) [OPTIMIZE]
│   │       ├── EvidenceBoard [NEW]
│   │       ├── Answer (Markdown Renderer)
│   │       └── RelatedSuggestions
│   ├── MessageInput (Bottom Fixed)
│   │   └── FileUpload / VoiceInput
│   └── MediaSidebar (Right Panel)
│       ├── LocalMediaPreview [OPTIMIZE]
│       └── WebMediaPreview
```

## 🧠 State Management

### `useChat` Hook
Core logic for the chat loop.
- **Messages:** Array of `Message` objects.
- **Loading:** Boolean stream status.
- **Streaming:** Handling SSE deltas.

### `SearchMode` (New State)
- **Modes:** `focusMode` (Web, Academic, YouTube, Reddit, Writing, Local).
- **Optimization:** `speed` (Fast/Pro) vs `quality` (Deep Research).
- **Selection:** Persistent preference via LocalStorage.

## 📦 Data Flow
1. **User Input** → `MessageInput`
2. **Optimistic Update** → `ChatWindow` adds user message.
3. **API Call** → `useChat` triggers `/api/chat`.
4. **Stream Handling** → Updates `AssistantMessage` incrementally.
   - `sources` event → Populates `MessageSources`.
   - `message` event → Appends text to `Answer`.
   - `finish` event → Finalizes state.

## 🔧 Key Refactoring Targets

### 1. `SearchModeSelector`
**Current:** Dropdown in `EmptyChat`.
**Target:** Prominent, visual selector with icon + description cards. Status: **Plan Ready**.

### 2. `LocalMediaPreview`
**Current:** Simple list in sidebar.
**Target:** Virtualized grid with lazy-loaded thumbnails and "Quick Look" modal.

### 3. `TranscriptOverlay`
**Current:** Not implemented / Basic text.
**Target:** High-performance canvas or overlay for timestamp highlighting on video/audio.
