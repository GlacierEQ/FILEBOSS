# LawGlance User Guide

## New Features Overview

### Calendar Integration
1. **Connect Calendar**:
   - Say: "Connect my calendar"
   - Follow the provided URL to authenticate
   - After authentication, say: "Finalize connection"

2. **Schedule Meetings**:
   - "Schedule a meeting for March 15 2024"
   - "Create a client meeting next Tuesday"

3. **View Appointments**:
   - "Show my upcoming events"
   - "List calendar entries"

### Communication Handling
- **Send Reminders**:
  - "Remind John about the court date tomorrow"
  - "Send email to client@example.com re: case update"

### Enhanced Research
- **Verify Legal Sources**:
  - "Check citation 123 US 456"
  - "Validate this legal reference"

## Troubleshooting
- **Reset Calendar Connection**:
  - Delete `calendar_token.json` file
  - Re-authenticate using "Connect my calendar"

- **State Management**:
  - Automatic backups created in `ai_state_prev.json`
  - Manual state reset: delete `ai_state.json`
