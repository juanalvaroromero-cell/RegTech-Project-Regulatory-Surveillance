# nlp_change_detector.py
import re
from sentence_transformers import util

def extract_text_content(filepath):
    """
    Simula la extracción de texto leyendo desde un archivo local,
    aísla únicamente el contenido normativo limpio.
    """
    with open(filepath, 'r', encoding='utf-8') as file:
        raw_content = file.read()
        
    if "=== TEXT CONTENT ===" in raw_content:
        text_block = raw_content.split("=== TEXT CONTENT ===")[1]
    else:
        text_block = raw_content
        
    if "=== ATTACHMENTS AND TRACKED LINKS ===" in text_block:
        text_block = text_block.split("=== ATTACHMENTS AND TRACKED LINKS ===")[0]
        
    return text_block.strip()

def hybrid_change_detector(old_paragraphs, new_paragraphs, model):
    relevant_changes = []
    
    if not old_paragraphs or not new_paragraphs:
        return relevant_changes 
        
    old_embeddings = model.encode(old_paragraphs, convert_to_tensor=True)
    new_embeddings = model.encode(new_paragraphs, convert_to_tensor=True)
    
    # Matriz de similitud
    cos_scores = util.cos_sim(old_embeddings, new_embeddings).tolist()
    
    # ==============================================================
    # 1. ALGORITMO DE ASIGNACIÓN EXCLUSIVA (Greedy Matching)
    # ==============================================================
    pairs = []
    for i in range(len(old_paragraphs)):
        for j in range(len(new_paragraphs)):
            pairs.append((i, j, cos_scores[i][j]))
            
    # Ordenamos de mayor a menor similitud
    pairs.sort(key=lambda x: x[2], reverse=True)
    
    matched_old = set()
    matched_new = set()
    final_matches = []
    
    for old_idx, new_idx, score in pairs:
        if old_idx not in matched_old and new_idx not in matched_new:
            # Solo emparejamos si la similitud es mínimamente razonable (> 0.50)
            if score >= 0.50:
                matched_old.add(old_idx)
                matched_new.add(new_idx)
                final_matches.append((old_idx, new_idx, score))
                
    # ==============================================================
    # 2. DETECCIÓN DE PÁRRAFOS BORRADOS (DELETED)
    # ==============================================================
    for i, old_p in enumerate(old_paragraphs):
        if i not in matched_old:
            relevant_changes.append({
                "type": "DELETED",
                "similarity": 0.0,
                "old_text": old_p,
                "new_text": "[PARAGRAPH COMPLETELY REMOVED FROM REGULATION]"
            })

    # ==============================================================
    # 3. DETECCIÓN DE AÑADIDOS, MODIFICADOS Y DESCARTES
    # ==============================================================
    for j, new_p in enumerate(new_paragraphs):
        if j not in matched_new:
            relevant_changes.append({
                "type": "ADDED",
                "similarity": 0.0,
                "old_text": "[NEW PARAGRAPH DETECTED]",
                "new_text": new_p
            })
        else:
            # Recuperamos su pareja asignada
            old_idx, score = next((o, s) for o, n, s in final_matches if n == j)
            best_old_p = old_paragraphs[old_idx]
            best_match_score = score
            
            if best_match_score < 0.999:
                
                # 1. REGEX FILTER 1: Critical Legal Subtlety
                legal_regex = r'\b(may|must|shall|should|will|cannot|can|required|optional)\b'
                old_legal = set(re.findall(legal_regex, best_old_p.lower()))
                new_legal = set(re.findall(legal_regex, new_p.lower()))
                
                # REGLA ESTRICTA: Debe superar el 0.90 de similitud matemática para que el Regex actúe
                has_legal_change = (old_legal != new_legal) and (best_match_score > 0.90)
                
                # 2. REGEX FILTER 2: Dates and Numbers
                num_regex = r'\b(\d+|one|two|three|four|five|six|seven|eight|nine|ten|january|february|march|april|june|july|august|september|october|november|december)\b'
                old_nums = set(re.findall(num_regex, best_old_p.lower()))
                new_nums = set(re.findall(num_regex, new_p.lower()))
                
                has_num_change = (old_nums != new_nums) and (best_match_score > 0.80)
                
                change_type = None
                
                if has_legal_change:
                    change_type = "MODIFIED (Critical Legal Modality)"
                elif has_num_change:
                    change_type = "MODIFIED (Critical Dates/Numbers)"
                else:
                    length_ratio = min(len(best_old_p), len(new_p)) / max(len(best_old_p), len(new_p))
                    
                    if best_match_score >= 0.60 and length_ratio > 0.80:
                        # TRAMPA SEMÁNTICA DESCARTADA
                        continue 
                    else:
                        change_type = "MODIFIED (Semantic Change)"
                
                relevant_changes.append({
                    "type": change_type,
                    "similarity": round(best_match_score, 4),
                    "old_text": best_old_p,
                    "new_text": new_p
                })
                
    return relevant_changes