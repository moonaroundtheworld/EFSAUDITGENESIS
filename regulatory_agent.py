import json
import os
from typing import List, Dict, Any, Optional

try:
    from database.models import upsert_transaction, log_audit_trail, log_regulatory_flag  # type: ignore
except ImportError:
    pass

KNOWLEDGE_DIR = os.path.join(os.path.dirname(__file__), 'knowledge')

def load_knowledge_base() -> Dict[str, List[Dict[str, Any]]]:
    isas_path = os.path.join(KNOWLEDGE_DIR, 'isas.json')
    companies_act_path = os.path.join(KNOWLEDGE_DIR, 'companies_act.json')
    
    knowledge: Dict[str, List[Dict[str, Any]]] = {"ISAs": [], "Companies_Act": []}
    
    if os.path.exists(isas_path):
        with open(isas_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            knowledge["ISAs"] = data.get("ISAs", [])
            
    if os.path.exists(companies_act_path):
        with open(companies_act_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            knowledge["Companies_Act"] = data.get("Pakistan_Companies_Act_2017", [])
            
    return knowledge

KNOWLEDGE = load_knowledge_base()

def evaluate_transaction_against_regulations(transaction: Dict[str, Any], client_id: Optional[int] = None) -> List[str]:
    flags: List[str] = []
    amount_str = transaction.get('amount') or transaction.get('Amount') or transaction.get('value', '0')
    try:
        amount = float(str(amount_str).replace(',', '').strip())
    except (ValueError, TypeError):
        amount = 0.0

    vendor = str(transaction.get('vendor_name') or transaction.get('Vendor') or transaction.get('vendor', '')).lower()
    date_str = str(transaction.get('date') or transaction.get('Date') or 'N/A')
    
    tx_id = None
    if client_id is not None:
        try:
            tx_id = upsert_transaction(client_id, amount, date_str, vendor, 'Regulatory Check', json.dumps(transaction))
        except Exception:
            pass

    if amount > 1000000 and ("cash" in vendor or vendor == ""):
        for ca in KNOWLEDGE.get("Companies_Act", []):
            if ca.get("section") == "Section 183":
                reason = f"[{ca['section']}]: {ca['title']}. {ca['description']}"
                flags.append(f"Regulatory Flag {reason}")
                if tx_id:
                    try:
                        log_regulatory_flag(tx_id, ca['section'], reason)
                        log_audit_trail(tx_id, "Regulatory Agent", reason)
                    except Exception:
                        pass
                
    if amount >= 50000 and amount % 10000 == 0:
        for isa in KNOWLEDGE.get("ISAs", []):
            if isa.get("standard") == "ISA 240":
                reason = f"[{isa['standard']}]: {isa['title']}. Large round numbers require elevated skepticism."
                flags.append(f"Audit Standard {reason}")
                if tx_id:
                    try:
                        log_regulatory_flag(tx_id, isa['standard'], reason)
                        log_audit_trail(tx_id, "Regulatory Agent", reason)
                    except Exception:
                        pass

    if "associated" in vendor or "related" in vendor or "subsidiary" in vendor:
         for ca in KNOWLEDGE.get("Companies_Act", []):
            if ca.get("section") == "Section 199":
                reason = f"[{ca['section']}]: {ca['title']}. Ensure special resolution exists for {vendor}."
                flags.append(f"Regulatory Flag {reason}")
                if tx_id:
                    try:
                        log_regulatory_flag(tx_id, ca['section'], reason)
                        log_audit_trail(tx_id, "Regulatory Agent", reason)
                    except Exception:
                        pass
                
    return flags

def get_regulatory_flags_for_dataset(data: List[Dict[str, Any]], client_id: Optional[int] = None) -> List[Dict[str, Any]]:
    regulatory_issues: List[Dict[str, Any]] = []
    for idx, row in enumerate(data):
        flags = evaluate_transaction_against_regulations(row, client_id)
        if flags:
            regulatory_issues.append({
                "row_index": idx + 1,
                "entry": row,
                "flags": flags
            })
            
    return regulatory_issues
