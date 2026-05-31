# LitMus — Local Academic Literature Synthesis Workplace

LitMus is a secure, 100% local desktop application designed to distill complex academic research papers into structured, publication-ready literature reviews. Powered entirely by Ollama and the `llama3.2` architecture, LitMus processes your files fully offline—requiring zero API keys, zero internet access, and costing nothing.

---

##  Key Features

* **Complete Privacy & Isolation:** Runs entirely on your local machine. No external packets leak, and your research data never touches a third-party cloud.
* **Smart Text Extraction:** Drag, drop, or map standard documentation payloads, including PDF, DOCX, TXT, and MD files.
* **Advanced Synthesis Matrix:** Automatically generates a cohesive, scholarly narrative (~500 words) paired with an isolated 5-part comparative table mapping:
  * Background
  * Objectives
  * Methodological Approach
  * Primary Outcomes / Key Findings
  * System Gaps
* **Built-in PDF & Text Compiler:** Copy the raw payload directly to your clipboard or compile the structured layout into a clean, formatted vector PDF report.

---

##  System Architecture & Prerequisites

LitMus acts as a native execution layer over an isolated local background service daemon.

* **Engine:** Ollama (Service automated on launch if missing)
* **Model Context:** `llama3.2` (~2GB architecture)
* **Minimum RAM Baseline:** 8GB System RAM (16GB recommended)
* **Storage Footprint:** ~5GB free space allocated for local model weights

---

##  Installation & Setup

### Running from Source
1. Clone this repository.
2. Ensure Python 3.x is installed.
3. Launch `litmus.py`. The application will silently handle internal dependencies (`PyPDF2`, `python-docx`, `fpdf2`) on its first lifecycle setup.

### Compiling into a Standalone Executable
If you prefer a standalone executable (`.exe`), run the provided automation layer sequence:
```cmd
build_exe.bat
