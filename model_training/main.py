import os
import shutil
import subprocess
import sys
import threading
import time
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
from pathlib import Path


# Default target directory (where image library gets copied to)
PARENT_DIR = Path(__file__).resolve().parent
LIBRARY_COPY_DIR = os.path.join(PARENT_DIR, "library_to_train_on")
DEFAULT_MODEL_DIR = os.path.join(PARENT_DIR, "trained_models")


class App:
    def __init__(self, root):
        self.root = root
        self.root.withdraw() # don't show for first frame
        self.root.title("Classification Pipeline")

        self.source_dir = None
        self.model_dir = DEFAULT_MODEL_DIR

        # Status label
        self.status_label = tk.Label(root, text="Step 1: Select source directory")
        self.status_label.pack(pady=5)

        # Progress bar
        self.progress = ttk.Progressbar(root, length=400, mode='determinate')
        self.progress.pack(pady=5, fill='x', padx=20)

        # Log box
        self.log = tk.Text(root, height=15, width=70, state='disabled')
        self.log.pack(pady=10, fill='both', expand=True)

        # Buttons
        self.btn_select = tk.Button(root, text="Select Source Directory", command=self.select_directory)
        self.btn_annotations = tk.Button(root, text="Confirm Annotations", command=self.ask_annotations, state='disabled')
        self.btn_model = tk.Button(root, text="Select Model Save Location", command=self.select_model_dir, state='disabled')
        self.btn_train = tk.Button(root, text="Train Model", command=self.train_model, state='disabled')
        self.btn_reset = tk.Button(root, text="Restart Program", command=self.hard_reset, state='normal')

        self.btn_select.pack(pady=5, fill='x', padx=50)
        self.btn_annotations.pack(pady=5, fill='x', padx=50)
        self.btn_model.pack(pady=5, fill='x', padx=50)
        self.btn_train.pack(pady=5, fill='x', padx=50)
        self.btn_reset.pack(pady=10, fill='x', padx=50)

        self.root.update_idletasks()

        width = self.root.winfo_reqwidth()
        height = self.root.winfo_reqheight()

        x = int((self.root.winfo_screenwidth() / 2) - (width / 2))
        y = int((self.root.winfo_screenheight() / 2) - (height / 2))

        self.root.geometry(f"{width}x{height}+{x}+{y}")
        self.root.minsize(width, height)
        self.root.resizable(True, True)

        self.root.deiconify() # now show window

    def log_message(self, msg):
        self.log.config(state='normal')
        self.log.insert(tk.END, msg + "\n")
        self.log.see(tk.END)
        self.log.config(state='disabled')
        self.root.update_idletasks()

    def select_directory(self):
        self.progress.pack(pady=5, fill='x', padx=20)
        self.source_dir = filedialog.askdirectory(title="Select Source Directory")
        if not self.source_dir:
            self.log_message("No directory selected. Skipping copy step.")
            self.btn_annotations.config(state='normal')
            self.btn_select.config(state='disabled')

            self.status_label.config(text="Step 2: Confirm annotations")
            self.btn_annotations.config(state='normal')
            self.progress.pack_forget()
            return

        self.log_message(f"Selected: {self.source_dir}")
        self.status_label.config(text="Copying files...")
        self.btn_select.config(state='disabled')
        self.progress.pack_forget()

        threading.Thread(target=self.copy_files).start()

    def copy_files(self):
        if not os.path.exists(LIBRARY_COPY_DIR):
            os.makedirs(LIBRARY_COPY_DIR)

        files = os.listdir(self.source_dir)
        total = len(files)

        if total == 0:
            self.log_message("No files found to copy.")
        else:
            for i, filename in enumerate(files):
                src = os.path.join(self.source_dir, filename)
                dst = os.path.join(LIBRARY_COPY_DIR, filename)

                if os.path.exists(dst):
                    self.log_message(f"Skipped (already exists): {filename}")
                elif os.path.isfile(src):
                    shutil.copy2(src, dst)
                    self.log_message(f"Copied: {filename}")

                progress_value = int((i + 1) / total * 100)
                self.progress['value'] = progress_value

                time.sleep(0.01)  # slight delay so UI updates smoothly

        self.log_message("File copy complete.")
        self.status_label.config(text="Step 2: Confirm annotations")
        self.btn_annotations.config(state='normal')

    def ask_annotations(self):
        result = messagebox.askyesno("Annotations", "Have annotations been supplied?")

        if not result:
            self.log_message("Annotations not provided. Launching labelme...")
            self.status_label.config(text="Launching labelme...")

            self.root.after(2000, self.launch_labelme)
            return
        
        self.btn_annotations.config(state='disabled', text="Annotations Confirmed ✓")
        self.log_message("Annotations confirmed.")
        self.status_label.config(text="Step 3: Select model save location")
        self.btn_model.config(state='normal')

    def launch_labelme(self):
        subprocess.Popen([sys.executable, "-m", "labelme"])
        self.root.destroy()

    def select_model_dir(self):
        use_default = messagebox.askyesno("Model Location", "Use default model directory?")

        if use_default:
            self.model_dir = DEFAULT_MODEL_DIR
        else:
            chosen = filedialog.askdirectory(title="Select Model Directory")
            if chosen:
                self.model_dir = chosen

        self.log_message(f"Model directory: {self.model_dir}")
        self.status_label.config(text="Ready to train model")
        self.btn_model.config(state='disabled')
        self.btn_train.config(state='normal')

    def train_model(self):
        self.status_label.config(text="Training model...")
        self.btn_train.config(state='disabled')

        threading.Thread(target=self._train_model_thread).start()

    def _train_model_thread(self):
        if not os.path.exists(self.model_dir):
            os.makedirs(self.model_dir)

        # Simulated training
        for i in range(5):
            self.log_message(f"Training step {i+1}/5...")
            time.sleep(1)

        self.log_message("Training complete. You may close the program now or restart")
        self.status_label.config(text="Done")
        messagebox.showinfo("Success", "Your classification models have been successfully trained")

    def hard_reset(self):
        confirm = messagebox.askyesno(
            "Restart",
            "This will restart the entire program. Continue?"
        )

        if not confirm:
            return

        self.root.destroy()
        subprocess.Popen([sys.executable] + sys.argv)


if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()