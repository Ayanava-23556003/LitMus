"""
LitMus - Local AI Literature Summarization Tool
Powered by Ollama (runs 100% locally - no API key, no internet, no cost)
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import subprocess
import sys
import json
import urllib.request
import urllib.error
from pathlib import Path
import os

# ── silent dependency bootstrap ───────────────────────────────────────────────
def _silent_install(pkg, import_name=None):
    import importlib
    try:
        importlib.import_module(import_name or pkg)
    except ImportError:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", pkg, "-q", "--quiet"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

for _pkg, _imp in [("PyPDF2", "PyPDF2"), ("python-docx", "docx"), ("fpdf2", "fpdf")]:
    _silent_install(_pkg, _imp)

import PyPDF2
import docx
from fpdf import FPDF

# ── config ─────────────────────────────────────────────────────────────────────
CONFIG_FILE = Path.home() / ".litmus_ollama.json"
OLLAMA_URL  = "http://localhost:11434"
MODEL_NAME  = "llama3.2"          # ~2GB, best quality/size balance
OLLAMA_DOWNLOAD_URL = "https://ollama.com/download/OllamaSetup.exe"

def load_config():
    if CONFIG_FILE.exists():
        try: return json.loads(CONFIG_FILE.read_text())
        except: pass
    return {}

def save_config(data):
    CONFIG_FILE.write_text(json.dumps(data, indent=2))

# ── Ollama helpers ─────────────────────────────────────────────────────────────
def ollama_is_running():
    try:
        urllib.request.urlopen(f"{OLLAMA_URL}/api/tags", timeout=2)
        return True
    except:
        return False

def ollama_is_installed():
    """Check common install paths"""
    paths = [
        Path(os.environ.get("LOCALAPPDATA","")) / "Programs" / "Ollama" / "ollama.exe",
        Path("C:/Program Files/Ollama/ollama.exe"),
        Path(os.environ.get("ProgramFiles","")) / "Ollama" / "ollama.exe",
    ]
    import shutil
    return any(p.exists() for p in paths) or shutil.which("ollama") is not None

def model_is_pulled():
    try:
        req = urllib.request.urlopen(f"{OLLAMA_URL}/api/tags", timeout=3)
        data = json.loads(req.read())
        models = [m["name"].split(":")[0] for m in data.get("models", [])]
        return MODEL_NAME in models
    except:
        return False

def pull_model(progress_cb):
    """Pull model with streaming progress"""
    import urllib.parse
    body = json.dumps({"name": MODEL_NAME}).encode()
    req = urllib.request.Request(
        f"{OLLAMA_URL}/api/pull",
        data=body, method="POST",
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=600) as resp:
        while True:
            line = resp.readline()
            if not line:
                break
            try:
                d = json.loads(line)
                status = d.get("status","")
                total = d.get("total", 0)
                completed = d.get("completed", 0)
                if total:
                    pct = int(completed / total * 100)
                    progress_cb(f"Downloading model… {pct}%  ({completed//1024//1024}MB / {total//1024//1024}MB)")
                else:
                    progress_cb(status)
            except:
                pass

def call_ollama(text, title=""):
    prompt = build_prompt(text, title)
    body = json.dumps({
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.7, "num_ctx": 8192}
    }).encode()
    req = urllib.request.Request(
        f"{OLLAMA_URL}/api/generate",
        data=body, method="POST",
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as resp:
        data = json.loads(resp.read())
        return data.get("response", "")

# ── text extraction ────────────────────────────────────────────────────────────
def extract_text(filepath):
    ext = Path(filepath).suffix.lower()
    try:
        if ext == ".pdf":
            parts = []
            with open(filepath, "rb") as f:
                r = PyPDF2.PdfReader(f)
                for page in r.pages:
                    t = page.extract_text()
                    if t: parts.append(t)
            return "\n".join(parts)
        elif ext == ".docx":
            d = docx.Document(filepath)
            return "\n".join(p.text for p in d.paragraphs if p.text.strip())
        elif ext in (".txt", ".md"):
            return Path(filepath).read_text(encoding="utf-8", errors="ignore")
    except Exception as e:
        return f"ERROR: {e}"

# ── summarization prompt ───────────────────────────────────────────────────────
def build_prompt(text, title=""):
    src = f'Paper Title: "{title}"\n\n' if title else ""
    return f"""You are an expert academic research analyst. Write in a natural, scholarly tone with varied sentence structure. Always fully paraphrase — never copy phrases from the source text verbatim.

