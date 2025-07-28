# Approach Explanation for Persona-Driven Document Intelligence

## Overview

Our solution for the "Persona-Driven Document Intelligence" challenge is a multi-stage pipeline designed to function as an intelligent document analyst. The system extracts and prioritizes the most relevant sections from a collection of PDF documents based on a specific user persona and their job-to-be-done. Our approach prioritizes semantic accuracy, modularity, and strict adherence to all hackathon constraints, including offline execution, CPU-only performance, and size limitations.

## Methodology

The pipeline is broken down into four key stages:

**1. Robust Content Extraction:**
The foundation of our system is a sophisticated heuristic-based PDF processor developed in Task 1A. This module does not rely on any single attribute like font size; instead, it uses a combination of spatial clustering, pattern matching, and contextual analysis to accurately identify headings and segment documents. Crucially, it extracts the full, original text content associated with each heading, providing rich, complete sections for the subsequent analysis stages. This ensures that the relevance ranking is based on the complete context, not just titles.

**2. Persona-Aware Query Elaboration:**
To accurately capture the user's intent, we developed a hybrid query generation system. Instead of simply using the raw input, we create an enhanced query that provides deeper context to the language model.
* For known, common personas (e.g., "Investment Analyst," "HR Professional"), we use a dictionary of pre-defined "implicit interests" to add relevant keywords and concepts to the query.
* For unknown personas, the system gracefully falls back to a dynamic keyword extraction method using NLTK's part-of-speech tagging to identify the key nouns and verbs in the job description.
This hybrid approach makes our query system both powerful and highly adaptable.

**3. Semantic Relevance Ranking:**
The core of our relevance engine is the `all-MiniLM-L6-v2` sentence-transformer model. This model was chosen for its excellent balance of performance, speed, and small size (~80 MB), making it ideal for the hackathon's constraints.
* We generate a single embedding for the enhanced query.
* We then generate an embedding for the full content of every section extracted from the documents.
* Using **cosine similarity**, we calculate a relevance score for each section against the query. The sections are then ranked to populate the `extracted_sections` in the final output.

**4. Subsection Analysis via Direct Extraction:**
To fulfill the `subsection_analysis` requirement, our system takes the top-ranked sections and provides the detailed information that supports their high relevance score. The `refined_text` field is populated with the **full, original content** extracted from that section. This extractive approach guarantees that the output is factually grounded in the source documents and completely avoids the risk of model "hallucination," ensuring the user receives accurate and trustworthy information.

This combination of robust heuristic parsing and advanced, query-aware semantic analysis results in a fast, accurate, and highly relevant document intelligence system.
