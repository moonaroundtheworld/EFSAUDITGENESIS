import json
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from database.models import upsert_transaction, log_audit_trail  # type: ignore
except ImportError:
    pass

def analyze_cash_transactions(data, client_id=None):
    """
    Cash & Bank Agent: Flags AML limits and missing voucher references.
    """
    aml_flags = []
    missing_vouchers = []
    split_transactions = []
    AML_THRESHOLD = 2000000 
    
    daily_vendor_totals = {}  # type: ignore
    
    for idx, row in enumerate(data):
        amount_str = row.get('amount') or row.get('Amount') or row.get('withdrawal') or '0'
        voucher = row.get('voucher_no') or row.get('Voucher') or row.get('reference') or ''
        date = str(row.get('date') or row.get('Date') or 'N/A').strip()
        vendor = str(row.get('vendor_name') or row.get('Vendor') or 'Unknown').strip()
        
        try:
            amt = abs(float(str(amount_str).replace(',', '').strip()))
            
            tx_id = None
            if client_id is not None:
                try:
                    tx_id = upsert_transaction(client_id, amt, date, vendor, 'Cash Transaction', json.dumps(row))
                except Exception:
                    pass
                
            # AML Threshold Check
            if amt > AML_THRESHOLD:
                reason = f"AML Flag: Transaction amount {amt} exceeds monitoring threshold {AML_THRESHOLD} PKR."
                aml_flags.append({"row": idx+1, "amount": amt, "issue": reason})
                if tx_id:
                    try: log_audit_trail(tx_id, "Cash Agent", reason, "Critical", "Pakistan AML Act")
                    except Exception: pass
            
            # Missing Voucher Reference
            if not str(voucher).strip():
                reason = "Control Flag: Missing voucher or reference identifier."
                missing_vouchers.append({"row": idx+1, "amount": amt, "issue": reason})
                if tx_id:
                    try: log_audit_trail(tx_id, "Cash Agent", reason, "Low", "Internal Controls")
                    except Exception: pass
                    
            # Accumulate for Split Transactions (Smurfing Check)
            key = (date.lower(), vendor.lower())
            if key not in daily_vendor_totals:
                daily_vendor_totals[key] = {'total': 0.0, 'rows': [], 'tx_ids': []}
            daily_vendor_totals[key]['total'] += amt
            daily_vendor_totals[key]['rows'].append(idx+1)
            if tx_id:
                daily_vendor_totals[key]['tx_ids'].append(tx_id)
                    
        except ValueError:
            pass
            
    # Pass 2: Check for Split Transactions
    for key, info in daily_vendor_totals.items():
        if len(info['rows']) > 1 and info['total'] > AML_THRESHOLD:
            date_val, vendor_val = key
            reason = f"Split Transaction (Smurfing): {len(info['rows'])} combined payments to '{vendor_val}' on '{date_val}' total {info['total']}, exceeding AML threshold."
            split_transactions.append({"date": date_val, "vendor": vendor_val, "total": info['total'], "rows": info['rows'], "issue": reason})
            for tid in info['tx_ids']:
                try: log_audit_trail(tid, "Cash Agent", reason, "Critical", "Pakistan AML Act - Smurfing")
                except Exception: pass
                
    return {
        "aml_flags": aml_flags,
        "missing_vouchers": missing_vouchers,
        "split_transactions": split_transactions
    }