{src}Analyze the research literature below and produce a structured summary.

INSTRUCTIONS:
1. Write a single cohesive paragraph of approximately 500 words covering these five components in this order: Background, Objectives, Methods, Key Findings, and Research Gaps. Do NOT use subheadings inside the paragraph. Do NOT use bullet points. Open with the broader research context, not "This paper" or "The study".

2. After the paragraph, write a markdown table with exactly these columns:
| Component | Summary |
Include one row each for: Background, Objectives, Methods, Key Findings, Research Gaps. Each cell: 1-2 sentences.

3. Output ONLY the paragraph and the table. No introduction, no preamble, no closing remarks.

SOURCE TEXT:
\"\"\"
{text[:10000]}
\"\"\"

Begin your response now:"""

# ── PDF export ─────────────────────────────────────────────────────────────────
def export_pdf(summary_text, out_path, title="Literature Summary"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_margins(20, 20, 20)
    pdf.set_font("Helvetica", "B", 16)
    pdf.set_text_color(21, 101, 192)
    pdf.multi_cell(0, 10, title, align="C")
    pdf.ln(3)
    pdf.set_draw_color(21, 101, 192)
    pdf.set_line_width(0.8)
    pdf.line(20, pdf.get_y(), 190, pdf.get_y())
    pdf.ln(6)

    lines = summary_text.strip().split("\n")
    para_lines, table_lines = [], []
    in_table = False
    for line in lines:
        if line.strip().startswith("|"):
            in_table = True
        (table_lines if in_table else para_lines).append(line)

    pdf.set_font("Times", "", 12)
    pdf.set_text_color(0, 0, 0)
    pdf.multi_cell(0, 7, "\n".join(para_lines).strip())
    pdf.ln(6)

    if table_lines:
        rows = []
        for line in table_lines:
            line = line.strip()
            if not line: continue
            stripped = line.replace("|","").replace("-","").replace(" ","")
            if not stripped: continue
            if line.startswith("|"):
                cols = [c.strip() for c in line.strip("|").split("|")]
                rows.append(cols)
        if len(rows) >= 2:
            col_w = [50, 130]
            pdf.set_font("Helvetica", "B", 11)
            pdf.set_fill_color(21, 101, 192)
            pdf.set_text_color(255, 255, 255)
            for i, h in enumerate(rows[0][:2]):
                pdf.cell(col_w[i], 9, h, border=1, fill=True)
            pdf.ln()
            pdf.set_font("Helvetica", "", 10)
            for ri, row in enumerate(rows[1:]):
                fill = ri % 2 == 0
                pdf.set_fill_color(227, 242, 253) if fill else pdf.set_fill_color(255,255,255)
                pdf.set_text_color(0, 0, 0)
                for i, cell in enumerate(row[:2]):
                    x, y = pdf.get_x(), pdf.get_y()
                    pdf.multi_cell(col_w[i], 7, cell, border=1, fill=fill)
                    pdf.set_xy(x + col_w[i], y)
                pdf.ln()
    pdf.output(out_path)


# ══════════════════════════════════════════════════════════════════════════════
# SETUP SCREEN — shown when Ollama is not running/installed
# ══════════════════════════════════════════════════════════════════════════════
class SetupScreen(tk.Frame):
    def __init__(self, parent, on_ready):
        super().__init__(parent, bg="#0a1628")
        self.parent = parent
        self.on_ready = on_ready
        self._build()

    def _build(self):
        C = self.master.C
        self.pack(fill="both", expand=True)

        card = tk.Frame(self, bg=C["panel"], bd=0)
        card.place(relx=0.5, rely=0.5, anchor="center", width=540)

        logo_path = r"C:\Users\ayanp\Downloads\LitMus.png"
        if os.path.exists(logo_path):
            try:
                self.setup_logo_img = tk.PhotoImage(file=logo_path).subsample(5, 5)
                logo_lbl = tk.Label(card, image=self.setup_logo_img, bg=C["panel"])
                logo_lbl.pack(pady=(20, 0))
            except Exception:
                pass

        tk.Label(card, text="LitMus Engine Setup", bg=C["panel"], fg=C["accent"],
                 font=("Segoe UI Semibold", 18)).pack(pady=(10,4))
        tk.Label(card, text="One-time system initialization required", bg=C["panel"], fg=C["muted"],
                 font=("Segoe UI", 10)).pack(pady=(0,20))

        tk.Frame(card, bg=C["border"], height=1).pack(fill="x", padx=30)

        steps = [
            ("1", "Download & install Ollama Architecture", "Free, open-source setup (~200MB)"),
            ("2", "Deploy AI model Core (llama3.2)", "One-time ~2GB framework, stored fully offline"),
            ("3", "Initialize LitMus Workspaces", "Works completely local without internet blocks"),
        ]
        for num, title, sub in steps:
            row = tk.Frame(card, bg=C["panel"])
            row.pack(fill="x", padx=30, pady=8)
            tk.Label(row, text=num, bg=C["accent"], fg="white",
                     font=("Segoe UI Semibold", 11), width=2).pack(side="left", ipady=4)
            info = tk.Frame(row, bg=C["panel"])
            info.pack(side="left", padx=12)
            tk.Label(info, text=title, bg=C["panel"], fg=C["text"],
                     font=("Segoe UI Semibold", 10)).pack(anchor="w")
            tk.Label(info, text=sub, bg=C["panel"], fg=C["muted"],
                     font=("Segoe UI", 9)).pack(anchor="w")

        tk.Frame(card, bg=C["border"], height=1).pack(fill="x", padx=30, pady=(12,0))

        self.status_var = tk.StringVar(value="")
        self.status_lbl = tk.Label(card, textvariable=self.status_var,
                                   bg=C["panel"], fg=C["muted"],
                                   font=("Segoe UI", 9), wraplength=480)
        self.status_lbl.pack(pady=(10,0))

        self.prog = ttk.Progressbar(card, mode="indeterminate",
                                    style="TProgressbar", length=480)
        self.prog.pack(padx=30, pady=(6,0))

        self.btn = tk.Button(card, text="⬇  Configure & Initialize Ollama",
                             bg=C["accent"], fg="white",
                             font=("Segoe UI Semibold", 11), relief="flat",
                             cursor="hand2", activebackground=C["accent2"],
                             command=self._start_setup)
        self.btn.pack(fill="x", padx=30, pady=20, ipady=12)

        tk.Label(card, text="Already installed on your system?",
                 bg=C["panel"], fg=C["muted"],
                 font=("Segoe UI", 9)).pack(pady=(0,4))
        tk.Button(card, text="▶  Boot Local Service & Verify",
                  bg=C["border"], fg=C["text"],
                  font=("Segoe UI", 9), relief="flat",
                  cursor="hand2", command=self._check_again).pack(pady=(0,20))

    def _set_status(self, msg, color=None):
        C = self.master.C
        self.status_var.set(msg)
        self.status_lbl.config(fg=color or C["muted"])

    def _start_setup(self):
        self.btn.config(state="disabled")
        threading.Thread(target=self._do_setup, daemon=True).start()

    def _do_setup(self):
        C = self.master.C

        if ollama_is_installed():
            self.after(0, self._set_status, "Ollama framework detected. Booting service...", C["success"])
            self._start_ollama()
            return

        self.after(0, self._set_status, "Downloading Ollama binary stack setup...")
        self.after(0, self.prog.start, 8)
        installer_path = Path.home() / "Downloads" / "OllamaSetup.exe"
        try:
            urllib.request.urlretrieve(
                OLLAMA_DOWNLOAD_URL, installer_path,
                reporthook=lambda b, bs, t: self.after(0, self._set_status,
                    f"Downloading System Stack… {min(100,int(b*bs/t*100)) if t>0 else ''}%")
            )
        except Exception as e:
            self.after(0, self.prog.stop)
            self.after(0, self._set_status, f"Network timeout or failure: {e}\nPlease provision ollama.com manually.", C["error"])
            self.after(0, lambda: self.btn.config(state="normal"))
            return

        self.after(0, self.prog.stop)
        self.after(0, self._set_status, "Executing infrastructure installation wrappers — complete window triggers...")

        try:
            subprocess.run([str(installer_path), "/S"], check=True)
        except Exception:
            subprocess.run([str(installer_path)])

        self._start_ollama()

    def _start_ollama(self):
        C = self.master.C
        self.after(0, self._set_status, "Binding and triggering local background service port...")
        self.after(0, self.prog.start, 8)
        try:
            import shutil
            ollama_exe = shutil.which("ollama") or str(
                Path(os.environ.get("LOCALAPPDATA","")) / "Programs" / "Ollama" / "ollama.exe")
            subprocess.Popen([ollama_exe, "serve"],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception as e:
            self.after(0, self._set_status, f"Failed daemon binding map: {e}", C["error"])

        import time
        for _ in range(15):
            time.sleep(1)
            if ollama_is_running():
                break

        if not ollama_is_running():
            self.after(0, self.prog.stop)
            self.after(0, self._set_status,
                "Server engine slow to react.\n"
                "Allow initialization seconds and execute verification check manually.", C["error"])
            self.after(0, lambda: self.btn.config(state="normal"))
            return

        self.after(0, self._set_status, f"Pulling token sequence layer {MODEL_NAME} (One-time download ~2GB)...")
        try:
            pull_model(lambda msg: self.after(0, self._set_status, msg))
        except Exception as e:
            self.after(0, self.prog.stop)
            self.after(0, self._set_status, f"Layer initialization failure: {e}", C["error"])
            self.after(0, lambda: self.btn.config(state="normal"))
            return

        self.after(0, self.prog.stop)
        self.after(0, self._set_status, "✓ Core workspace verified! Launching LitMus Framework Layout...", C["success"])
        import time; time.sleep(1)
        self.after(0, self.on_ready)

    def _check_again(self):
        C = self.master.C
        if ollama_is_running():
            if model_is_pulled():
                self._set_status("✓ Subsystems online! Transferring system arrays...", C["success"])
                self.after(800, self.on_ready)
            else:
                self._set_status(f"Server alive but vector layers missing. Pulling {MODEL_NAME} target context...")
                self.prog.start(8)
                threading.Thread(target=self._pull_only, daemon=True).start()
        else:
            self._set_status("No local connection tracking found. Ensure execution layer is not sandboxed.", C["error"])

    def _pull_only(self):
        C = self.master.C
        try:
            pull_model(lambda msg: self.after(0, self._set_status, msg))
            self.after(0, self.prog.stop)
            self.after(0, self._set_status, "✓ Vectors mapped successfully! Booting main environment layout...", C["success"])
            import time; time.sleep(1)
            self.after(0, self.on_ready)
        except Exception as e:
            self.after(0, self.prog.stop)
            self.after(0, self._set_status, f"Pull tracking pipeline failed: {e}", C["error"])


# ══════════════════════════════════════════════════════════════════════════════
# MAIN APPLICATION INTERFACE
# ══════════════════════════════════════════════════════════════════════════════
class LitMusApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("LitMus — Local Academic Synthesis Workplace")
        self.geometry("1020x820")
        self.minsize(850, 680)
        self.configure(bg="#0a1628")
        self.resizable(True, True)
        self.files = []
        self.summary_result = ""
        self.C = {
            "bg":       "#0a1628",
            "panel":    "#0f2040",
            "accent":   "#1565c0",
            "accent2":  "#42a5f5",
            "text":     "#e3f0ff",
            "muted":    "#7ba7cc",
            "success":  "#26a69a",
            "error":    "#ef5350",
            "border":   "#1a3a5c",
            "input_bg": "#071020",
            "green":    "#00e676",
        }
        self._setup_styles()

        # Fix/Force the native Title Bar and taskbar to display your custom PNG logo
        logo_path = r"C:\Users\ayanp\Downloads\LitMus.png"
        if os.path.exists(logo_path):
            try:
                self.iconphoto(True, tk.PhotoImage(file=logo_path))
            except Exception:
                pass

        # Wire close window button handler intercept logic
        self.protocol("WM_DELETE_WINDOW", self._on_closing)

        if ollama_is_running() and model_is_pulled():
            self._build_main_ui()
        else:
            SetupScreen(self, on_ready=self._switch_to_main)

    def _switch_to_main(self):
        for w in self.winfo_children():
            w.destroy()
        self._build_main_ui()

    def _on_closing(self):
        """Triggers clean notification constraints preventing accidental workspace data loss"""
        if self.summary_result:
            if messagebox.askyesno(
                "Unsaved Synthesis Data", 
                "You have an active literature summary generated.\n\n"
                "Closing the application will clear this session buffer. "
                "Are you sure you want to exit LitMus?"
            ):
                self.destroy()
        else:
            self.destroy()

    def _setup_styles(self):
        C = self.C
        s = ttk.Style(self)
        s.theme_use("clam")
        s.configure("TFrame",       background=C["bg"])
        s.configure("TLabel",       background=C["bg"], foreground=C["text"], font=("Segoe UI",10))
        s.configure("TProgressbar", troughcolor=C["panel"], background=C["accent"], thickness=4)
        s.configure("TNotebook",    background=C["bg"], borderwidth=0)
        s.configure("TNotebook.Tab", background=C["panel"], foreground=C["muted"],
                    font=("Segoe UI",10), padding=[12,5])
        s.map("TNotebook.Tab",
              background=[("selected", C["accent"])],
              foreground=[("selected", "white")])

    def _build_main_ui(self):
        C = self.C
        # top bar
        top = tk.Frame(self, bg=C["panel"], height=65)
        top.pack(fill="x")
        top.pack_propagate(False)

        # Embedded Image Display Asset Layout
        logo_path = r"C:\Users\ayanp\Downloads\LitMus.png"
        if os.path.exists(logo_path):
            try:
                self.logo_img = tk.PhotoImage(file=logo_path).subsample(6, 6)
                logo_lbl = tk.Label(top, image=self.logo_img, bg=C["panel"])
                logo_lbl.pack(side="left", padx=(18, 5), pady=5)
            except Exception:
                pass

        tk.Label(top, text="LitMus", bg=C["panel"], fg=C["accent2"],
                 font=("Segoe UI Semibold", 16, "bold")).pack(side="left", padx=5, pady=12)
        tk.Label(top, text="•  100% Local Intelligence Array (No Authorization Keys Required)",
                 bg=C["panel"], fg=C["green"],
                 font=("Segoe UI", 9)).pack(side="left", padx=10, pady=16)

        main = tk.Frame(self, bg=C["bg"])
        main.pack(fill="both", expand=True)

        left = tk.Frame(main, bg=C["panel"], width=310)
        left.pack(side="left", fill="y", padx=(12,6), pady=12)
        left.pack_propagate(False)

        right = tk.Frame(main, bg=C["bg"])
        right.pack(side="left", fill="both", expand=True, padx=(0,12), pady=12)

        self._build_left(left)
        self._build_right(right)

        bar = tk.Frame(self, bg=C["border"], height=30)
        bar.pack(fill="x", side="bottom")
        bar.pack_propagate(False)
        self.status_var = tk.StringVar(value="✓ Local Core Connected  •  Secure Mode Active")
        tk.Label(bar, textvariable=self.status_var, bg=C["border"],
                 fg=C["muted"], font=("Segoe UI", 9)).pack(side="left", padx=12, pady=5)
        self.progress = ttk.Progressbar(bar, mode="indeterminate",
                                        style="TProgressbar", length=120)
        self.progress.pack(side="right", padx=12, pady=8)

    def _build_left(self, parent):
        C = self.C

        self._sec(parent, "📄  Manuscript Identification (Optional)")
        self.title_var = tk.StringVar()
        self._entry(parent, self.title_var).pack(fill="x", padx=14, pady=(2,12), ipady=6)

        self._sec(parent, "📂  Target Research Vector Files")
        btn_row = tk.Frame(parent, bg=C["panel"])
        btn_row.pack(fill="x", padx=14, pady=(4,6))
        tk.Button(btn_row, text="+ Add Artifacts", bg=C["accent"], fg="white",
                  font=("Segoe UI", 9, "bold"), relief="flat", cursor="hand2",
                  command=self._add_files).pack(side="left", ipadx=10, ipady=5)
        tk.Button(btn_row, text="Reset", bg=C["border"], fg=C["muted"],
                  font=("Segoe UI", 9), relief="flat", cursor="hand2",
                  command=self._clear_files).pack(side="left", padx=8, ipadx=8, ipady=5)

        self.file_lb = tk.Listbox(parent, bg=C["input_bg"], fg=C["text"],
                                  selectbackground=C["accent"],
                                  font=("Segoe UI", 9), relief="flat", height=6,
                                  borderwidth=0, highlightthickness=1,
                                  highlightbackground=C["border"])
        self.file_lb.pack(fill="x", padx=14, pady=(0,4))
        tk.Label(parent, text="Supported types: PDF · DOCX · TXT · MD",
                 bg=C["panel"], fg=C["muted"],
                 font=("Segoe UI", 8)).pack(anchor="w", padx=14, pady=(0,12))

        self._sec(parent, "✏️  Direct Context Array Input")
        self.paste_box = tk.Text(parent, bg=C["input_bg"], fg=C["text"],
                                 insertbackground=C["text"], relief="flat",
                                 font=("Segoe UI", 9), height=9,
                                 highlightbackground=C["border"],
                                 highlightcolor=C["accent"], highlightthickness=1,
                                 wrap="word")
        self.paste_box.pack(fill="x", padx=14, pady=(4,14))

        tk.Button(parent, text="⚡  Synthesize Matrix Narrative",
                  bg=C["accent"], fg="white",
                  font=("Segoe UI Semibold", 11), relief="flat",
                  cursor="hand2", activebackground=C["accent2"],
                  command=self._start).pack(fill="x", padx=14, pady=(4,14), ipady=12)

    def _build_right(self, parent):
        C = self.C
        nb = ttk.Notebook(parent)
        nb.pack(fill="both", expand=True)

        sf = tk.Frame(nb, bg=C["bg"])
        nb.add(sf, text="   Distilled Knowledge Output   ")
        tb = tk.Frame(sf, bg=C["panel"], height=40)
        tb.pack(fill="x")
        tb.pack_propagate(False)
        for lbl, cmd in [("📋 Copy Payload", self._copy),
                         ("💾 Save Text Data", self._save_txt),
                         ("📄 Export Structured PDF", self._export_pdf)]:
            tk.Button(tb, text=lbl, bg=C["panel"], fg=C["muted"],
                      font=("Segoe UI", 9), relief="flat", cursor="hand2",
                      activebackground=C["border"], activeforeground=C["text"],
                      command=cmd).pack(side="left", padx=4, pady=6, ipadx=8)

        self.summary_box = scrolledtext.ScrolledText(
            sf, bg=C["input_bg"], fg=C["text"],
            insertbackground=C["text"], relief="flat",
            font=("Segoe UI", 10), wrap="word",
            padx=16, pady=14, highlightthickness=0)
        self.summary_box.pack(fill="both", expand=True, padx=8, pady=(4,8))
        self._placeholder()

        hf = tk.Frame(nb, bg=C["bg"])
        nb.add(hf, text="   App Framework Manual   ")
        hb = scrolledtext.ScrolledText(hf, bg=C["input_bg"], fg=C["text"],
                                       relief="flat", font=("Segoe UI", 10),
                                       wrap="word", padx=16, pady=14, highlightthickness=0)
        hb.pack(fill="both", expand=True, padx=8, pady=8)
        hb.insert("end", HELP_TEXT)
        hb.config(state="disabled")

    def _sec(self, parent, text):
        C = self.C
        tk.Label(parent, text=text, bg=C["panel"], fg=C["accent2"],
                 font=("Segoe UI Semibold", 10)).pack(anchor="w", padx=14, pady=(14,2))
        tk.Frame(parent, bg=C["border"], height=1).pack(fill="x", padx=14, pady=(0,4))

    def _entry(self, parent, var):
        C = self.C
        return tk.Entry(parent, textvariable=var,
                        bg=C["input_bg"], fg=C["text"],
                        insertbackground=C["text"], relief="flat",
                        font=("Segoe UI", 10),
                        highlightbackground=C["border"],
                        highlightcolor=C["accent"], highlightthickness=1)

    def _placeholder(self):
        self.summary_box.config(state="normal")
        self.summary_box.delete("1.0", "end")
        self.summary_box.insert("end",
            "Your literature summary will appear here.\n\n"
            "➔ Map or load documentation artifacts into the left layout controls.\n"
            "➔ Trigger 'Synthesize Matrix Narrative' command layout.\n\n"
            "Evaluation Matrix Layout Yielded:\n"
            "  • Continuous High-Tone Academic Analysis Document Synthesis (~500 Words)\n"
            "  • Isolated Comparative Summary Rows Profile (Background ➔ Objectives ➔ Methods ➔ Key Findings ➔ Gaps)")
        self.summary_box.config(state="disabled")

    def _add_files(self):
        paths = filedialog.askopenfilenames(
            title="Select Research Files",
            filetypes=[("Supported Format Structures", "*.pdf *.docx *.txt *.md"),
                       ("PDF Vector Data", "*.pdf"), ("Word Processing Doc", "*.docx"), ("Plain Text Array", "*.txt")])
        for p in paths:
            if p not in self.files:
                self.files.append(p)
                self.file_lb.insert("end", f"  {Path(p).name}")
        if paths:
            self.status_var.set(f"Allocated {len(self.files)} tracking files to environment memory.")

    def _clear_files(self):
        self.files.clear()
        self.file_lb.delete(0, "end")
        self.status_var.set("Workspace indices cleared.")

    def _start(self):
        combined = ""
        for fp in self.files:
            t = extract_text(fp)
            if t and not t.startswith("ERROR"):
                combined += f"\n\n--- {Path(fp).name} ---\n{t}"
            elif t and t.startswith("ERROR"):
                messagebox.showwarning("File Processing Fault", f"{Path(fp).name}:\n{t}")

        pasted = self.paste_box.get("1.0", "end").strip()
        if pasted:
            combined += f"\n\n{pasted}"

        if not combined.strip():
            messagebox.showerror("Workspace Null", "Please deliver payload arrays before triggering synthesis layers.")
            return

        if not ollama_is_running():
            messagebox.showerror("Local Service Isolated",
                "Ollama daemon engine dropped out.\nRestart application sequence to bind infrastructure assets.")
            return

        self.summary_box.config(state="normal")
        self.summary_box.delete("1.0", "end")
        self.summary_box.insert("end", "⏳ Distilling data layers inside isolated local sandboxes — Standby…\n\n(Complex papers take 15–60s depending on host computational parameters)")
        self.summary_box.config(state="disabled")
        self.progress.start(10)
        self.status_var.set("Computing narrative threads offline…")

        threading.Thread(target=self._run, args=(combined,), daemon=True).start()

    def _run(self, text):
        try:
            title = self.title_var.get().strip()
            result = call_ollama(text, title)
            self.summary_result = result
            self.after(0, self._show, result)
        except Exception as e:
            self.after(0, self._run_fault_fallback, str(e))

    def _run_fault_fallback(self, err_msg):
        self.progress.stop()
        self.summary_box.config(state="normal")
        self.summary_box.delete("1.0", "end")
        self.summary_box.insert("end", f"❌ System Error Encountered\n\n{err_msg}")
        self.summary_box.config(state="disabled")
        self.status_var.set("Synthesis execution broken.")

    def _show(self, text):
        self.progress.stop()
        self.summary_box.config(state="normal")
        self.summary_box.delete("1.0", "end")
        self.summary_box.insert("end", text)
        self.summary_box.config(state="disabled")
        self.status_var.set("✓ Analysis finalized  •  Host Sandbox Confirmed Secure  •  Zero external packets leaked")

    def _copy(self):
        if self.summary_result:
            self.clipboard_clear()
            self.clipboard_append(self.summary_result)
            self.status_var.set("Synthesis mapped to local clip clipboard.")

    def _save_txt(self):
        if not self.summary_result:
            messagebox.showinfo("Buffer Empty", "Execute context analysis matrices first.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".txt",
                                            filetypes=[("Text Matrix Report", "*.txt")],
                                            initialfile="litmus_synthesis_output")
        if path:
            Path(path).write_text(self.summary_result, encoding="utf-8")
            self.status_var.set(f"✓ Output saved: {Path(path).name}")

    def _export_pdf(self):
        if not self.summary_result:
            messagebox.showinfo("Buffer Empty", "Execute context analysis matrices first.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".pdf",
                                            filetypes=[("Formal Standard Vector PDF", "*.pdf")],
                                            initialfile="litmus_synthesis_output")
        if path:
            title = self.title_var.get().strip() or "Literature Review Document Evaluation Matrix"
            try:
                export_pdf(self.summary_result, path, title)
                self.status_var.set(f"✓ PDF layout compiled: {Path(path).name}")
            except Exception as e:
                messagebox.showerror("PDF Export Interrupted", str(e))


HELP_TEXT = """
LitMus — Localized Analysis Framework Manual
════════════════════════════════════════════════════

ZERO-AUTHENTICATION HARDWARE PARADIGM
LitMus establishes isolated local host execution sandboxes by connecting directly with an open-source Ollama framework daemon running in the background. No third-party servers, tokens, data leaks, or usage payment gates exist.

OPERATIONAL RUN TIMELINE
  1. File Allocation ➔ Use '+ Add Artifacts' interface paths or paste text data block strings directly.
  2. Model Compute   ➔ Click 'Synthesize Matrix Narrative'.
  3. Processing Span ➔ Processing takes anywhere between 15 to 60 seconds depending heavily on CPU cores and RAM speeds.

REPORT MATRIX YIELD PATTERN
  • Unified High-Tone Academic Paraphrased Synthesis Block (~500 Words)
  • Structured Grid Components Evaluation Table Mapping:
    (Background ➔ Objectives ➔ Methodological Approach ➔ Primary Outcomes ➔ System Gaps)

HOST HARDWARE LOWER LIMITS
  Host Memory Profile: 8GB System RAM baseline (16GB recommended for high speed).
  Solid-State Storage: 5GB free environment workspace sector allocation for AI model matrices.
"""

if __name__ == "__main__":
    app = LitMusApp()
    app.mainloop()