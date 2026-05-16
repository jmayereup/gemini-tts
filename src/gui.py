import tkinter as tk
from tkinter import ttk, messagebox
import threading
import os
from .tts_client import TTSClient
from .audio_encoder import encode_vbr_mp3

class TTSApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Gemini TTS Studio")
        self.root.geometry("600x700")
        
        # Initialize TTS Client
        try:
            self.client = TTSClient()
        except ValueError as e:
            messagebox.showerror("Configuration Error", str(e))
            self.root.destroy()
            return

        self._setup_ui()

    def _setup_ui(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Transcript
        ttk.Label(main_frame, text="Transcript:", font=("Helvetica", 10, "bold")).pack(anchor=tk.W)
        self.text_area = tk.Text(main_frame, height=10, wrap=tk.WORD)
        self.text_area.pack(fill=tk.BOTH, expand=True, pady=(5, 10))
        self.text_area.insert(tk.END, "Enter text here...")

        # Options Frame
        options_frame = ttk.LabelFrame(main_frame, text="Settings", padding="10")
        options_frame.pack(fill=tk.X, pady=5)

        # Voice
        ttk.Label(options_frame, text="Voice:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.voice_combo = ttk.Combobox(options_frame, values=["Charon", "Aoede", "Fenrir", "Kore", "Puck"])
        self.voice_combo.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5)
        self.voice_combo.set("Charon")

        # Scene
        ttk.Label(options_frame, text="Scene:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.scene_combo = ttk.Combobox(options_frame, values=[
            "A quiet buddhist temple.",
            "A busy urban street.",
            "A professional recording studio.",
            "A cozy living room."
        ])
        self.scene_combo.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=5)
        self.scene_combo.set("A quiet buddhist temple.")

        # Audio Profile
        ttk.Label(options_frame, text="Audio Profile:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.profile_combo = ttk.Combobox(options_frame, values=[
            "The calm clear teaching voice of a Buddhist monk.",
            "A fast-paced energetic podcast host.",
            "A friendly conversational tone.",
            "A deep dramatic narrator."
        ])
        self.profile_combo.grid(row=2, column=1, sticky=(tk.W, tk.E), padx=5)
        self.profile_combo.set("The calm clear teaching voice of a Buddhist monk.")

        options_frame.columnconfigure(1, weight=1)

        # Status
        self.status_var = tk.StringVar(value="Ready")
        self.status_label = ttk.Label(main_frame, textvariable=self.status_var, font=("Helvetica", 9, "italic"))
        self.status_label.pack(pady=5)

        # Progress Bar
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress.pack(fill=tk.X, pady=5)

        # Generate Button
        self.gen_btn = ttk.Button(main_frame, text="Generate MP3", command=self.on_generate)
        self.gen_btn.pack(pady=10)

    def on_generate(self):
        text = self.text_area.get("1.0", tk.END).strip()
        if not text:
            messagebox.showwarning("Warning", "Please enter some text.")
            return

        voice = self.voice_combo.get()
        scene = self.scene_combo.get()
        profile = self.profile_combo.get()

        self.gen_btn.config(state=tk.DISABLED)
        self.status_var.set("Generating...")
        self.progress.start()

        # Run in thread
        thread = threading.Thread(target=self._generate_thread, args=(text, voice, scene, profile))
        thread.start()

    def _generate_thread(self, text, voice, scene, profile):
        try:
            all_pcm = b""
            sample_rate = 24000
            
            for chunk_data, rate in self.client.generate_audio_stream(text, voice, scene, profile):
                all_pcm += chunk_data
                sample_rate = rate
            
            if not all_pcm:
                self._update_status("No audio generated.")
                return

            self._update_status("Encoding MP3...")
            mp3_data = encode_vbr_mp3(all_pcm, sample_rate)
            
            # Find a unique filename
            i = 0
            while os.path.exists(f"output_{i}.mp3"):
                i += 1
            filename = f"output_{i}.mp3"
            
            with open(filename, "wb") as f:
                f.write(mp3_data)
            
            self._update_status(f"Saved to {filename}")
            messagebox.showinfo("Success", f"Audio saved to {filename}")

        except Exception as e:
            self._update_status(f"Error: {str(e)}")
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
        finally:
            self.root.after(0, self._cleanup_gen)

    def _cleanup_gen(self):
        self.gen_btn.config(state=tk.NORMAL)
        self.progress.stop()

    def _update_status(self, text):
        self.root.after(0, lambda: self.status_var.set(text))
