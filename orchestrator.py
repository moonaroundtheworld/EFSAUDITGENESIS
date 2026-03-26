import csv
import json
import os
import sys
import re
from datetime import datetime

from database.models import ensure_client, save_master_report  # type: ignore
from fraud_agent import analyze_benfords_law, identify_duplicates, detect_weekend_posting  # type: ignore
from agents.forensics import detect_circular_transactions, detect_ghost_entities  # type: ignore
from logic.synergy import SynergyManager  # type: ignore
from regulatory_agent import get_regulatory_flags_for_dataset  # type: ignore
from agents.inventory import analyze_inventory  # type: ignore
from agents.cash import analyze_cash_transactions  # type: ignore

class DataSanitizer:
    @staticmethod
    def clean(data):
        """Fixes common CSV formatting errors before processing"""
        cleaned = []
        for row in data:
            new_row = {}
            for k, v in row.items():  # type: ignore
                if not k or not v: continue
                val = str(v).strip()
                # Remove currency symbols from pure number fields
                if k.lower() in ['amount', 'unit_cost', 'nrv', 'selling_price', 'cost', 'qty', 'quantity']:
                    val = re.sub(r'[^\d.-]', '', val)
                    if not val: val = '0'
                # Attempt to normalize dates (MM/DD/YYYY to YYYY-MM-DD or retain original)
                elif k.lower() in ['date', 'last_sale_date']:
                    try:
                        if '/' in val:
                            parts = val.split('/')
                            if len(parts) == 3:
                                d = datetime(int(parts[2]), int(parts[0]), int(parts[1]))
                                val = d.strftime('%Y-%m-%d')
                    except Exception:
                        pass
                new_row[k.lower()] = val
            cleaned.append(new_row)
        return cleaned

class LeadAuditorOrchestrator:
    def __init__(self, client_name: str):
        self.client_name = client_name
        self.client_id = ensure_client(client_name)
        
    def execute_audit(self, filepath: str):
        raw_data = []
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                raw_data.append(row)
                
        print(f"Orchestrator running cleaning layer across {len(raw_data)} records...")
        clean_data = DataSanitizer.clean(raw_data)
        
        print("Dispatching data to Audit Agent Fleet in parallel logic...")
        
        # Fraud Agent (Includes Advanced Pattern Detection)
        benford = analyze_benfords_law(clean_data)
        duplicates = identify_duplicates(clean_data, self.client_id)
        weekend_holidays = detect_weekend_posting(clean_data, self.client_id)
        
        # Forensics Agent
        circular_tx = detect_circular_transactions(clean_data, self.client_id)
        ghost_entities = detect_ghost_entities(clean_data, self.client_id)
        
        # Regulatory Agent
        regulatory = get_regulatory_flags_for_dataset(clean_data, self.client_id)
        
        # Inventory Agent
        inventory = analyze_inventory(clean_data, self.client_id)
        
        # Cash Agent
        cash = analyze_cash_transactions(clean_data, self.client_id)
        
        # Consolidate into Risk Heatmap
        risk_heatmap = {
            "client": self.client_name,
            "total_records_analyzed": len(clean_data),
            "fraud_patterns": {
                "benfords_law": benford,
                "duplicates": duplicates,
                "weekend_holiday_postings": weekend_holidays
            },
            "forensics_alerts": {
                "circular_transactions": circular_tx,
                "ghost_entities": ghost_entities
            },
            "regulatory_flags": regulatory,
            "inventory_valuation": inventory,
            "cash_aml_metrics": cash
        }
        
        # Synergy Agent (Cross-Agent Meta-Mapping natively appended logic sequence)
        synergy_flags, synergy_risk_score = SynergyManager.analyze_heatmap(risk_heatmap, self.client_id)
        risk_heatmap["synergy_analysis"] = synergy_flags
        risk_heatmap["synergy_risk_score"] = synergy_risk_score
        
        try:
            save_master_report(self.client_id, json.dumps(risk_heatmap))
        except Exception as e:
            pass
            
        # Deep Hardware Vault Lock (In-Memory Wipe overriding buffers)
        SynergyManager.secure_wipe(clean_data, raw_data, duplicates, circular_tx, ghost_entities, regulatory)
            
        return risk_heatmap

if __name__ == "__main__":
    filepath = os.path.join(os.path.dirname(__file__), 'test_audit_data.csv')
    if not os.path.exists(filepath):
        print(f"Error: {filepath} not found.")
        sys.exit(1)
        
    auditor = LeadAuditorOrchestrator("Samba Bank Corp")
    heatmap = auditor.execute_audit(filepath)
    
    print("\n[ RISK HEATMAP ]")
    print(json.dumps(heatmap, indent=2))
    print("\n[SUCCESS] Orchestration complete. Heatmap captured.")
