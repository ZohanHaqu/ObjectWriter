import tkinter as tk
from tkinter import messagebox, scrolledtext, filedialog, simpledialog
from tkinter import ttk
import subprocess
import os
import sys
import threading

class ObjectWriterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ObjectWriter - Python Script Editor with Preview")
        self.current_file = None  # To track if a file has been saved

        # Set window icon (main window)
        self.root.iconbitmap('objectwriter.ico')

        # Text area for code input
        self.text_area = scrolledtext.ScrolledText(self.root, wrap='word', font=("Courier", 10), undo=True)
        self.text_area.pack(expand=True, fill='both')
        
        # Menu bar
        self.menu_bar = tk.Menu(self.root)
        self.root.config(menu=self.menu_bar)

        # File menu for opening/saving scripts
        self.file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="File", menu=self.file_menu)
        self.file_menu.add_command(label="Open", command=self.open_file)
        self.file_menu.add_command(label="Save", command=self.save_file)
        self.file_menu.add_command(label="Compile", command=self.compile_project)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Exit", command=self.exit_app)

        # Preview button using ttk
        self.preview_button = ttk.Button(self.root, text="Preview Output", command=self.preview_output)
        self.preview_button.pack(pady=5)

        # Code execution output area
        self.output_area = scrolledtext.ScrolledText(self.root, wrap='word', font=("Courier", 10), height=10)
        self.output_area.pack(expand=True, fill='both')

        # Insert sample code to start with
        self.sample_code = """# Sample Python Script
def greet(name):
    return f"Hello, {name}!"

print(greet('World'))"""
        self.text_area.insert('1.0', self.sample_code)

    def open_file(self):
        filepath = filedialog.askopenfilename(defaultextension=".py", filetypes=[("Python files", "*.py"), ("All files", "*.*")])
        if filepath:
            with open(filepath, 'r') as file:
                code = file.read()
            self.text_area.delete('1.0', tk.END)
            self.text_area.insert('1.0', code)
            self.current_file = filepath  # Set the current file path

    def save_file(self):
        filepath = filedialog.asksaveasfilename(defaultextension=".py", filetypes=[("Python files", "*.py"), ("All files", "*.*")])
        if filepath:
            code = self.text_area.get('1.0', tk.END)
            with open(filepath, 'w') as file:
                file.write(code)
            self.current_file = filepath  # Set the current file path

    def exit_app(self):
        self.root.quit()

    def preview_output(self):
        # Get the Python code from the text area
        code = self.text_area.get('1.0', tk.END)

        # Execute the Python code
        try:
            # Run the script and capture the output
            process = subprocess.Popen(
                ['python', '-c', code], 
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
                text=True
            )
            stdout, stderr = process.communicate()

            # Display the output or error in the output area
            if stderr:
                self.output_area.delete('1.0', tk.END)
                self.output_area.insert('1.0', f"Error:\n{stderr}")
            else:
                self.output_area.delete('1.0', tk.END)
                self.output_area.insert('1.0', f"Output:\n{stdout}")

        except Exception as e:
            messagebox.showerror("Execution Error", f"Error executing code: {e}")

    def compile_project(self):
        # Check if the project is saved
        if not self.current_file:
            messagebox.showerror("Save Error", "Save the project before compiling.")
            return

        # Open the Compile window
        compile_window = tk.Toplevel(self.root)
        compile_window.title("Compile Options")
        compile_window.iconbitmap('objectwriter.ico')  # Set the icon for the compile window

        # Option to use recommended PyInstaller command
        ttk.Label(compile_window, text="Choose compilation method:").pack(pady=10)
        
        # Button for recommended compilation
        recommend_button = ttk.Button(compile_window, text="Use Recommended PyInstaller Command", 
                                      command=lambda: self.run_recommended_compile(compile_window))
        recommend_button.pack(pady=5)

        # Button for custom PyInstaller command
        custom_button = ttk.Button(compile_window, text="Use Custom PyInstaller Command", 
                                   command=lambda: self.run_custom_compile(compile_window))
        custom_button.pack(pady=5)

        # Compile Location input (Folder selection)
        ttk.Label(compile_window, text="Select Compile Location:").pack(pady=10)
        self.compile_location = tk.StringVar()
        location_entry = ttk.Entry(compile_window, textvariable=self.compile_location, width=40)
        location_entry.pack(pady=5)

        # Button to choose folder location
        browse_button = ttk.Button(compile_window, text="Browse", command=lambda: self.select_compile_location(location_entry))
        browse_button.pack(pady=5)

    def select_compile_location(self, location_entry):
        # Ask the user to choose a folder for compilation output
        location = filedialog.askdirectory()
        if location:
            self.compile_location.set(location)  # Update the entry with the selected location

    def run_recommended_compile(self, compile_window):
        # Ensure PyInstaller is installed
        if not self.is_pyinstaller_installed():
            install_pyinstaller = messagebox.askyesno(
                "PyInstaller Not Found", 
                "PyInstaller is not installed. Do you want to install it?"
            )
            if install_pyinstaller:
                self.install_pyinstaller()
            else:
                compile_window.destroy()
                return

        # Get the current file path and compile location
        script_path = self.current_file  # Use the saved file path
        icon_path = filedialog.askopenfilename(filetypes=[("Icon files", "*.ico")])
        if not icon_path:
            icon_path = None

        compile_location = self.compile_location.get()
        if not compile_location:
            messagebox.showerror("Compile Location Error", "Please select a compile location.")
            compile_window.destroy()
            return

        # Build PyInstaller command
        command = f"pyinstaller --onefile --icon={icon_path} --name=ObjectWriter --distpath={compile_location} {script_path}"

        # Start compilation with progress bar and log
        self.start_compilation(command, compile_window)

        compile_window.protocol("WM_DELETE_WINDOW", lambda: None)  # Disable closing during compilation
        compile_window.grab_set()  # Keep compile window in focus while compiling
        compile_window.transient(self.root)  # Make compile window transient to main window
        compile_window.mainloop()

    def run_custom_compile(self, compile_window):
        # Custom PyInstaller command from the user
        custom_command = simpledialog.askstring(
            "Custom PyInstaller Command", 
            "Enter your custom PyInstaller command:"
        )
        if custom_command:
            self.start_compilation(custom_command, compile_window)

        compile_window.protocol("WM_DELETE_WINDOW", lambda: None)  # Disable closing during compilation
        compile_window.grab_set()  # Keep compile window in focus while compiling
        compile_window.transient(self.root)  # Make compile window transient to main window
        compile_window.mainloop()

    def is_pyinstaller_installed(self):
        try:
            subprocess.check_output(["pyinstaller", "--version"])
            return True
        except subprocess.CalledProcessError:
            return False

    def install_pyinstaller(self):
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
            messagebox.showinfo("Installation Complete", "PyInstaller has been successfully installed.")
        except subprocess.CalledProcessError as e:
            messagebox.showerror("Installation Failed", f"Failed to install PyInstaller: {e}")

    def start_compilation(self, command, compile_window):
        # Create the log area
        log_area = scrolledtext.ScrolledText(compile_window, wrap='word', height=10, width=60)
        log_area.pack(pady=10)

        # Create the progress bar
        progress_bar = ttk.Progressbar(compile_window, length=400, mode='indeterminate')
        progress_bar.pack(pady=10)
        progress_bar.start()  # Start the progress bar

        # Run the PyInstaller command in a separate thread
        def compile_thread():
            try:
                process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

                # Process the output and update the log area
                for stdout_line in iter(process.stdout.readline, ""):
                    if log_area.winfo_exists():
                        log_area.insert(tk.END, stdout_line)
                        log_area.yview(tk.END)
                for stderr_line in iter(process.stderr.readline, ""):
                    if log_area.winfo_exists():
                        log_area.insert(tk.END, stderr_line)
                        log_area.yview(tk.END)

                process.stdout.close()
                process.stderr.close()
                process.wait()

                if progress_bar.winfo_exists():
                    progress_bar.stop()  # Stop the progress bar
                messagebox.showinfo("Compilation Success", "Compilation finished successfully!")

            except Exception as e:
                if progress_bar.winfo_exists():
                    progress_bar.stop()
                messagebox.showerror("Compilation Error", f"Error during compilation: {e}")

        # Start the compile process in a new thread
        threading.Thread(target=compile_thread, daemon=True).start()

if __name__ == "__main__":
    root = tk.Tk()
    app = ObjectWriterApp(root)
    root.mainloop()
