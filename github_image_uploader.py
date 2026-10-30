import os
import base64
import hashlib
import threading
import time
import requests
import tkinter as tk

from tkinter import filedialog, messagebox, ttk

from PIL import Image
from pillow_heif import register_heif_opener


# Enable HEIC/HEIF support in Pillow
register_heif_opener()


GITHUB_API = "https://api.github.com"

# GitHub Contents API is not suitable for very large files.
# 100 MB is the hard upper limit for a single file through
# the Contents API, but keeping this lower gives safer uploads.
MAX_FILE_SIZE = 90 * 1024 * 1024

# Files that will get a JPG preview when they are HEIC/HEIF.
HEIC_EXTENSIONS = {
    ".heic",
    ".heif"
}


class GitHubUploader:

    def __init__(self, root):

        self.root = root

        self.root.title(
            "GitHub Private Media Uploader"
        )

        self.root.geometry(
            "850x750"
        )

        self.root.minsize(
            750,
            650
        )

        self.selected_folders = []

        self.keep_heic = tk.BooleanVar(
            value=True
        )

        self.create_gui()

    # =========================================================
    # GUI
    # =========================================================

    def create_gui(self):

        title = tk.Label(
            self.root,
            text="GitHub Private Media Uploader",
            font=("Segoe UI", 20, "bold")
        )

        title.pack(
            pady=15
        )

        # -----------------------------------------------------
        # GitHub Username
        # -----------------------------------------------------

        tk.Label(
            self.root,
            text="GitHub Username"
        ).pack(
            anchor="w",
            padx=30
        )

        self.username_entry = tk.Entry(
            self.root,
            width=80
        )

        self.username_entry.pack(
            padx=30,
            pady=5
        )

        # -----------------------------------------------------
        # Repository
        # -----------------------------------------------------

        tk.Label(
            self.root,
            text="Private Repository Name"
        ).pack(
            anchor="w",
            padx=30
        )

        self.repo_entry = tk.Entry(
            self.root,
            width=80
        )

        self.repo_entry.pack(
            padx=30,
            pady=5
        )

        # -----------------------------------------------------
        # Token
        # -----------------------------------------------------

        tk.Label(
            self.root,
            text="GitHub Personal Access Token"
        ).pack(
            anchor="w",
            padx=30
        )

        self.token_entry = tk.Entry(
            self.root,
            width=80,
            show="*"
        )

        self.token_entry.pack(
            padx=30,
            pady=5
        )

        # -----------------------------------------------------
        # HEIC option
        # -----------------------------------------------------

        self.heic_checkbox = tk.Checkbutton(
            self.root,
            text=(
                "Keep original HEIC file "
                "and also create a JPG preview"
            ),
            variable=self.keep_heic
        )

        self.heic_checkbox.pack(
            anchor="w",
            padx=30,
            pady=10
        )

        # -----------------------------------------------------
        # Folder selection
        # -----------------------------------------------------

        button_frame = tk.Frame(
            self.root
        )

        button_frame.pack(
            pady=10
        )

        tk.Button(
            button_frame,
            text="Select Folder",
            width=22,
            command=self.select_folder
        ).pack(
            side="left",
            padx=5
        )

        tk.Button(
            button_frame,
            text="Clear Folders",
            width=22,
            command=self.clear_folders
        ).pack(
            side="left",
            padx=5
        )

        # -----------------------------------------------------
        # Selected folders
        # -----------------------------------------------------

        tk.Label(
            self.root,
            text="Selected Folders"
        ).pack(
            anchor="w",
            padx=30
        )

        self.folder_list = tk.Listbox(
            self.root,
            height=7,
            width=105
        )

        self.folder_list.pack(
            padx=30,
            pady=5,
            fill="x"
        )

        # -----------------------------------------------------
        # Progress
        # -----------------------------------------------------

        tk.Label(
            self.root,
            text="Upload Progress"
        ).pack(
            anchor="w",
            padx=30,
            pady=(15, 0)
        )

        self.progress = ttk.Progressbar(
            self.root,
            orient="horizontal",
            length=750,
            mode="determinate"
        )

        self.progress.pack(
            padx=30,
            pady=5,
            fill="x"
        )

        # -----------------------------------------------------
        # Status
        # -----------------------------------------------------

        self.status_label = tk.Label(
            self.root,
            text="Ready",
            anchor="w"
        )

        self.status_label.pack(
            fill="x",
            padx=30,
            pady=5
        )

        # -----------------------------------------------------
        # Upload button
        # -----------------------------------------------------

        self.upload_button = tk.Button(
            self.root,
            text="UPLOAD TO PRIVATE GITHUB",
            command=self.start_upload,
            width=35,
            height=2,
            font=("Segoe UI", 11, "bold")
        )

        self.upload_button.pack(
            pady=15
        )

        # -----------------------------------------------------
        # Log
        # -----------------------------------------------------

        tk.Label(
            self.root,
            text="Upload Log"
        ).pack(
            anchor="w",
            padx=30
        )

        self.log_text = tk.Text(
            self.root,
            height=12,
            width=105
        )

        self.log_text.pack(
            padx=30,
            pady=5,
            fill="both",
            expand=True
        )

    # =========================================================
    # Folder Selection
    # =========================================================

    def select_folder(self):

        folder = filedialog.askdirectory(
            title="Select folder to upload"
        )

        if not folder:
            return

        folder = os.path.abspath(
            folder
        )

        if folder in self.selected_folders:

            messagebox.showinfo(
                "Already Selected",
                "This folder has already been selected."
            )

            return

        self.selected_folders.append(
            folder
        )

        self.folder_list.insert(
            tk.END,
            folder
        )

        self.log(
            f"Selected: {folder}"
        )

    # =========================================================
    # Clear Folders
    # =========================================================

    def clear_folders(self):

        self.selected_folders.clear()

        self.folder_list.delete(
            0,
            tk.END
        )

        self.log(
            "Folder selection cleared."
        )

    # =========================================================
    # Logging
    # =========================================================

    def log(self, message):

        self.root.after(
            0,
            self._write_log,
            message
        )

    def _write_log(self, message):

        self.log_text.insert(
            tk.END,
            message + "\n"
        )

        self.log_text.see(
            tk.END
        )

    # =========================================================
    # Status
    # =========================================================

    def set_status(self, message):

        self.root.after(
            0,
            lambda: self.status_label.config(
                text=message
            )
        )

    # =========================================================
    # Start Upload
    # =========================================================

    def start_upload(self):

        username = (
            self.username_entry
            .get()
            .strip()
        )

        repo = (
            self.repo_entry
            .get()
            .strip()
        )

        token = (
            self.token_entry
            .get()
            .strip()
        )

        if not username:

            messagebox.showerror(
                "Missing Information",
                "Enter your GitHub username."
            )

            return

        if not repo:

            messagebox.showerror(
                "Missing Information",
                "Enter your private repository name."
            )

            return

        if not token:

            messagebox.showerror(
                "Missing Information",
                "Enter your GitHub Personal Access Token."
            )

            return

        if not self.selected_folders:

            messagebox.showerror(
                "No Folder Selected",
                "Select at least one folder."
            )

            return

        self.upload_button.config(
            state="disabled"
        )

        self.progress["value"] = 0

        thread = threading.Thread(
            target=self.upload_files,
            args=(
                username,
                repo,
                token
            ),
            daemon=True
        )

        thread.start()

    # =========================================================
    # Get All Files
    # =========================================================

    def collect_files(self):

        files = []

        for selected_folder in self.selected_folders:

            selected_folder = os.path.abspath(
                selected_folder
            )

            parent_folder = os.path.dirname(
                selected_folder
            )

            for root, directories, filenames in os.walk(
                selected_folder
            ):

                # Ignore common temporary/system folders
                directories[:] = [
                    d for d in directories
                    if d not in {
                        ".git",
                        "__pycache__",
                        "node_modules"
                    }
                ]

                for filename in filenames:

                    local_path = os.path.join(
                        root,
                        filename
                    )

                    relative_path = os.path.relpath(
                        local_path,
                        parent_folder
                    )

                    github_path = relative_path.replace(
                        "\\",
                        "/"
                    )

                    files.append(
                        (
                            local_path,
                            github_path
                        )
                    )

        return files

    # =========================================================
    # Upload Everything
    # =========================================================

    def upload_files(
        self,
        username,
        repo,
        token
    ):

        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2026-03-10"
        }

        try:

            # -------------------------------------------------
            # Test repository
            # -------------------------------------------------

            self.set_status(
                "Checking GitHub repository..."
            )

            repository_url = (
                f"{GITHUB_API}/repos/"
                f"{username}/{repo}"
            )

            response = requests.get(
                repository_url,
                headers=headers,
                timeout=30
            )

            if response.status_code != 200:

                self.show_error(
                    "Could not access the repository.\n\n"
                    f"HTTP Status: "
                    f"{response.status_code}\n\n"
                    f"{response.text}"
                )

                return

            self.log(
                "GitHub repository connection successful."
            )

            # -------------------------------------------------
            # Collect files
            # -------------------------------------------------

            self.set_status(
                "Scanning selected folders..."
            )

            files = self.collect_files()

            if not files:

                self.show_error(
                    "No files were found."
                )

                return

            self.log(
                f"Found {len(files)} file(s)."
            )

            self.progress["maximum"] = len(files)

            uploaded = 0
            skipped = 0
            failed = 0

            # -------------------------------------------------
            # Process each file
            # -------------------------------------------------

            for index, (
                local_path,
                github_path
            ) in enumerate(
                files,
                start=1
            ):

                filename = os.path.basename(
                    local_path
                )

                extension = os.path.splitext(
                    filename
                )[1].lower()

                self.set_status(
                    f"Processing {index}/{len(files)}: "
                    f"{filename}"
                )

                # ---------------------------------------------
                # Check file size
                # ---------------------------------------------

                file_size = os.path.getsize(
                    local_path
                )

                size_mb = (
                    file_size /
                    (1024 * 1024)
                )

                if file_size > MAX_FILE_SIZE:

                    self.log(
                        f"SKIPPED: {github_path}"
                    )

                    self.log(
                        f"File size: "
                        f"{size_mb:.2f} MB"
                    )

                    self.log(
                        "This file is too large for "
                        "this uploader."
                    )

                    skipped += 1

                    self.update_progress(
                        index
                    )

                    continue

                # ---------------------------------------------
                # HEIC
                # ---------------------------------------------

                if extension in HEIC_EXTENSIONS:

                    # Upload original HEIC
                    if self.keep_heic.get():

                        success = (
                            self.upload_single_file(
                                username,
                                repo,
                                github_path,
                                local_path,
                                headers
                            )
                        )

                        if success:

                            uploaded += 1

                        else:

                            failed += 1

                    # Create JPG preview
                    jpg_path = (
                        self.convert_heic_to_jpg(
                            local_path
                        )
                    )

                    if jpg_path:

                        jpg_github_path = (
                            os.path.splitext(
                                github_path
                            )[0]
                            + ".jpg"
                        )

                        self.log(
                            f"Creating JPG preview: "
                            f"{jpg_github_path}"
                        )

                        success = (
                            self.upload_single_file(
                                username,
                                repo,
                                jpg_github_path,
                                jpg_path,
                                headers
                            )
                        )

                        if success:

                            uploaded += 1

                        else:

                            failed += 1

                        # Delete temporary JPG
                        try:

                            os.remove(
                                jpg_path
                            )

                        except Exception:
                            pass

                # ---------------------------------------------
                # Normal file
                # ---------------------------------------------

                else:

                    success = (
                        self.upload_with_retry(
                            username,
                            repo,
                            github_path,
                            local_path,
                            headers
                        )
                    )

                    if success:

                        uploaded += 1

                    else:

                        failed += 1

                self.update_progress(
                    index
                )

            # -------------------------------------------------
            # Finished
            # -------------------------------------------------

            self.set_status(
                "Upload completed."
            )

            self.log(
                "========================================"
            )

            self.log(
                "UPLOAD FINISHED"
            )

            self.log(
                f"Uploaded: {uploaded}"
            )

            self.log(
                f"Skipped: {skipped}"
            )

            self.log(
                f"Failed: {failed}"
            )

            self.log(
                "========================================"
            )

            self.root.after(
                0,
                lambda: messagebox.showinfo(
                    "Upload Complete",
                    (
                        "Upload process completed.\n\n"
                        f"Uploaded: {uploaded}\n"
                        f"Skipped: {skipped}\n"
                        f"Failed: {failed}"
                    )
                )
            )

        except Exception as error:

            self.show_error(
                str(error)
            )

        finally:

            self.root.after(
                0,
                lambda: self.upload_button.config(
                    state="normal"
                )
            )

    # =========================================================
    # Upload With Retry
    # =========================================================

    def upload_with_retry(
        self,
        username,
        repo,
        github_path,
        local_path,
        headers,
        retries=3
    ):

        for attempt in range(
            1,
            retries + 1
        ):

            success = (
                self.upload_single_file(
                    username,
                    repo,
                    github_path,
                    local_path,
                    headers
                )
            )

            if success:

                return True

            if attempt < retries:

                self.log(
                    f"Retrying "
                    f"{github_path} "
                    f"({attempt}/{retries})..."
                )

                time.sleep(2)

        return False

    # =========================================================
    # Upload Single File
    # =========================================================

    def upload_single_file(
        self,
        username,
        repo,
        github_path,
        local_path,
        headers
    ):

        try:

            with open(
                local_path,
                "rb"
            ) as file:

                file_data = file.read()

            encoded_content = (
                base64.b64encode(
                    file_data
                ).decode(
                    "utf-8"
                )
            )

            api_url = (
                f"{GITHUB_API}/repos/"
                f"{username}/{repo}/contents/"
                f"{github_path}"
            )

            # ---------------------------------------------
            # Check whether file already exists
            # ---------------------------------------------

            existing = requests.get(
                api_url,
                headers=headers,
                timeout=60
            )

            data = {
                "message": (
                    f"Upload {github_path}"
                ),
                "content": encoded_content
            }

            # ---------------------------------------------
            # Existing file
            # ---------------------------------------------

            if existing.status_code == 200:

                existing_data = (
                    existing.json()
                )

                existing_sha = (
                    existing_data.get(
                        "sha"
                    )
                )

                data["sha"] = existing_sha

                self.log(
                    f"Updating: {github_path}"
                )

            # ---------------------------------------------
            # New file
            # ---------------------------------------------

            elif existing.status_code == 404:

                self.log(
                    f"Uploading: {github_path}"
                )

            # ---------------------------------------------
            # Other response
            # ---------------------------------------------

            else:

                self.log(
                    f"Could not check existing file: "
                    f"{github_path}"
                )

            # ---------------------------------------------
            # Upload
            # ---------------------------------------------

            response = requests.put(
                api_url,
                headers=headers,
                json=data,
                timeout=180
            )

            if response.status_code in (
                200,
                201
            ):

                self.log(
                    f"SUCCESS: {github_path}"
                )

                return True

            # ---------------------------------------------
            # Handle conflict
            # ---------------------------------------------

            if response.status_code == 409:

                self.log(
                    f"Conflict detected: "
                    f"{github_path}"
                )

                return False

            self.log(
                f"FAILED {github_path}"
            )

            self.log(
                f"GitHub HTTP "
                f"{response.status_code}"
            )

            try:

                error_data = response.json()

                self.log(
                    str(
                        error_data.get(
                            "message",
                            response.text
                        )
                    )
                )

            except Exception:

                self.log(
                    response.text
                )

            return False

        except Exception as error:

            self.log(
                f"ERROR uploading "
                f"{github_path}: "
                f"{error}"
            )

            return False

    # =========================================================
    # Convert HEIC to JPG
    # =========================================================

    def convert_heic_to_jpg(
        self,
        heic_path
    ):

        try:

            image = Image.open(
                heic_path
            )

            # Convert images with transparency
            # to RGB before saving as JPG.
            if image.mode not in (
                "RGB",
                "L"
            ):

                image = image.convert(
                    "RGB"
                )

            jpg_path = (
                os.path.splitext(
                    heic_path
                )[0]
                + "_github_preview.jpg"
            )

            image.save(
                jpg_path,
                "JPEG",
                quality=95
            )

            image.close()

            return jpg_path

        except Exception as error:

            self.log(
                f"HEIC conversion failed: "
                f"{heic_path}"
            )

            self.log(
                str(error)
            )

            return None

    # =========================================================
    # Progress
    # =========================================================

    def update_progress(
        self,
        value
    ):

        self.root.after(
            0,
            lambda: self.progress.configure(
                value=value
            )
        )

    # =========================================================
    # Error Dialog
    # =========================================================

    def show_error(
        self,
        message
    ):

        self.set_status(
            "Error"
        )

        self.log(
            "ERROR: " + message
        )

        self.root.after(
            0,
            lambda: messagebox.showerror(
                "Error",
                message
            )
        )


# =============================================================
# Main
# =============================================================

if __name__ == "__main__":

    root = tk.Tk()

    app = GitHubUploader(
        root
    )

    root.mainloop()