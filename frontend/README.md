# Personal AI frontend

This directory contains the first user-facing UI foundation for the personal AI chatbot.

## Product rules

- Keep the primary experience to **Chat** and **Research**.
- Treat files, voice, images, citations, projects and memory as capabilities of a conversation, not separate modes.
- Open the right-side workspace only when an artifact, file preview, research detail or other secondary context is useful.
- Keep the main navigation small: New Chat, Search, Chats, Projects, Saved, Settings.
- Do not add model-selection controls, paid-plan UI, agent marketplaces, social feeds, or other features that the current backend does not actually provide.
- Prefer progressive disclosure: show advanced controls only when the current task needs them.
- Keep the responsive mobile experience close to the simplicity of Telegram/WhatsApp-style chat.

## Current UI slice

- Responsive desktop/tablet/mobile shell
- Telegram-style sidebar and chat history
- Searchable chat list
- Chat / Research composer switch
- File/voice attachment affordances
- Product/result cards with actions
- Citations and source status
- Research progress state
- Contextual right-side workspace
- File cards in workspace
- Saved/projects/settings navigation placeholders
- System / light / dark appearance
- Accent themes and compact/comfortable density
- Keyboard shortcut (`Ctrl/Cmd + K`)

The current implementation is intentionally frontend-only. Backend/API wiring should be added without changing the information architecture unless real product requirements prove that a change is necessary.
