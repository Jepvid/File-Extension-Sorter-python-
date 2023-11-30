import os
import shutil
from pathlib import Path
import sys
import threading
import argparse
import ctypes

def create_hard_link(source_path, destination_path):
    try:
        # Create a hard link
        ctypes.windll.kernel32.CreateHardLinkW(destination_path, source_path, 0)
        print(f"Hard link created: {source_path} to {destination_path}")
    except Exception as e:
        print(f"Error creating hard link for {source_path}: {e}")
        sys.exit(1)

def user_input_thread(stop_event):
    input("Press Enter to stop the script...")
    stop_event.set()

def copy_or_symlink_or_hardlink(source_path, destination_path, use_symlink, use_hardlink):
    try:
        if os.path.exists(destination_path):
            print(f"Skipped: File already exists at {destination_path}")
            return

        if use_hardlink:
            # Check if a hard link or file already exists, and skip if it does
            if os.path.islink(destination_path):
                print(f"Skipped: Symlink already exists at {destination_path}")
                return
            create_hard_link(source_path, destination_path)
        elif use_symlink:
            # Check if a symlink already exists, and skip if it does
            if os.path.islink(destination_path):
                print(f"Skipped: Symlink already exists at {destination_path}")
                return
            # Create a symbolic link
            os.symlink(source_path, destination_path, target_is_directory=os.path.isdir(source_path))
            print(f"Symlink created: {source_path} to {destination_path}")
        else:
            # Copy the file only if it doesn't already exist in the destination
            if os.path.exists(destination_path):
                print(f"Skipped: File already exists at {destination_path}")
                return
            shutil.copy2(source_path, destination_path)
            print(f"Copied: {source_path} to {destination_path}")

    except Exception as e:
        print(f"Error processing {source_path}: {e}")
        sys.exit(1)  # Exit with a non-zero code indicating an error


def copy_and_organize(source_folder, destination_folder, stop_event, batch_mode=False, use_symlink=False, use_hardlink=False, delete_source=False):
    # Create destination folder if it doesn't exist
    Path(destination_folder).mkdir(parents=True, exist_ok=True)

    # Find all unique extensions in the source folder
    media_extensions = set()
    for root, _, files in os.walk(source_folder):
        for file in files:
            _, extension = os.path.splitext(file)
            media_extensions.add(extension.lower())

    # Counters for the summary report
    total_files_processed = 0
    files_processed = 0
    files_skipped = 0
    file_type_counts = {}
    folders_processed = 0
    max_subfolder_depth = 0
    jobs_done = 0

    # Iterate through subfolders in the source folder
    if batch_mode:
        for subfolder in os.listdir(source_folder):
            subfolder_path = os.path.join(source_folder, subfolder)
            if os.path.isdir(subfolder_path):
                folders_processed += 1

                # Recursively walk through the current subfolder and its subfolders
                for root, _, files in os.walk(subfolder_path):
                    for file in files:
                        if stop_event.is_set():
                            print("Stopping the script...")
                            sys.exit(0)

                        total_files_processed += 1

                        source_path = os.path.join(root, file)

                        # Get the file extension (e.g., '.jpg')
                        _, extension = os.path.splitext(file)

                        # Create a folder for the specific file type if it doesn't exist
                        type_folder = os.path.join(destination_folder, subfolder, extension[1:].lower())
                        Path(type_folder).mkdir(parents=True, exist_ok=True)

                        # Build the destination path
                        destination_path = os.path.join(type_folder, file)

                        copy_or_symlink_or_hardlink(source_path, destination_path, use_symlink, use_hardlink)
                        files_processed += 1

                        # Count file type occurrences for the summary report
                        file_type_counts[extension] = file_type_counts.get(extension, 0) + 1

                # Update the maximum subfolder depth
                max_subfolder_depth = max(max_subfolder_depth, len(os.path.relpath(subfolder_path, source_folder).split(os.path.sep)))
                jobs_done += 1

    else:
        for root, _, files in os.walk(source_folder):
            for file in files:
                if stop_event.is_set():
                    print("Stopping the script...")
                    sys.exit(0)

                total_files_processed += 1

                source_path = os.path.join(root, file)

                # Get the file extension (e.g., '.jpg')
                _, extension = os.path.splitext(file)

                # Create a folder for the specific file type if it doesn't exist
                type_folder = os.path.join(destination_folder, extension[1:].lower())
                Path(type_folder).mkdir(parents=True, exist_ok=True)

                # Build the destination path
                destination_path = os.path.join(type_folder, file)

                copy_or_symlink_or_hardlink(source_path, destination_path, use_symlink, use_hardlink)
                files_processed += 1

                # Count file type occurrences for the summary report
                file_type_counts[extension] = file_type_counts.get(extension, 0) + 1

        # Update the maximum subfolder depth for single job mode
        max_subfolder_depth = 0

    # Summary Report
    print("\nSummary Report:")
    print(f"Total files processed: {total_files_processed}")
    print(f"Files processed: {files_processed}")
    print(f"Files skipped: {files_skipped} ({(files_skipped / total_files_processed) * 100:.2f}%)")
    print(f"Percentage of file types:")
    for ext, count in file_type_counts.items():
        percentage = (count / total_files_processed) * 100
        print(f"  {ext}: {count} files ({percentage:.2f}%)")
    print(f"Total folders processed: {folders_processed}")
    print(f"Maximum subfolder depth: {max_subfolder_depth}")
    print(f"Jobs done: {jobs_done}")

    # Delete source if specified (with double confirmation)
    if delete_source:
        confirmation = input(f"\nDo you really want to delete the source folder '{source_folder}'? (yes/no): ")
        if confirmation.lower() == "yes":
            confirmation = input("This action is irreversible. Type 'DELETE' to confirm: ")
            if confirmation.upper() == "DELETE":
                try:
                    shutil.rmtree(source_folder)
                    print(f"Source folder '{source_folder}' deleted.")
                except Exception as e:
                    print(f"Error deleting source folder '{source_folder}': {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Copy, symlink, or hardlink media files from source to destination.")
    parser.add_argument("source_folder", help="Path to the source folder")
    parser.add_argument("destination_folder", help="Path to the destination folder")
    parser.add_argument("-batch", action="store_true", help="Enable batch mode")
    parser.add_argument("-spacesave", action="store_true", help="Enable space-saving mode (symlinks)")
    parser.add_argument("-spacesaveadmin", action="store_true", help="Enable space-saving admin mode (hard links)")
    parser.add_argument("-input", help="Specify the input file or folder")
    parser.add_argument("-output", help="Specify the output folder")
    parser.add_argument("-delete_source", action="store_true", help="Delete the source folder when done (with confirmation)")

    args = parser.parse_args()

    source_folder = args.source_folder if not args.input else args.input
    destination_folder = args.destination_folder if not args.output else args.output

    copy_and_organize(
        source_folder,
        destination_folder,
        threading.Event(),
        batch_mode=args.batch,
        use_symlink=args.spacesave,
        use_hardlink=args.spacesaveadmin,
        delete_source=args.delete_source
    )
