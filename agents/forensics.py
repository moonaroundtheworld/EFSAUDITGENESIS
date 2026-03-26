import sys
import os
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from database.models import upsert_transaction, log_audit_trail  # type: ignore
except ImportError:
    pass

def detect_circular_transactions(data, client_id=None):
    flags = []
    parsed = []
    
    for idx, row in enumerate(data):
        amt_str = str(row.get('amount', 0)).replace(',', '').strip()
        date_str = str(row.get('date', '')).strip()
        vendor = str(row.get('vendor_name') or row.get('vendor') or 'unknown').strip().lower()
        if amt_str and date_str:
            try:
                amt = abs(float(amt_str))
                d = datetime.strptime(date_str, "%Y-%m-%d")
                parsed.append((idx+1, d, amt, vendor))
            except ValueError:
                pass
                
    # Detect roughly identical +/- 2% amounts leaving and entering across differing accounts within 45 days
    seen_pairs = set()
    for i in range(len(parsed)):
        for j in range(i+1, len(parsed)):
            idx1, d1, amt1, v1 = parsed[i]  # type: ignore
            idx2, d2, amt2, v2 = parsed[j]  # type: ignore
            
            if amt1 > 0:
                deviation = abs(amt1 - amt2) / amt1
                if deviation <= 0.02: # 2% margin
                    days_diff = abs((d1 - d2).days)
                    if 0 < days_diff <= 45 and v1 != v2:
                        pair = tuple(sorted([idx1, idx2]))
                        if pair not in seen_pairs:
                            seen_pairs.add(pair)
                            reason = f"Circular Transaction (Round-Tripping): Amount equivalent to {amt1} (±{round(deviation*100,2)}%) moved across differing entities ('{v1}' & '{v2}') within {days_diff} days."  # type: ignore
                            flags.append({"rows": [idx1, idx2], "amount": amt1, "issue": reason})
                            # Would log to DB here if tx_ids generated
    return flags

def detect_ghost_entities(data, client_id=None):
    flags = []
    accounts_map: dict = {}
    nic_map: dict = {}
    
    for idx, row in enumerate(data):
        vendor = str(row.get('vendor_name') or row.get('vendor') or 'unknown').strip().lower()
        acc = str(row.get('bank_account') or row.get('account_number') or row.get('iban', '')).strip()
        nic = str(row.get('nic') or row.get('cnic') or row.get('identity', '')).strip()
        
        if acc:
            if acc not in accounts_map:
                accounts_map[acc] = set()
            accounts_map[acc].add(vendor)  # type: ignore
            if len(accounts_map[acc]) > 1:  # type: ignore
                reason = f"Ghost Vendor Flag: Bank Account '{acc}' is shared by multiple distinct entities: {list(accounts_map[acc])}"
                if not any(f.get("identifier") == acc for f in flags):
                    flags.append({"identifier": acc, "type": "Bank Account", "entities": list(accounts_map[acc]), "issue": reason})
                    
        if nic:
            if nic not in nic_map:
                nic_map[nic] = set()
            nic_map[nic].add(vendor)  # type: ignore
            if len(nic_map[nic]) > 1:  # type: ignore
                reason = f"Ghost Employee Flag: NIC/CNIC '{nic}' is shared by multiple distinct entities: {list(nic_map[nic])}"
                if not any(f.get("identifier") == nic for f in flags):
                    flags.append({"identifier": nic, "type": "NIC", "entities": list(nic_map[nic]), "issue": reason})
                    
    return flags
