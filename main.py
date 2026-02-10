import os
import re
import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox
from typing import Optional

try:
    from PyPDF2 import PdfReader
except Exception:
    PdfReader = None

try:
    from dotenv import load_dotenv
except Exception:
    load_dotenv = None

try:
    from google import genai
    from google.genai import types
except Exception:
    genai = None
    types = None


APP_TITLE = "Professional Persona Chat"
UNKNOWN_LOG = "queriestoanswer.txt"
CONTACT_LOG = "contactlater.txt"
UNKNOWN_REPLY = "I don't have that information."


def read_pdf_text(path: str) -> str:
    if PdfReader is None:
        raise RuntimeError("PyPDF2 not installed. Run: pip install PyPDF2")
    reader = PdfReader(path)
    chunks = []
    for page in reader.pages:
        text = page.extract_text() or ""
        chunks.append(text)
    return "\n".join(chunks).strip()


def build_system_prompt(resume_text: str) -> str:
    guard_rails = (
        "SYSTEM GUARD RAILS:\n"
        "- You are the resume owner. Speak in first person (I, me, my).\n"
        "- Only answer using facts explicitly found in the resume below.\n"
        "- If a question is outside the resume, reply: "
        "\"I don't have that information in my resume.\" and do not speculate.\n"
        "- Ask for the user's email and their reason if they want to contact me.\n"
        "- Keep responses professional and concise.\n"
    )
    return f"{guard_rails}\nRESUME:\n{resume_text}"


def is_contact_request(text: str) -> bool:
    keywords = ["contact", "email", "reach", "connect", "talk", "call", "meeting"]
    t = text.lower()
    return any(k in t for k in keywords)


def extract_email(text: str) -> Optional[str]:
    match = re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)
    return match.group(0) if match else None


def log_unknown(question: str) -> None:
    with open(UNKNOWN_LOG, "a", encoding="utf-8") as f:
        f.write(question.strip() + "\n")


def log_contact(email: str, context: str) -> None:
    with open(CONTACT_LOG, "a", encoding="utf-8") as f:
        f.write(f"email: {email} | context: {context.strip()}\n")


def get_gemini_client():
    if load_dotenv is not None:
        load_dotenv()
    if genai is None:
        raise RuntimeError("google-genai not installed. Run: pip install google-genai")
    return genai.Client()


def call_llm(system_prompt: str, user_msg: str) -> str:
    client = get_gemini_client()
    model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    response = client.models.generate_content(
        model=model,
        contents=user_msg,
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
        ),
    )
    return (response.text or "").strip()


class ChatApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title(APP_TITLE)

        self.resume_text = ""
        self.system_prompt = ""
        self.awaiting_contact_context = False
        self.pending_email = ""
        self.client_ready = False

        self.chat = scrolledtext.ScrolledText(root, state="disabled", width=80, height=22)
        self.chat.grid(row=0, column=0, columnspan=3, padx=8, pady=8, sticky="nsew")

        self.entry = tk.Entry(root, width=70)
        self.entry.grid(row=1, column=0, padx=8, pady=8, sticky="ew")
        self.entry.bind("<Return>", self.on_send)

        self.send_btn = tk.Button(root, text="Send", command=self.on_send)
        self.send_btn.grid(row=1, column=1, padx=4, pady=8)

        self.load_btn = tk.Button(root, text="Reload Resume", command=self.load_resume)
        self.load_btn.grid(row=1, column=2, padx=4, pady=8)

        root.grid_columnconfigure(0, weight=1)
        root.grid_rowconfigure(0, weight=1)

        self._append("System", "Loading resume from resume.pdf...")
        self.load_resume()

    def _append(self, speaker: str, msg: str) -> None:
        self.chat.configure(state="normal")
        self.chat.insert(tk.END, f"{speaker}: {msg}\n")
        self.chat.configure(state="disabled")
        self.chat.see(tk.END)

    def load_resume(self) -> None:
        path = os.path.join(os.getcwd(), "resume.pdf")
        try:
            if not os.path.exists(path):
                raise RuntimeError("resume.pdf not found in project folder.")
            self.resume_text = read_pdf_text(path)
            if not self.resume_text:
                raise RuntimeError("Resume text is empty.")
            self.system_prompt = build_system_prompt(self.resume_text)
            self.client_ready = True
            self._append("System", "Resume loaded from resume.pdf. You can start chatting.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def on_send(self, event=None) -> None:
        user_msg = self.entry.get().strip()
        if not user_msg:
            return
        self.entry.delete(0, tk.END)
        self._append("You", user_msg)
        reply = self.handle_message(user_msg)
        self._append("Agent", reply)

    def handle_message(self, user_msg: str) -> str:
        if not self.system_prompt:
            return "Please load a resume PDF first."

        if self.awaiting_contact_context:
            context = user_msg
            log_contact(self.pending_email, context)
            self.awaiting_contact_context = False
            self.pending_email = ""
            return "Thanks. I have your email and reason, and will pass it along."

        if is_contact_request(user_msg):
            email = extract_email(user_msg)
            if email:
                self.pending_email = email
                self.awaiting_contact_context = True
                return "Thanks. Please share the reason you want to contact me."
            return "Sure. Please share your email and the reason you want to contact me."

        try:
            reply = call_llm(self.system_prompt, user_msg)
        except Exception as e:
            return f"LLM error: {e}"

        if reply.strip() == UNKNOWN_REPLY:
            log_unknown(user_msg)

        return reply or UNKNOWN_REPLY


def main() -> None:
    root = tk.Tk()
    app = ChatApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
