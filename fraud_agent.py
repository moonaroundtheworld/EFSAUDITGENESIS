import collections
import math
from typing import List, Dict, Any, Optional, Tuple
import json

try:
    from database.models import upsert_transaction, log_audit_trail  # type: ignore
except ImportError:
    pass

def get_first_digit(num_str: Any) -> Optional[int]:
    """Extracts the first non-zero digit from a string or number."""
    for char in str(num_str):
        if char.isdigit() and char != '0':
            return int(char)
    return None

def analyze_benfords_law(data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyzes the first digits of 'amount' fields in the dataset against Benford's Law.
    Returns a dictionary of actual vs expected frequency percentages.
    """
    first_digits: List[int] = []
    
    for row in data:
        amount = row.get('amount') or row.get('Amount') or row.get('Value') or row.get('value')
        if amount is not None:
            digit = get_first_digit(amount)
            if digit:
                first_digits.append(digit)
    
    total = len(first_digits)
    if total == 0:
        return {
            "actual": {str(k): 0.0 for k in range(1, 10)}, 
            "expected": {str(k): math.log10(1 + 1/k) * 100 for k in range(1, 10)}
        }
    
    counts = collections.Counter(first_digits)  # type: ignore
    actual = {str(d): (counts.get(d, 0) / total) * 100 for d in range(1, 10)}  # type: ignore
    expected = {str(d): math.log10(1 + 1/d) * 100 for d in range(1, 10)}
    
    total_divergence = sum(abs(actual[str(d)] - expected[str(d)]) for d in range(1, 10))
    control_risk_escalated = total_divergence > 15.0
    
    return {
        "actual": actual, 
        "expected": expected,
        "total_divergence_pct": total_divergence,
        "control_risk_escalated": control_risk_escalated
    }

def identify_duplicates(data: List[Dict[str, Any]], client_id: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Flags potential double-billings.
    Checks for exact matches on amount, date, and vendor_name.
    """
    seen: Dict[Tuple[str, str, str], int] = {}
    duplicates: List[Dict[str, Any]] = []
    
    for idx, row in enumerate(data):
        amount = row.get('amount') or row.get('Amount')
        date = row.get('date') or row.get('Date')
        vendor = row.get('vendor_name') or row.get('Vendor') or row.get('vendor')
        
        tx_id = None
        if client_id is not None and amount and date and vendor:
            try:
                amt_val = float(str(amount).replace(',', '').strip())
                tx_id = upsert_transaction(client_id, amt_val, str(date).strip(), str(vendor).strip(), 'Duplicate Check', json.dumps(row))
            except Exception:
                pass
                
        if amount and date and vendor:
            key = (str(amount).strip(), str(date).strip(), str(vendor).strip().lower())
            
            if key in seen:
                reason = f"Duplicate Entry Found: Exact match with Row {seen[key] + 1}"
                duplicates.append({
                    "original_row_index": seen[key] + 1,
                    "duplicate_row_index": idx + 1,
                    "entry": row,
                    "issue": reason
                })
                if tx_id:
                    try:
                        log_audit_trail(tx_id, "Fraud Agent", reason)
                    except Exception:
                        pass
            else:
                seen[key] = idx
                
    return duplicates

from datetime import datetime

# Moved detect_round_tripping to agents/forensics.py

def detect_weekend_posting(data, client_id=None):
    flags = []
    pakistan_holidays = ["03-23", "05-01", "08-14", "11-09", "12-25"]
    for idx, row in enumerate(data):
        date_str = str(row.get('date', '')).strip()
        if date_str:
            try:
                d = datetime.strptime(date_str, "%Y-%m-%d")
                mmdd = d.strftime("%m-%d")
                if d.weekday() == 6:
                    reason = f"Weekend Posting Flag: Manual entry made on Sunday, {date_str}."
                    flags.append({"row": idx+1, "date": date_str, "issue": reason})
                elif mmdd in pakistan_holidays:
                    reason = f"Holiday Posting Flag: Manual entry made on Public Holiday, {date_str}."
                    flags.append({"row": idx+1, "date": date_str, "issue": reason})
            except ValueError:
                pass
    return flags
