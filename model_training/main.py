import os
import shutil
import subprocess
import sys
import threading
import time
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
from pathlib import Path
from pipeline_gui_application import (
    polygons_to_rle_coco as ptrc, 
    train_AMM_classifier as trammc
)


# Default target directory (where image library gets copied to)
PARENT_DIR = Path(__file__).resolve().parent
LIBRARY_COPY_DIR = os.path.join(PARENT_DIR, "library_to_train_on")
DEFAULT_MODEL_DIR = os.path.join(PARENT_DIR, "trained_models")
ANNOTATIONS_DIR = os.path.join(PARENT_DIR, "manual_label_annotations")
RAM_DIR = os.path.join(PARENT_DIR, "intermittent_storage")
TRAINABLE_ANNOTATIONS_FILE = "coco.json"

AMM_CLASSIFIER_CONFIG = os.path.join(PARENT_DIR, "pipeline_gui_application", "train_AMM_classifier_config.json")

class App:
    def __init__(self, root):
        self.root = root
        self.root.withdraw() # don't show for first frame
        self.root.title("Classification Pipeline")

        self.source_dir = None
        self.model_dir = DEFAULT_MODEL_DIR

        # Status label
        self.status_label = tk.Label(root, text="Step 1: Select source directory for copying training images")
        self.status_label.pack(pady=5)

        # Clear inputs
        self.btn_clear = tk.Button(root, text="Clear Training Inputs", command=self.clear_training_inputs, state='normal')

        # Progress bar
        self.progress = ttk.Progressbar(root, length=400, mode='determinate')
        self.progress.pack(pady=5, fill='x', padx=20)

        # Log box
        self.log = tk.Text(root, height=15, width=70, state='disabled')
        self.log.pack(pady=10, fill='both', expand=True)

        # Buttons
        self.btn_row_1 = tk.Frame(self.root)
        self.btn_select = tk.Button(self.btn_row_1, text="Select Source Directory", command=self.select_directory)
        self.btn_skip = tk.Button(self.btn_row_1, text="Skip Source Selection", command=self.skip_source_selection)
        self.btn_annotations = tk.Button(root, text="Confirm Annotations", command=self.ask_annotations, state='disabled')
        self.btn_model = tk.Button(root, text="Select Model Save Location", command=self.select_model_dir, state='disabled')
        self.btn_train = tk.Button(root, text="Train Model", command=self.train_model, state='disabled')
        self.btn_reset = tk.Button(root, text="Restart Program", command=self.hard_reset, state='normal')

        self.btn_clear.pack(expand=True, pady=5, fill='x', padx=50)
        self.btn_row_1.pack(pady=5, fill='x', padx=50)
        self.btn_skip.pack(side='right', expand=True, pady=5, fill='x', padx=50)
        self.btn_select.pack(side='left', expand=True, pady=5, fill='x', padx=50)
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

    import tkinter as tk

    def custom_yes_no_cancel(self, title, message,
                          yes_text="Yes",
                          no_text="No",
                          cancel_text="Cancel"):

        win = tk.Toplevel(self.root)
        win.title(title)
        win.grab_set()
        win.resizable(False, False)
        win.withdraw()

        result = {"value": None}

        # Message
        tk.Label(win, text=message, padx=20, pady=10).pack()

        # Button actions
        def yes():
            result["value"] = True
            win.destroy()

        def no():
            result["value"] = False
            win.destroy()

        def cancel():
            result["value"] = None
            win.destroy()

        def close_x():
            result["value"] = "closed"
            win.destroy()

        win.protocol("WM_DELETE_WINDOW", close_x)

        # Buttons
        btn_frame = tk.Frame(win)
        btn_frame.pack(pady=10, padx=10, fill='x', expand=True)

        tk.Button(btn_frame, text=yes_text, command=yes).pack(side="left", expand=True, fill='x', padx=5)
        tk.Button(btn_frame, text=no_text, command=no).pack(side="left", expand=True, fill='x', padx=5)
        tk.Button(btn_frame, text=cancel_text, command=cancel).pack(side="left", expand=True, fill='x', padx=5)

        # ---- CENTER OVER MAIN WINDOW ----
        win.update_idletasks()

        parent_x = self.root.winfo_rootx()
        parent_y = self.root.winfo_rooty()
        parent_w = self.root.winfo_width()
        parent_h = self.root.winfo_height()

        win_w = win.winfo_reqwidth()
        win_h = win.winfo_reqheight()

        x = parent_x + (parent_w - win_w) // 2
        y = parent_y + (parent_h - win_h) // 2

        win.geometry(f"{win_w}x{win_h}+{x}+{y}")

        # Block until closed
        win.deiconify()
        win.wait_window()

        return result["value"]

    def log_message(self, msg):
        self.log.config(state='normal')
        self.log.insert(tk.END, msg + "\n")
        self.log.see(tk.END)
        self.log.config(state='disabled')
        self.root.update_idletasks()

    def select_directory(self):
        self.source_dir = filedialog.askdirectory(title="Select Source Directory")
        if not self.source_dir:
            self.log_message("No directory selected. Skipping copy step.")
            self.btn_annotations.config(state='normal')
            self.btn_select.config(state='disabled')

            self.status_label.config(text="Step 2: Confirm annotations")
            self.btn_annotations.config(state='normal')
            return

        self.log_message(f"Selected: {self.source_dir}")
        self.status_label.config(text="Copying files...")
        self.btn_select.config(state='disabled')
        self.btn_skip.config(state='disabled')

        threading.Thread(target=self.copy_files, daemon=True).start()

    def skip_source_selection(self):
        self.log_message("Source selection skipped.")
        self.source_dir = None  # or a default folder if you want
        self.status_label.config(text="Step 2: Confirm annotations")
        self.btn_select.config(state='disabled')
        self.btn_skip.config(state='disabled')
        self.btn_annotations.config(state='normal')

    def copy_files(self, src_dir=None, dest_dir=LIBRARY_COPY_DIR, proceed_pipeline=True):
        self.progress.pack(pady=5, fill='x', padx=20)
        if not os.path.exists(dest_dir):
            os.makedirs(dest_dir)

        if src_dir is None:
            src_dir = self.source_dir
        files = os.listdir(src_dir)
        total = len(files)

        if total == 0:
            self.log_message("No files found to copy.")
        else:
            for i, filename in enumerate(files):
                src = os.path.join(src_dir, filename)
                dst = os.path.join(dest_dir, filename)

                if os.path.exists(dst):
                    self.log_message(f"Skipped (already exists): {filename}")
                elif os.path.isfile(src):
                    shutil.copy2(src, dst)
                    self.log_message(f"Copied: {filename}")

                progress_value = int((i + 1) / total * 100)
                self.progress['value'] = progress_value

                time.sleep(0.01)  # slight delay so UI updates smoothly

        self.log_message("File copy complete.")
        if not proceed_pipeline: return

        # Done with step 1 if coming from there
        self.status_label.config(text="Step 2: Confirm annotations")
        self.btn_annotations.config(state='normal')

    def ask_annotations(self):
        result = self.custom_yes_no_cancel("Annotations", "Have annotations been supplied?", yes_text="Already supplied", no_text="Import Annotations", cancel_text="Launch Labelme")

        if result is None:
            self.log_message("Launching Labelme...")
            self.status_label.config(text="Launching labelme...")
            self.root.after(2000, self.launch_labelme)
            return
        elif result is False:
            folder = filedialog.askdirectory(title="Select Annotation Folder")

            if folder:
                self.annotation_folder = folder
                self.copy_files(folder, ANNOTATIONS_DIR, proceed_pipeline=False)
                self.log_message(f"Imported annotations from: {folder}")

                self.btn_annotations.config(
                    state='disabled',
                    text="Annotations Imported ✓"
                )
        elif result == "closed":
            return

        self.btn_annotations.config(state='disabled', text="Annotations Confirmed ✓")
        self.btn_clear.config(state='disabled')
        self.log_message("Annotations confirmed. Converting annotations from each image to a trainable format...")
        for img_ref, prog_status in ptrc.create_bulk_coco_annotations_from_polygon_images(ANNOTATIONS_DIR, os.path.join(RAM_DIR, TRAINABLE_ANNOTATIONS_FILE)):
            if prog_status < 100: self.log_message(f"Transposed annotations of {img_ref}")
            self.progress['value'] = prog_status
        self.log_message("Formatting complete.")
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

        threading.Thread(target=self._train_model_thread, daemon=True).start()

    def _train_model_thread(self):
        if not os.path.exists(self.model_dir):
            os.makedirs(self.model_dir)

        self.log_message("Loading images and applying various settings before classifier training begins...")
        for training_log_entry, progress_value in trammc.train_amm_classifier_model(AMM_CLASSIFIER_CONFIG, LIBRARY_COPY_DIR,
                                        os.path.join(RAM_DIR, TRAINABLE_ANNOTATIONS_FILE), 
                                        self.model_dir):
            self.progress['value'] = progress_value
            self.log_message(training_log_entry)

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
    
    def clear_directory(self, folder_path):
        self.log_message(f"Clearing files from {folder_path}...")
        files_to_delete = os.listdir(folder_path)
        num_files = len(files_to_delete)
        for i, filename in enumerate(files_to_delete):
            file_path = os.path.join(folder_path, filename)
            if os.path.isfile(file_path):
                os.remove(file_path)
                self.log_message(f"Deleted {file_path}...")
                progress_value = int((i + 1) / num_files * 100)
                self.progress['value'] = progress_value

    def clear_training_inputs(self):
        request_result = self.custom_yes_no_cancel("Empty Volatile Storage", "Would you like to clear model inputs for a new training cycle?", yes_text="Clear Images", no_text="Clear Annotations", cancel_text="Clear Both")
                        
        if request_result is True:
            self.clear_directory(LIBRARY_COPY_DIR)
        elif request_result is False:
            self.clear_directory(ANNOTATIONS_DIR)
        elif request_result is None:
            self.clear_directory(LIBRARY_COPY_DIR)
            self.clear_directory(ANNOTATIONS_DIR)
        elif request_result == "closed":
            return

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()