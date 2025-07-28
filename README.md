# Persona-Driven Document Intelligence

## Overview

This project is an intelligent document analysis pipeline that extracts, ranks, and analyzes the most relevant sections from a collection of PDF documents, tailored to a specific user persona and their job-to-be-done. It uses a hybrid query generation system, robust PDF parsing, and semantic relevance ranking powered by a fine-tuned SBERT model.

## Major Files & Directories

- `run_1b.py`: Main entry point. Orchestrates PDF processing, query building, relevance analysis, and output generation.
- `app/process_pdf.py`: Heuristic-based PDF processor. Extracts structured sections and their full content from PDFs.
- `app/relevance_analyzer.py`: Ranks sections by semantic relevance using SBERT and cosine similarity.
- `sbert_model/`: Contains the fine-tuned SBERT model and configuration files.
- `download_model.py`: Script to download required models and NLTK data for offline use.
- `Dockerfile`: Defines the containerized environment for reproducible, offline execution.
- `approach_explaination.md`: Detailed explanation of the methodology and pipeline stages.

## Steps to Run (Docker)

1. **Build the Docker Image**
   ```sh
   docker build -t persona-doc-intel .
   ```

2. **Run the Container**
   Replace `<collection_dir>` with the path to your input collection directory (containing `challenge1b_input.json` and a `PDFs/` folder).
   ```sh
   docker run --rm -v $(pwd):/app persona-doc-intel python run_1b.py "<collection_dir>"
   ```

   The output will be saved in the collection directory as `challenge1b_22_output.json`.

## Requirements

- Docker (recommended)
- Alternatively, Python 3.9+, `pip install -r requirements.txt`

## Notes

- All processing is offline and CPU-only.
- For local runs, ensure NLTK data and SBERT model are downloaded (handled by `download_model.py`).
- See [approach_explaination.md](approach_explaination.md) for methodology details.

---

For questions, see the code comments or [approach_explaination.md](approach_explaination.md).