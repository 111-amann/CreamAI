# Screenshot Instructions for Checkpoint 2

## Required Screenshot: `checkpoint-2.png`

Capture a screenshot of the running Streamlit application showing:

### Essential Elements to Capture:

1. **Application Header**
   - Title: "🐍 PyDocsPal"
   - Subtitle: "Your Python Documentation Assistant"

2. **Sidebar (Left)**
   - Backend URL display
   - Backend connection status (✅ Backend connected)
   - Mode selector showing both "RAG" and "Agent" options
   - Python Version dropdown (showing versions 3.8-3.15)

3. **Chat Interface (Main Area)**
   - At least one complete user-assistant exchange
   - User message in chat bubble
   - Assistant response with formatted text

4. **Key Features Visible**
   - **Citations section** (📚 Sources) with expandable details
   - **Compatibility badge** showing one of:
     - ✅ Works from Python X.Y
     - ⚠️ Deprecated since Python X.Y
     - ❌ Removed in Python X.Y
     - 💡 Compatibility unknown
   - **Feedback buttons** (👍 and 👎)

5. **Bonus Elements (if possible in one screenshot)**
   - Expanded citation showing source details
   - Expanded compatibility information
   - Agent mode showing approval buttons (if in approval state)

### Recommended Test Queries for Screenshot:

**For RAG Mode:**
```
What is pathlib.Path.mkdir?
```

**For Agent Mode (best for compatibility badges):**
```
Is pathlib.Path.mkdir available in Python 3.8?
```

or

```
Tell me about os.popen and check if it's deprecated
```

### How to Capture:

1. Start both servers:
   ```bash
   # Terminal 1
   python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
   
   # Terminal 2
   streamlit run ui/app.py
   ```

2. Open browser to `http://localhost:8501`

3. Set up the desired view:
   - Select appropriate mode (Agent mode recommended for compatibility features)
   - Select Python version (3.8 or 3.12)
   - Submit a test query
   - Expand at least one citation
   - Optionally expand compatibility details

4. Capture screenshot:
   - Windows: Windows Key + Shift + S
   - Mac: Cmd + Shift + 4
   - Linux: Print Screen or Screenshot tool

5. Save as: `docs/screenshots/checkpoint-2.png`

### Image Specifications:

- Format: PNG
- Recommended minimum width: 1280px
- Recommended minimum height: 800px
- Should show full browser window with Streamlit interface
- Clear, readable text (avoid tiny fonts or excessive zoom)

### Verification Checklist:

- [ ] Application title visible
- [ ] Sidebar with settings visible
- [ ] At least one complete Q&A visible
- [ ] Citations section visible
- [ ] Compatibility badge or info visible
- [ ] Feedback buttons visible
- [ ] Image is clear and readable
- [ ] File saved as `checkpoint-2.png` in `docs/screenshots/`
- [ ] Image referenced in README.md
