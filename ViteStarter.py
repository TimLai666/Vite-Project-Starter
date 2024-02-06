import subprocess
import threading
import tkinter as tk
import os
import signal
import sys
from tkinter import messagebox, filedialog, simpledialog ,ttk, scrolledtext # 導入simpledialog


class ViteProjectStarter(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Vite Project Starter")
        self.geometry("400x600")  # 設定窗口大小
        self.process = None  # 保存專案進程的引用
        self.create_widgets()  # 創建 GUI 組件
        self.templates = ["vue", "react", "preact", "lit", "svelte", "vanilla"]
        self.protocol("WM_DELETE_WINDOW", self.on_closing)  # 設置關閉事件處理器

    def create_widgets(self):
        tk.Button(self, text="Create and Setup Vite Project", command=self.get_project_info).pack(pady=20)
        tk.Button(self, text="Build Vite Project", command=self.build_vite_project).pack(pady=10)
        self.run_stop_btn = tk.Button(self, text="Run Vite Project", command=self.run_stop_project)
        self.run_stop_btn.pack(pady=10)
        self.output_text = scrolledtext.ScrolledText(self, wrap=tk.WORD)
        self.output_text.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)

    def get_project_info(self):
        # Prompt for the project name
        project_name = simpledialog.askstring("Project Name", "Enter the project name:")
        if not project_name:
            messagebox.showwarning("Warning", "Project creation cancelled. No project name provided.")
            return

        # Create a new window to select a framework
        self.framework_window = tk.Toplevel(self)
        self.framework_window.title("Select a Framework")
        self.framework_window.geometry("300x100")

        tk.Label(self.framework_window, text="Select a Framework:").pack(pady=(10, 0))
        self.template_var = tk.StringVar(self.framework_window)

        # Make sure the templates list is defined before this point or directly include it here
        templates = ["vue", "react", "preact", "lit", "svelte", "vanilla"]

        template_dropdown = ttk.Combobox(self.framework_window, textvariable=self.template_var, values=templates, state="readonly")
        template_dropdown.pack()
        template_dropdown.set(templates[0])  # Default to first template

        tk.Button(self.framework_window, text="OK", command=lambda: self.setup_vite_project(project_name)).pack(pady=10)

    def setup_vite_project(self, project_name):
        template = self.template_var.get()
        self.framework_window.destroy()  # Close the framework selection window

        project_path = filedialog.askdirectory(title="Select the directory to create the Vite project in")
        if not project_path:
            messagebox.showinfo("Info", "Project creation cancelled. No directory selected.")
            return

        try:
            # Create Vite project
            subprocess.run(f"npm create vite@latest {project_name} -- --template {template}", shell=True, check=True, cwd=project_path)
            
            # Navigate into the project directory and install dependencies
            full_project_path = f"{project_path}/{project_name}"
            subprocess.run("npm install", shell=True, check=True, cwd=full_project_path)
            
            messagebox.showinfo("Success", f"Project '{project_name}' created with '{template}' template and dependencies installed.\n\nNow run:\n\n  cd {project_name}\n  npm run dev")
        except subprocess.CalledProcessError as e:
            messagebox.showerror("Error", f"Failed to setup Vite project: {str(e)}")

    def build_vite_project(self):
        project_path = filedialog.askdirectory(title="Select the Vite project directory to build")
        if project_path:
            try:
                subprocess.run('npm run build', shell=True, check=True, cwd=project_path)
                messagebox.showinfo("Success", "Vite project built successfully.")
            except subprocess.CalledProcessError as e:
                messagebox.showerror("Error", f"Failed to build Vite project: {str(e)}")

    def run_stop_project(self):
        if self.process:
            self.stop_project()
        else:
            self.run_project()

    def run_project(self):
        self.project_directory = filedialog.askdirectory(title="Select the Vite project directory to run")
        if not self.project_directory:
            messagebox.showinfo("Info", "Project run cancelled. No directory selected.")
            return
        
        try:
            self.run_stop_btn.config(text="Stop Vite Project")
            messagebox.showinfo("Info", "Vite project is running...")
            
            # 啟動專案並捕獲輸出
            self.process = subprocess.Popen('npm run dev', stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True, cwd=self.project_directory, text=True, bufsize=1, universal_newlines=True)
            
            # 在一個新線程中讀取輸出，以避免阻塞 GUI
            threading.Thread(target=self.read_output, daemon=True).start()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to run Vite project: {str(e)}")
            self.run_stop_btn.config(text="Run Vite Project")
    
    def read_output(self):
        """讀取子進程的輸出並將其顯示在 GUI 中。"""
        for line in self.process.stdout:
            self.append_text(line)
        self.process.stdout.close()
        self.process.wait()
        
        # 當進程結束時更新按鈕狀態
        self.run_stop_btn.config(text="Run Vite Project")
        self.append_text("\nVite project has been stopped.")
        self.process = None


    def stop_project(self):
        if self.process:
            self.terminate_process()
            self.process.wait()  # 等待進程終止
            self.process = None
            self.run_stop_btn.config(text="Run Vite Project")
            messagebox.showinfo("Info", "Vite project has been stopped.")

    def on_closing(self):
        if self.process:
            self.terminate_process()
            self.process.wait()  # 等待進程終止
        self.destroy()
    
    def terminate_process(self):
        if sys.platform == "win32":
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(self.process.pid)], check=True)
        elif sys.platform != "win32":
            os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)

    def append_text(self, text):
        # Ensure that changes to the Text widget are done in the main thread
        self.output_text.insert(tk.END, text)
        self.output_text.see(tk.END)  # Auto-scroll to the end


if __name__ == "__main__":
    app = ViteProjectStarter()
    app.mainloop()
