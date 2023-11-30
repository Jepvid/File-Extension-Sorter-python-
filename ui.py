import os
import tkinter as tk
from tkinter import filedialog, messagebox
from threading import Thread
import subprocess
import sys

# Set the current working directory to the script's directory
script_directory = os.path.dirname(os.path.realpath(__file__))
os.chdir(script_directory)

# Function to stop the script
def stop_processing():
    stop_event.set()
    show_error_message("Stopping the script...")

def browse_source_folder():
    folder_path = filedialog.askdirectory()
    entry_source_path.delete(0, tk.END)
    entry_source_path.insert(0, folder_path)

def browse_destination_folder():
    folder_path = filedialog.askdirectory()
    entry_destination_path.delete(0, tk.END)
    entry_destination_path.insert(0, folder_path)

def show_error_message(message):
    messagebox.showerror("Error", message)

def start_processing():
    source_folder = entry_source_path.get()
    destination_folder = entry_destination_path.get()

    # Get the state of toggle buttons
    batch_mode = batch_var.get()
    use_symlink = spacesave_var.get()
    use_hardlink = spacesaveadmin_var.get()
    delete_source = delete_source_var.get()

    # Check for conflicting options
    if use_symlink and use_hardlink:
        show_error_message("Error: Cannot use -spacesave and -spacesaveadmin at the same time.")
        return

    # Get the path to the media-organizer.py script in the same folder as ui.py
    ui_folder = os.path.dirname(__file__)
    media_organizer_path = os.path.join(ui_folder, "organize-media.py")

    # Construct the command based on toggle states
    command = [
        sys.executable,
        f'"{media_organizer_path}"',  # Enclose in double quotes
        f'"{source_folder}"',           # Enclose in double quotes
        f'"{destination_folder}"',      # Enclose in double quotes
    ]
    if batch_mode:
        command.append("-batch")
    if use_symlink:
        command.append("-spacesave")
    if use_hardlink:
        command.append("-spacesaveadmin")
    if delete_source:
        command.append("-delete_source")

    # Run your script in a separate thread to avoid blocking the UI
    def run_script():
        subprocess.run(" ".join(command), shell=True)

    # Start a new thread to run the script
    script_thread = Thread(target=run_script)
    script_thread.start()

# Create the main window
root = tk.Tk()
root.title("Media Organizer")

# Create and place widgets
label_source_path = tk.Label(root, text="Source Folder:")
label_source_path.grid(row=0, column=0, padx=10, pady=10)

entry_source_path = tk.Entry(root, width=50)
entry_source_path.grid(row=0, column=1, padx=10, pady=10)

button_browse_source = tk.Button(root, text="Browse", command=browse_source_folder)
button_browse_source.grid(row=0, column=2, padx=10, pady=10)

label_destination_path = tk.Label(root, text="Destination Folder:")
label_destination_path.grid(row=1, column=0, padx=10, pady=10)

entry_destination_path = tk.Entry(root, width=50)
entry_destination_path.grid(row=1, column=1, padx=10, pady=10)

button_browse_destination = tk.Button(root, text="Browse", command=browse_destination_folder)
button_browse_destination.grid(row=1, column=2, padx=10, pady=10)

# Toggle buttons for optional arguments
batch_var = tk.BooleanVar()
batch_checkbutton = tk.Checkbutton(root, text="Batch Mode (-batch)", variable=batch_var)
batch_checkbutton.grid(row=2, column=0, columnspan=3, padx=10, pady=5, sticky=tk.W)

spacesave_var = tk.BooleanVar()
spacesave_checkbutton = tk.Checkbutton(root, text="Space Saving Mode (-spacesave)", variable=spacesave_var)
spacesave_checkbutton.grid(row=3, column=0, columnspan=3, padx=10, pady=5, sticky=tk.W)

spacesaveadmin_var = tk.BooleanVar()
spacesaveadmin_checkbutton = tk.Checkbutton(root, text="Space Saving Admin Mode (-spacesaveadmin)", variable=spacesaveadmin_var)
spacesaveadmin_checkbutton.grid(row=4, column=0, columnspan=3, padx=10, pady=5, sticky=tk.W)

delete_source_var = tk.BooleanVar()
delete_source_checkbox = tk.Checkbutton(root, text="Delete Source After Processing", variable=delete_source_var)
delete_source_checkbox.grid(row=5, column=0, columnspan=3, padx=10, pady=5, sticky=tk.W)

button_start = tk.Button(root, text="Start Processing", command=start_processing)
button_start.grid(row=6, column=0, columnspan=3, pady=10)


# Start the main loop
root.mainloop()
