# Professional Persona Resume Chat (Gemini)

A minimal Python chat UI that answers as you (the resume owner), using only facts from `resume.pdf`. It logs unknown questions and collects contact requests.

## Features
- Loads `resume.pdf` from the project root on startup.
- Responds in first person and only with resume facts.
- Logs unknown questions to `queriestoanswer.txt`.
- Collects contact requests (email + reason) in `contactlater.txt`.
- Simple Tkinter chat UI.

## Setup
1. Create a virtual environment (optional but recommended).
2. Install dependencies:

```bash
pip install google-genai python-dotenv PyPDF2
```

3. Add your Gemini API key in `.env`:

```env
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-2.5-flash
```

## Run
```bash
python main.py
```

## Files
- `main.py` - app code
- `resume.pdf` - your resume (required)
- `.env` - local secrets (do not commit)
- `queriestoanswer.txt` - unknown questions log
- `contactlater.txt` - contact requests log

## Notes
- If `resume.pdf` is missing, the app will show an error on startup.
- You can change the model in `.env` (for example, `gemini-2.5-flash-lite`).

## Security
- Keep `.env` out of git. Rotate keys if they are ever exposed.
