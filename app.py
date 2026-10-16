"""A small voice assistant demo using NLTK, SpeechRecognition, and pyttsx3.

Speech-to-text uses Google's recognition service through SpeechRecognition, so
an internet connection is needed while listening. Text-to-speech is local.
"""

from __future__ import annotations

import datetime as dt
import threading
import tkinter as tk
import urllib.parse
import webbrowser
from tkinter import messagebox, scrolledtext

import nltk
import pyttsx3
import speech_recognition as sr
from nltk.stem import PorterStemmer
from nltk.tokenize import wordpunct_tokenize


class VoiceAssistantApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Python Voice Assistant")
        self.root.geometry("560x440")
        self.root.minsize(460, 360)

        self.recognizer = sr.Recognizer()
        self.stemmer = PorterStemmer()
        self.speaker = pyttsx3.init()
        self.speaker.setProperty("rate", 175)
        self.busy = False

        tk.Label(root, text="Voice Assistant", font=("Segoe UI", 20, "bold")).pack(pady=(16, 4))
        tk.Label(
            root,
            text="Click Listen and try: ‘what time is it’, ‘open YouTube’, or ‘search for cats’.",
            wraplength=500,
        ).pack(padx=16, pady=(0, 12))

        self.conversation = scrolledtext.ScrolledText(root, height=13, wrap=tk.WORD, state=tk.DISABLED)
        self.conversation.pack(fill=tk.BOTH, expand=True, padx=16, pady=4)

        buttons = tk.Frame(root)
        buttons.pack(pady=12)
        self.listen_button = tk.Button(buttons, text="🎙 Listen", width=16, command=self.listen)
        self.listen_button.pack(side=tk.LEFT, padx=5)
        tk.Button(buttons, text="Exit", width=10, command=self.close).pack(side=tk.LEFT, padx=5)

        self.status = tk.StringVar(value="Ready")
        tk.Label(root, textvariable=self.status, anchor="w", relief=tk.SUNKEN).pack(fill=tk.X, side=tk.BOTTOM)
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.say("Hello! I am ready. Click Listen and tell me a command.")

    def add_line(self, who: str, text: str) -> None:
        self.conversation.configure(state=tk.NORMAL)
        self.conversation.insert(tk.END, f"{who}: {text}\n\n")
        self.conversation.see(tk.END)
        self.conversation.configure(state=tk.DISABLED)

    def say(self, text: str) -> None:
        self.add_line("Assistant", text)
        # Speech runs off the GUI thread so the window stays responsive.
        threading.Thread(target=self._speak, args=(text,), daemon=True).start()

    def _speak(self, text: str) -> None:
        try:
            self.speaker.say(text)
            self.speaker.runAndWait()
        except RuntimeError:
            # Ignore overlapping speech engine shutdown during app close.
            pass

    def listen(self) -> None:
        if self.busy:
            return
        self.busy = True
        self.listen_button.configure(state=tk.DISABLED)
        self.status.set("Listening…")
        threading.Thread(target=self._listen_worker, daemon=True).start()

    def _listen_worker(self) -> None:
        try:
            with sr.Microphone() as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = self.recognizer.listen(source, timeout=6, phrase_time_limit=8)
            self.root.after(0, lambda: self.status.set("Recognizing speech…"))
            text = self.recognizer.recognize_google(audio)
            self.root.after(0, lambda heard=text: self.add_line("You", heard))
            self.root.after(0, lambda heard=text: self.handle_command(heard))
        except sr.WaitTimeoutError:
            self.root.after(0, lambda: self.say("I did not hear anything. Please try again."))
        except sr.UnknownValueError:
            self.root.after(0, lambda: self.say("Sorry, I could not understand that."))
