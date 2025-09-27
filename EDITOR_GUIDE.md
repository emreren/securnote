# External Editor Guide for SecurNote

## Overview
SecurNote now supports external editors for writing and editing notes, making it easier to create longer content.

## Usage

### 1. Starting CLI
```bash
poetry run python -m securnote
```

### 2. Adding Notes with External Editor
1. Login to your account
2. Choose "1. Add Note"
3. Select "2. Use external editor"
4. Enter note title
5. Your default editor will open
6. Write your content and save/exit
7. Note will be encrypted and stored

### 3. Editing Existing Notes
1. Login to your account
2. Choose "4. Edit Note"
3. Select the note ID from the list
4. Choose editing option:
   - 1: Edit title only
   - 2: Edit content with external editor
   - 3: Edit both

## Editor Configuration

### Setting Default Editor
```bash
# Use nano (default)
export EDITOR=nano

# Use vim
export EDITOR=vim

# Use any editor available in PATH
export EDITOR=your_editor
```

### Available Editors
- **nano**: Simple, user-friendly editor
- **vim**: Advanced editor with powerful features
- **vi**: Basic vi editor

## Features

### For New Notes
- Choose between inline typing or external editor
- Automatic comment line removal (lines starting with #)
- Temporary file cleanup
- Empty content validation

### For Editing Notes
- View current content in editor
- Modify existing notes
- Update title and/or content
- Preserve encryption and security

## Security Notes
- All content is encrypted before storage
- Temporary files are automatically deleted
- Original note security is maintained during editing
- No plaintext data is permanently stored

## Example Workflow
```bash
# Set preferred editor
export EDITOR=nano

# Start SecurNote
poetry run python -m securnote

# Register/Login
# Add notes using external editor
# Edit existing notes as needed
```