import json
import sys
import os

# Ensure database is reachable
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from database.models import upsert_transaction, log_audit_trail  # type: ignore
except ImportError:
    pass

def analyze_inventory(data, client_id=None):
    """
    Inventory Agent: Detects Negative Stock and Valuation Outliers (NRV vs Cost).
    """
    negative_stock = []
    valuation_outliers = []
    
    for idx, row in enumerate(data):
        item = row.get('item_name') or row.get('Item') or row.get('item') or f"Row {idx+1}"
        qty_str = row.get('quantity') or row.get('Qty') or row.get('qty', '0')
        cost_str = row.get('unit_cost') or row.get('Cost') or row.get('cost', '0')
        nrv_str = row.get('nrv') or row.get('selling_price') or row.get('NRV') or '0'
        days_str = row.get('days_since_last_sale') or row.get('idle_days') or row.get('Stale_Days') or '0'
        
        try:
            qty = float(str(qty_str).replace(',', '').strip())
            cost = float(str(cost_str).replace(',', '').strip())
            nrv = float(str(nrv_str).replace(',', '').strip())
            
            try:
                days_idle = int(str(days_str).strip())
            except ValueError:
                days_idle = 0

            tx_id = None
            if client_id is not None:
                amount = qty * cost if qty > 0 else 0
                try:
                    tx_id = upsert_transaction(client_id, amount, 'N/A', item, 'Inventory Row', json.dumps(row))
                except Exception:
                    pass
            
            # 1. Negative Stock
            if qty < 0:
                reason = f"Negative stock detected: Quantity {qty}"
                negative_stock.append({"row": idx+1, "item": item, "issue": reason})
                if tx_id:
                    try:
                        log_audit_trail(tx_id, "Inventory Agent", reason, "High", "Framework Rules")
                    except Exception:
                        pass
            
            # 2. NRV vs Cost (Potential Overvaluation)
            if nrv > 0 and nrv < cost:
                reason = f"Potential Overvaluation: NRV ({nrv}) is lower than Cost ({cost}). Recommendation: Write-down."
                valuation_outliers.append({"row": idx+1, "item": item, "issue": reason})
                if tx_id:
                    try:
                        log_audit_trail(tx_id, "Inventory Agent", reason, "High", "IAS 2 Inventories")
                    except Exception:
                        pass
                        
            # 3. Stale Stock (> 180 Days)
            if days_idle > 180:
                reason = f"Stale Stock: Item hasn't moved in {days_idle} days. Consider Slow Moving Provision."
                negative_stock.append({"row": idx+1, "item": item, "issue": reason})
                if tx_id:
                    try:
                        log_audit_trail(tx_id, "Inventory Agent", reason, "Medium", "IAS 2 Inventories")
                    except Exception:
                        pass
                    
        except ValueError:
            pass

    return {
        "negative_stock": negative_stock,
        "valuation_outliers": valuation_outliers
    }

class ReconciliationEngine:
    @staticmethod
    def reconcile(client_id: int, item_id: str, item_value_per_unit: float, physical_quantity: float, system_quantity: float, performance_materiality: float, location_tag: str):
        """
        Floor-to-Sheet logic directly comparing mobile inputs mathematically against system Vault logs.
        """
        variance_qty = system_quantity - physical_quantity
        variance_value = variance_qty * item_value_per_unit
        
        flag = None
        if variance_value > performance_materiality:
            reason = f"Material Stock Shortage [Floor-to-Sheet]: Physical count ({physical_quantity}) at '{location_tag}' is short by {variance_qty} units vs System ({system_quantity}). Variance absolute value (PKR {variance_value:,.2f}) strictly exceeds Performance Materiality rules (PKR {performance_materiality:,.2f})."
            flag = {
                "item_id": item_id,
                "variance_value": variance_value,
                "severity": "Critical",
                "issue": reason
            }
        elif variance_value > 0:
            reason = f"Immaterial Stock Shortage: Physical count is short by {variance_qty} units (PKR {variance_value:,.2f}), successfully mapped under structural materiality boundaries."
            flag = {
                "item_id": item_id,
                "variance_value": variance_value,
                "severity": "Low",
                "issue": reason
            }
            
        return flag
