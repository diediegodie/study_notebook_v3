# Study Notebook

A minimalist, local-first notebook app for students, inspired by Notion and Obsidian. Designed for simplicity, speed, and usability—no configuration or account required.

## Features
- **Organize notes in folders and subfolders**
- **Markdown support** for all notes
- **Material Design UI** built with [Flet](https://flet.dev/docs/)
- **Local storage**: all data saved on your device
- **Zero configuration**: open and start using immediately
- **No login/account required**

## Philosophy
- **Simple, Fast, Useful**: Anyone can use it in 5 minutes
- **3 Clicks Rule**: No action requires more than 3 clicks
- **Local First**: Privacy and speed by default

## Tech Stack
- **Frontend**: Flet (Python)
- **Backend**: Python 3.8+, Clean Architecture principles
- **UI**: Material Design, theme variables for consistency
- **Data Format**: Markdown (.md files)

## Project Structure
- `main.py`: App entry point
- `backend/`: State and file management
- `ui/`: Pages, widgets, and themes
- `notebooks/`: User notes and folders
- `docs/`: Documentation and instructions

## How to Run
1. Install [Python 3.8+](https://www.python.org/downloads/)
2. Install dependencies:
   ```bash
   pip install flet
   ```
3. Run the app:
   ```bash
   python main.py
   ```

## Code Style & Architecture
- Modular, clean code following Clean Architecture
- Separation of concerns: UI, backend, state, and file management
- All styles use theme variables for consistency

## For Developers
- See `docs/instructions.md` for development guidelines
- Follow Material Design and Clean Architecture best practices
- Do not add features outside the defined roadmap

---
For more info, see the [Material Design Guidelines](https://material.io/design/) and [Flet documentation](https://flet.dev/docs/).
