import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import os
import json
import re
from .tts_client import TTSClient
from .audio_encoder import encode_vbr_mp3

SETTINGS_FILE = "settings.json"

class TTSApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Gemini TTS Studio")
        self.root.geometry("650x750")
        
        # Load settings
        self.settings = self._load_settings()
        
        # Initialize TTS Client
        try:
            self.client = TTSClient()
        except ValueError as e:
            messagebox.showerror("Configuration Error", str(e))
            self.root.destroy()
            return

        self._setup_ui()

    def _load_settings(self):
        default_settings = {
            "voices": ["Charon", "Aoede", "Fenrir", "Kore", "Puck"],
            "scenes": ["A quiet buddhist temple."],
            "profiles": ["The calm clear teaching voice of a Buddhist monk."],
            "default_save_path": os.getcwd()
        }
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, "r") as f:
                try:
                    settings = json.load(f)
                    # Ensure all keys exist
                    for key, value in default_settings.items():
                        if key not in settings:
                            settings[key] = value
                    return settings
                except json.JSONDecodeError:
                    return default_settings
        return default_settings

    def _save_settings(self):
        with open(SETTINGS_FILE, "w") as f:
            json.dump(self.settings, f, indent=2)

    def _add_option(self, combo, key):
        value = combo.get().strip()
        if value and value not in self.settings[key]:
            self.settings[key].append(value)
            self._save_settings()
            combo['values'] = self.settings[key]
            messagebox.showinfo("Success", f"Added '{value}' to {key}")
        elif not value:
            messagebox.showwarning("Warning", "Cannot add empty option")
        else:
            messagebox.showinfo("Info", "Option already exists")

    def _remove_option(self, combo, key):
        value = combo.get().strip()
        if value in self.settings[key]:
            if messagebox.askyesno("Confirm", f"Remove '{value}' from {key}?"):
                self.settings[key].remove(value)
                self._save_settings()
                combo['values'] = self.settings[key]
                if self.settings[key]:
                    combo.set(self.settings[key][0])
                else:
                    combo.set("")
        else:
            messagebox.showwarning("Warning", "Option not found in list")

    def _setup_ui(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Header Frame
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 5))

        # Transcript Label
        ttk.Label(header_frame, text="Transcript:", font=("Helvetica", 10, "bold")).pack(side=tk.LEFT)
        
        # Settings Button
        settings_btn = ttk.Button(header_frame, text="⚙ Settings", width=12, command=self._open_settings_dialog)
        settings_btn.pack(side=tk.RIGHT)
        
        # Using a font that is more likely to support Unicode/Thai on Linux
        self.text_area = tk.Text(main_frame, height=10, wrap=tk.WORD, font=("Helvetica", 12))
        self.text_area.pack(fill=tk.BOTH, expand=True, pady=(5, 10))
        self.text_area.insert(tk.END, "Enter text here...")
        
        # Placeholder behavior
        self.text_area.bind("<FocusIn>", self._on_text_focus)
        self.text_area.bind("<FocusOut>", self._on_text_blur)
        self.text_area.config(foreground="grey")

        # Options Frame
        options_frame = ttk.LabelFrame(main_frame, text="Settings", padding="10")
        options_frame.pack(fill=tk.X, pady=5)

        # Helper to create row with +/- buttons
        def create_option_row(parent, label, key, row):
            ttk.Label(parent, text=f"{label}:").grid(row=row, column=0, sticky=tk.W, pady=5)
            
            combo = ttk.Combobox(parent, values=self.settings[key])
            combo.grid(row=row, column=1, sticky=(tk.W, tk.E), padx=5)
            if self.settings[key]:
                combo.set(self.settings[key][0])
            
            btn_frame = ttk.Frame(parent)
            btn_frame.grid(row=row, column=2, sticky=tk.W)
            
            add_btn = ttk.Button(btn_frame, text="+", width=3, 
                                 command=lambda: self._add_option(combo, key))
            add_btn.pack(side=tk.LEFT, padx=2)
            
            rem_btn = ttk.Button(btn_frame, text="-", width=3, 
                                 command=lambda: self._remove_option(combo, key))
            rem_btn.pack(side=tk.LEFT, padx=2)
            
            return combo

        self.voice_combo = create_option_row(options_frame, "Voice", "voices", 0)
        self.scene_combo = create_option_row(options_frame, "Scene", "scenes", 1)
        self.profile_combo = create_option_row(options_frame, "Audio Profile", "profiles", 2)

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

    def _split_text(self, text, limit=1000):
        """Splits text into chunks of max limit characters, respecting paragraphs."""
        paragraphs = text.split('\n')
        chunks = []
        current_chunk = ""
        
        for p in paragraphs:
            p = p.strip()
            if not p:
                continue
            
            # If adding this paragraph exceeds limit
            if len(current_chunk) + len(p) + 1 > limit:
                if current_chunk:
                    chunks.append(current_chunk)
                    current_chunk = ""
                
                # If the paragraph itself is too long, split it by sentence or length
                if len(p) > limit:
                    # Split by common sentence enders or just spaces
                    sentences = re.split(r'([。\.!\?\s]+)', p)
                    temp_chunk = ""
                    for s in sentences:
                        if not s: continue
                        if len(temp_chunk) + len(s) > limit:
                            if temp_chunk:
                                chunks.append(temp_chunk)
                            temp_chunk = s
                        else:
                            temp_chunk += s
                    current_chunk = temp_chunk
                else:
                    current_chunk = p
            else:
                if current_chunk:
                    current_chunk += "\n" + p
                else:
                    current_chunk = p
                    
        if current_chunk:
            chunks.append(current_chunk)
            
        return chunks

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
            
            chunks = self._split_text(text)
            num_chunks = len(chunks)
            
            for i, chunk in enumerate(chunks):
                if num_chunks > 1:
                    self._update_status(f"Generating part {i+1}/{num_chunks}...")
                
                for chunk_data, rate in self.client.generate_audio_stream(chunk, voice, scene, profile):
                    all_pcm += chunk_data
                    sample_rate = rate
            
            if not all_pcm:
                self._update_status("No audio generated.")
                return

            self._update_status("Encoding MP3...")
            mp3_data = encode_vbr_mp3(all_pcm, sample_rate)
            
            self._update_status("Ready to save.")
            self.root.after(0, lambda: self._save_audio(mp3_data))

        except Exception as e:
            self._update_status(f"Error: {str(e)}")
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
        finally:
            self.root.after(0, self._cleanup_gen)

    def _save_audio(self, data):
        initial_dir = self.settings.get("default_save_path")
        if not initial_dir or not os.path.exists(initial_dir):
            initial_dir = os.getcwd()

        filename = filedialog.asksaveasfilename(
            defaultextension=".mp3",
            filetypes=[("MP3 files", "*.mp3"), ("All files", "*.*")],
            initialdir=initial_dir,
            initialfile="tts_output.mp3",
            title="Save Generated Audio"
        )
        
        if filename:
            try:
                with open(filename, "wb") as f:
                    f.write(data)
                self._update_status(f"Saved to {os.path.basename(filename)}")
                messagebox.showinfo("Success", f"Audio saved successfully!")
            except Exception as e:
                messagebox.showerror("Save Error", f"Could not save file: {e}")
        else:
            self._update_status("Save cancelled.")

    def _cleanup_gen(self):
        self.gen_btn.config(state=tk.NORMAL)
        self.progress.stop()

    def _update_status(self, text):
        self.root.after(0, lambda: self.status_var.set(text))

    def _on_text_focus(self, event):
        if self.text_area.get("1.0", tk.END).strip() == "Enter text here...":
            self.text_area.delete("1.0", tk.END)
            self.text_area.config(foreground="black")

    def _on_text_blur(self, event):
        if not self.text_area.get("1.0", tk.END).strip():
            self.text_area.insert("1.0", "Enter text here...")
            self.text_area.config(foreground="grey")

    def _open_settings_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Settings")
        dialog.geometry("500x220")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Center the dialog
        dialog.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (dialog.winfo_width() // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")

        frame = ttk.Frame(dialog, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="Default Save Location:", font=("Helvetica", 10, "bold")).pack(anchor=tk.W, pady=(0, 5))
        
        path_frame = ttk.Frame(frame)
        path_frame.pack(fill=tk.X, pady=5)
        
        path_var = tk.StringVar(value=self.settings.get("default_save_path", ""))
        path_entry = ttk.Entry(path_frame, textvariable=path_var)
        path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        def browse_path():
            directory = filedialog.askdirectory(parent=dialog, initialdir=path_var.get() or os.getcwd())
            if directory:
                path_var.set(directory)
                
        browse_btn = ttk.Button(path_frame, text="Browse...", command=browse_path)
        browse_btn.pack(side=tk.RIGHT)
        
        ttk.Label(frame, text="Generated files will start in this folder by default.", 
                  font=("Helvetica", 8), foreground="grey").pack(anchor=tk.W, pady=(0, 10))

        def save_and_close():
            new_path = path_var.get().strip()
            if new_path and not os.path.exists(new_path):
                if not messagebox.askyesno("Warning", "The path does not exist. Save anyway?", parent=dialog):
                    return
            
            self.settings["default_save_path"] = new_path
            self._save_settings()
            messagebox.showinfo("Success", "Settings saved!", parent=dialog)
            dialog.destroy()
            
        save_btn = ttk.Button(frame, text="Save Settings", command=save_and_close)
        save_btn.pack(pady=10)
