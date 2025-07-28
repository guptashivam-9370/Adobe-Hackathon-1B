import os
import sys
import json
import datetime
from app.process_pdf import extract_structure_1b as extract_structure
from app.relevance_analyzer import RelevanceAnalyzer
# from app.summarizer import Summarizer
# app/query_builder.py
import nltk
# --- Hard-coded elaborations for known personas ---
PERSONA_INTERESTS = {
    "investment analyst": "This person is interested in financial data, tables, charts, growth metrics, market share, competitive analysis, and future outlook.",
    "phd researcher": "This person is interested in methodologies, experimental setup, datasets, results, benchmarks, citations, and prior work.",
    "travel planner": "This person is interested in activities, nightlife, entertainment, restaurants, budget options, transportation, and accommodation.",
    "student": "This person is interested in key concepts, definitions, summaries, and examples for exam preparation."
}
nltk.download('averaged_perceptron_tagger_eng')
def extract_keywords(text):
    """
    Extracts key nouns and verbs from a text string using NLTK.
    This serves as the dynamic fallback.
    """
    try:
        # Tokenize the text into words
        words = nltk.word_tokenize(text)
        # Tag words with their part of speech
        tagged_words = nltk.pos_tag(words)
        
        keywords = []
        for word, tag in tagged_words:
            # Filter for nouns (NN) and verbs (VB)
            if tag.startswith('NN') or tag.startswith('VB'):
                keywords.append(word.lower())
        
        # Return unique keywords
        return list(set(keywords))
        
    except Exception as e:
        print(f"NLTK keyword extraction failed: {e}. Returning empty list.")
        return []

def build_query(persona, job_to_be_done):
    """
    Builds an enhanced query using the hybrid approach.
    """
    persona_lower = persona.lower()
    
    # Start with a natural language base query
    base_query = f"A {persona} is trying to {job_to_be_done.lower()}"
    
    # --- The Hybrid Logic ---
    # 1. Try to find a pre-defined elaboration for the persona
    elaboration = PERSONA_INTERESTS.get(persona_lower)
    
    # 2. If not found, fall back to dynamic keyword extraction
    if not elaboration:
        print(f"Persona '{persona}' not found in dictionary. Falling back to dynamic keyword extraction.")
        keywords = extract_keywords(job_to_be_done)
        if keywords:
            elaboration = f"The key focus is on: {', '.join(keywords)}."
        else:
            elaboration = "" # No keywords found
            
    # Combine the parts into a final, rich query
    final_query = f"{base_query} {elaboration}".strip()
    
    print(f"\nGenerated Query: {final_query}")
    return final_query
def get_sections_from_pdf(pdf_path):
    """
    Uses the Round 1A processor to get structured sections with their full content.
    """
    try:
        structure = extract_structure(pdf_path) 
    except Exception as e:
        print(f"  - Error processing {os.path.basename(pdf_path)} with processor: {e}")
        return []

    sections = structure.get('outline', [])
    for section in sections:
        section['doc_name'] = os.path.basename(pdf_path)
        section['section_title'] = section.pop('text')
        section['page_num'] = section.pop('page')

    return sections

def perform_subsection_analysis(ranked_sections):
    """
    Populates the subsection analysis by extracting the full, original content
    from the top-ranked sections.
    """
    subsection_results = []
    top_sections = ranked_sections[:5]

    print("\nPerforming subsection analysis (extracting full content)...")
    for section in top_sections:
        subsection_results.append({
            "document": section["doc_name"],
            "refined_text": section.get("content", "Content not available."), # Use the full content
            "page_number": section["page_num"]
        })
    
    return subsection_results

def main():
    if len(sys.argv) < 2:
        print("Usage: python run_1b.py '<address of the collection directory>'")
        return
    
    collection_dir = sys.argv[1]
    input_json_file = os.path.join(collection_dir, "challenge1b_input.json")
    pdfs_dir = os.path.join(collection_dir, "PDFs")

    with open(input_json_file, 'r') as f:
        input_data = json.load(f)

    documents_to_process = input_data.get("documents", [])
    persona = input_data.get("persona", {}).get("role", "")
    job_to_be_done = input_data.get("job_to_be_done", {}).get("task", "")

    all_sections = []
    for doc_info in documents_to_process:
        filename = doc_info.get("filename")
        if filename:
            pdf_path = os.path.join(pdfs_dir, filename)
            if os.path.exists(pdf_path):
                print(f"  - Reading {filename}")
                all_sections.extend(get_sections_from_pdf(pdf_path))
    
    analyzer = RelevanceAnalyzer(model_path="./sbert_model")
    query = build_query(persona, job_to_be_done)
    
    ranked_sections = analyzer.analyze(query, all_sections)
    
    # --- This now uses the simpler, correct logic ---
    subsection_details = perform_subsection_analysis(ranked_sections)

    output_filename = os.path.join(collection_dir, "challenge1b_22_output.json")
    output_data = {
        "metadata": {
            "input_documents": [d.get("filename") for d in documents_to_process],
            "persona": persona, "job_to_be_done": job_to_be_done,
            "processing_timestamp": datetime.datetime.now().isoformat()
        },
        "extracted_sections": [],
        "subsection_analysis": subsection_details
    }
    
    for i, section in enumerate(ranked_sections[:5]):
        output_data["extracted_sections"].append({
            "document": section["doc_name"],
            "page_number": section["page_num"],
            "section_title": section["section_title"],
            "importance_rank": i + 1
        })
        
    with open(output_filename, "w") as f:
        json.dump(output_data, f, indent=4)
        
    print(f"\nAnalysis complete. Output saved to {output_filename}")

if __name__ == "__main__":
    main()