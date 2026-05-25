# nlp_change_detector.py

import difflib
import re
from sentence_transformers import SentenceTransformer, util

# ==========================================
# NLP MODEL INITIALIZATION
# ==========================================
# We load the lightweight model for semantic comparison.
# 'all-MiniLM-L6-v2' is highly efficient and runs locally without needing a GPU.
print("Loading NLP Model (SentenceTransformers)... Please wait.")
nlp_model = SentenceTransformer('all-MiniLM-L6-v2')
print("Model loaded successfully.\n")

# (Make sure nlp_model is initialized at the top of your file as usual)

def hybrid_change_detector(old_text, new_text, semantic_threshold=0.95):
    """
    Compares two regulatory texts using a hybrid approach:
    Layer 1: Structural comparison (difflib)
    Layer 2: Semantic comparison (Cosine Similarity)
    Layer 3: Advanced Entity Override (Regex for digits, words-numbers, months, emails)
    """
    old_paragraphs = [p.strip() for p in old_text.split('\n\n') if len(p.strip()) > 10]
    new_paragraphs = [p.strip() for p in new_text.split('\n\n') if len(p.strip()) > 10]
    
    relevant_changes = []
    
    # Precompiled Regex patterns to search within the text
    month_pattern = r'\b(January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\b'
    word_num_pattern = r'\b(one|two|three|four|five|six|seven|eight|nine|ten|first|second|third)\b'
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    
    for new_p in new_paragraphs:
        # 1. EXACT MATCH FILTER (difflib layer)
        if new_p in old_paragraphs:
            continue
            
        # 2. FIND CLOSEST MATCH
        matches = difflib.get_close_matches(new_p, old_paragraphs, n=1, cutoff=0.3)
        
        if matches:
            old_p = matches[0]
            
            # --- SEMANTIC LAYER ---
            embedding_old = nlp_model.encode(old_p, convert_to_tensor=True)
            embedding_new = nlp_model.encode(new_p, convert_to_tensor=True)
            similarity_score = util.cos_sim(embedding_old, embedding_new).item()
            
            # --- ENTITY EXTRACTION LAYER (The Radar) ---
            # 1. Extract digits (0-9)
            digits_old = re.findall(r'\d+', old_p)
            digits_new = re.findall(r'\d+', new_p)
            
            # 2. Extract months (ignoring case)
            months_old = re.findall(month_pattern, old_p, re.IGNORECASE)
            months_new = re.findall(month_pattern, new_p, re.IGNORECASE)
            
            # 3. Extract numbers in text format (one, two...)
            word_nums_old = re.findall(word_num_pattern, old_p, re.IGNORECASE)
            word_nums_new = re.findall(word_num_pattern, new_p, re.IGNORECASE)
            
            # 4. Extract Emails
            emails_old = re.findall(email_pattern, old_p)
            emails_new = re.findall(email_pattern, new_p)
            
            # Trigger checks
            numbers_changed = (digits_old != digits_new) or (word_nums_old != word_nums_new)
            months_changed = (months_old != months_new)
            emails_changed = (emails_old != emails_new)
            
            # --- FINAL EVALUATION ---
            if similarity_score < semantic_threshold or numbers_changed or months_changed or emails_changed:
                
                # Intelligent classification of the change type
                if emails_changed:
                    change_type = "MODIFIED (Email Address Changed)"
                elif months_changed or numbers_changed:
                    change_type = "MODIFIED (Critical Dates/Numbers)"
                else:
                    change_type = "MODIFIED (Semantic Change)"
                
                relevant_changes.append({
                    "type": change_type,
                    "similarity": round(similarity_score, 4),
                    "old_text": old_p,
                    "new_text": new_p
                })
        else:
            # If no close match is found structurally, it is a completely new paragraph
            relevant_changes.append({
                "type": "ADDED",
                "similarity": 0.0,
                "old_text": None,
                "new_text": new_p
            })
            
    return relevant_changes

def extract_text_content(filepath):
    """Helper function to extract only the '=== TEXT CONTENT ===' part from a file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            if "=== TEXT CONTENT ===" in content and "=== ATTACHMENTS AND TRACKED LINKS ===" in content:
                return content.split("=== TEXT CONTENT ===")[1].split("=== ATTACHMENTS AND TRACKED LINKS ===")[0].strip()
            return content # Fallback if structure is missing
    except Exception as e:
        print(f"Error reading file {filepath}: {e}")
        return ""
          
    