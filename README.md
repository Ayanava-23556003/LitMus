# LitMus — Local Academic Literature Summarization Tool

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.20478557.svg)](https://doi.org/10.5281/zenodo.20478557)

**LitMus** is a secure, 100% offline desktop application built with Python and Tkinter designed for academic research analysts, students, and scholars. By leveraging local inference, LitMus allows you to distill dense scientific papers, articles, and manuscripts into high-quality, structured academic briefs with **zero API keys, zero internet dependencies, and absolute data privacy**.

---

##  Quick Start (Windows Executable)

For immediate deployment without needing a local Python configuration, download the pre-compiled standalone binary executable:

 **[Download LitMus.exe v1.0](https://github.com/Ayanava-23556003/LitMus/releases/download/v1.0/LitMus.exe)**

> **Deployment Note:** Target client machines do not require Python dependencies installed—simply launch the executable. It communicates natively with your local Ollama runtime environment.

---

##  Core Architectural Features

* **100% Local Intelligence Array:** Powered by an integrated **Ollama** backend running the ultra-efficient **Llama 3.2** (~2GB) model. Reading records, files, and generated text stay entirely sandboxed on your physical host machine—zero data packets are leaked.
* **Silent Dependency Bootstrapping:** On execution, the system dynamically verifies and imports essential parsing modules (`PyPDF2`, `python-docx`, `fpdf2`) without requiring manual pip overhead.
* **Robust Multi-Format Parsing:** Drag or load documentation artifacts straight into the staging environment. Supported formats include:
  * **PDF** Vector Data (`.pdf`)
  * **Word** Processing Documents (`.docx`)
  * **Plain Text** Arrays & Markdown (`.txt`, `.md`)
* **Automated System Setup Guardrail:** If the execution framework detects that Ollama or the required model weights are missing at launch, an intuitive **Setup UI Layer** triggers automatically. It manages the installer download, boots background service daemons, and pulls the necessary context layer frameworks seamlessly.

---

##  Structured Summary Engine (The Review Protocol)

LitMus enforces strict academic evaluation matrix yields rather than generic text shortening. The prompting backend restricts the local model to an explicit structural layout:

1. **Fully Paraphrased Narrative:** Completely rephrases content with an advanced, scholarly tone, avoiding verbatim source phrases.
2. **The 500-Word Continuous Block:** Synthesizes a unified paragraph detailing the *Background, Objectives, Methods, Key Findings,* and *Research Gaps* in chronological sequence—absent of bullet points or inline subheadings.
3. **The Comparative Evaluation Table:** Appends a clean, markdown-ready grid to the bottom of the output, mapping those same 5 key components into concise, 1-to-2 sentence summary cells for rapid parsing.

---

##  User Interface & Export Pipeline

* **Cyber-Academic Dark Palette:** Features a custom professional layout using deep navy backgrounds (`#0a1628`), custom graphics, and green system connectivity nodes for easy viewing over extended study sessions.
* **Export Pipeline:** * **Clipboard Mirroring:** "Copy Payload" maps raw formatting straight into your local system clipboard.
  * **Data Serialization:** "Save Text Data" exports clean plain text formatting (`.txt`).
  * **Structured PDF Layouts:** "Export Structured PDF" cross-compiles your narrative summary alongside an alternation-tinted, professional dual-column data table utilizing dynamic multi-page text constraints.
* **Buffer Loss Interception:** Closing windows trigger confirmation checks if an active unexported synthesis is held in system memory to prevent data loss.

---

##  Compilation & Manual Source Execution

### Running from Source
If running directly from the Python script, ensure you have Python 3.10+ installed and run:
```bash
python litmus.py
