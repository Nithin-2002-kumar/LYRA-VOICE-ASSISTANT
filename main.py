# lyra.py – LYRA: Linguistic Yielding Responsive Assistant

import logging
import subprocess
import threading
import tkinter as tk
from datetime import datetime
from tkinter import scrolledtext, ttk
import webbrowser
import os
import pyautogui
import wikipedia
import pyttsx3
import spacy
import speech_recognition as sr
from enum import Enum, auto
import re


class CommandIntents(Enum):
    OPEN_BROWSER = auto()
    OPEN_NOTEPAD = auto()
    OPEN_FILE_EXPLORER = auto()
    SEARCH_WIKIPEDIA = auto()
    OPEN_CALCULATOR = auto()
    TIME = auto()
    SCREENSHOT = auto()
    EXIT_PROGRAM = auto()


# Logging Setup
logging.basicConfig(
    filename="lyra.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


class LyraAssistant:
    def __init__(self, master):
        self.master = master
        master.title("LYRA Assistant")
        master.geometry("800x600")

        self.engine = pyttsx3.init('sapi5')
        self.engine.setProperty("rate", 150)
        self.engine.setProperty("volume", 0.9)

        self.nlp = spacy.load("en_core_web_sm")

        self.user_name = "User"
        self.expecting_name = True
        self.listening = False

        self.create_widgets()
        self.speak("What is your name?")
        threading.Thread(target=self.listen_for_name, daemon=True).start()

    def create_widgets(self):
        main_frame = ttk.Frame(self.master)
        main_frame.pack(expand=True, fill='both', padx=10, pady=10)

        self.text_area = scrolledtext.ScrolledText(main_frame, wrap=tk.WORD, state='disabled')
        self.text_area.pack(expand=True, fill='both')
        self.text_area.tag_config('user', foreground='blue')
        self.text_area.tag_config('lyra', foreground='green')

        input_frame = ttk.Frame(main_frame)
        input_frame.pack(fill='x')

        self.command_entry = ttk.Entry(input_frame)
        self.command_entry.pack(side='left', expand=True, fill='x')
        self.command_entry.bind("<Return>", self.process_text_command)

        self.listen_btn = ttk.Button(input_frame, text="🎤 Listen", command=self.toggle_listening)
        self.listen_btn.pack(side='left', padx=(5, 0))

        self.status_var = tk.StringVar()
        self.status_bar = ttk.Label(main_frame, textvariable=self.status_var)
        self.status_bar.pack(fill='x')

    def speak(self, text):
        self.text_area.configure(state='normal')
        self.text_area.insert(tk.END, f"Lyra: {text}\n", 'lyra')
        self.text_area.configure(state='disabled')
        self.text_area.see(tk.END)
        self.engine.say(text)
        self.engine.runAndWait()

    def user_says(self, text):
        self.text_area.configure(state='normal')
        self.text_area.insert(tk.END, f"You: {text}\n", 'user')
        self.text_area.configure(state='disabled')
        self.text_area.see(tk.END)

    def toggle_listening(self):
        if not self.listening:
            self.listening = True
            self.listen_btn.config(text="🔴 Listening")
            threading.Thread(target=self.listen_and_process, daemon=True).start()
        else:
            self.listening = False
            self.listen_btn.config(text="🎤 Listen")
            self.status_var.set("Ready")

    def listen_for_name(self):
        name = self.listen()
        if name:
            self.user_name = name.capitalize()
            self.expecting_name = False
            self.speak(f"Hello {self.user_name}, how can I help you today?")

    def listen_and_process(self):
        command = self.listen()
        if command:
            self.user_says(command)
            self.execute_command(command)
        self.listening = False
        self.listen_btn.config(text="🎤 Listen")

    def listen(self):
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            self.status_var.set("Listening...")
            recognizer.adjust_for_ambient_noise(source)
            try:
                audio = recognizer.listen(source, timeout=5)
                command = recognizer.recognize_google(audio, language='en')
                return command.lower()
            except:
                self.speak("Sorry, I didn't catch that.")
                return None

    def process_text_command(self, event=None):
        command = self.command_entry.get()
        self.command_entry.delete(0, tk.END)
        if command:
            self.user_says(command)
            self.execute_command(command)

    def process_command(self, text):
        patterns = {
            r"open.?browser": CommandIntents.OPEN_BROWSER,
            r"open.?notepad": CommandIntents.OPEN_NOTEPAD,
            r"open.?file.?explorer": CommandIntents.OPEN_FILE_EXPLORER,
            r"search.?wikipedia": CommandIntents.SEARCH_WIKIPEDIA,
            r"open.?calculator": CommandIntents.OPEN_CALCULATOR,
            r"what.?time": CommandIntents.TIME,
            r"screenshot": CommandIntents.SCREENSHOT,
            r"exit": CommandIntents.EXIT_PROGRAM
        }
        for pattern, intent in patterns.items():
            if re.search(pattern, text):
                return intent
        return None

    def execute_command(self, command):
        if self.expecting_name:
            self.user_name = command.capitalize()
            self.expecting_name = False
            self.speak(f"Welcome, {self.user_name}. How can I help you today?")
            return

        intent = self.process_command(command)

        try:
            if intent == CommandIntents.OPEN_BROWSER:
                self.speak("Opening browser")
                subprocess.run(["start", "chrome"], shell=True)
            elif intent == CommandIntents.OPEN_NOTEPAD:
                self.speak("Opening Notepad")
                subprocess.run(["notepad"], shell=True)
            elif intent == CommandIntents.OPEN_FILE_EXPLORER:
                self.speak("Opening File Explorer")
                subprocess.run(["explorer"], shell=True)
            elif intent == CommandIntents.SEARCH_WIKIPEDIA:
                self.speak("What should I search on Wikipedia?")
                query = self.listen()
                if query:
                    try:
                        result = wikipedia.summary(query, sentences=2)
                        self.speak(result)
                    except:
                        self.speak("Sorry, I couldn't find information on that.")
            elif intent == CommandIntents.OPEN_CALCULATOR:
                self.speak("Opening Calculator")
                subprocess.run(["calc"], shell=True)
            elif intent == CommandIntents.TIME:
                now = datetime.now().strftime("%I:%M %p")
                self.speak(f"It is {now}")
            elif intent == CommandIntents.SCREENSHOT:
                image = pyautogui.screenshot()
                image.save("lyra_screenshot.png")
                self.speak("Screenshot taken and saved.")
            elif intent == CommandIntents.EXIT_PROGRAM:
                self.speak("Goodbye!")
                self.master.quit()
            else:
                self.speak("I'm not sure how to respond to that.")
        except Exception as e:
            logging.error(f"Command failed: {e}")
            self.speak("Sorry, something went wrong.")


if __name__ == "__main__":
    root = tk.Tk()
    app = LyraAssistant(root)
    root.mainloop()
