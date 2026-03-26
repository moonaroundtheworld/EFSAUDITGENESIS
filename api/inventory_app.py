from fastapi import APIRouter, HTTPException  # type: ignore
from pydantic import BaseModel  # type: ignore
from database.models import SessionLocal, Client, Transaction, log_audit_trail  # type: ignore
from agents.inventory import ReconciliationEngine  # type: ignore
import json
import os
from datetime import datetime

router = APIRouter()

class SyncCountRequest(BaseModel):
    client_name: str
    item_id: str
    item_value_per_unit: float
    system_quantity: float
    physical_quantity: float
    location_tag: str
    evidence_hash: str
    counter_id: str
    gps_metadata: str
    performance_materiality: float

@router.post("/sync-count")
def sync_inventory_count(payload: SyncCountRequest):
    db = SessionLocal()
    client = db.query(Client).filter(Client.name == payload.client_name).first()
    if not client:
        db.close()
        raise HTTPException(status_code=404, detail="Client not found")
        
    # 1. Floor-to-Sheet Discrepancy Logic
    flag = ReconciliationEngine.reconcile(
        client_id=client.id,
        item_id=payload.item_id,
        item_value_per_unit=payload.item_value_per_unit,
        physical_quantity=payload.physical_quantity,
        system_quantity=payload.system_quantity,
        performance_materiality=payload.performance_materiality,
        location_tag=payload.location_tag
    )
    
    if flag and flag['severity'] == "Critical":
        # Target the genesis client node to record the systemic stock deficit
        tx = db.query(Transaction).filter(Transaction.client_id == client.id).first()
        if tx:
            log_audit_trail(tx.id, "Inventory Field Agent", flag['issue'], "Critical", "ISA 501: Audit Evidence - Physical Inventory Counting")
            
    db.close()

    # 2. Evidence Vaulting
    # Secure storage logic natively persisting metadata logs linking GPS to the physical count
    vault_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "vault", "evidence", payload.client_name.replace(" ", "_"))
    os.makedirs(vault_dir, exist_ok=True)
    
    evidence_metadata = {
        "item_id": payload.item_id,
        "physical_quantity": payload.physical_quantity,
        "location_tag": payload.location_tag,
        "evidence_hash": payload.evidence_hash,
        "timestamp": datetime.utcnow().isoformat(),
        "gps_metadata": payload.gps_metadata,
        "counter_id": payload.counter_id,
        "variance_flagged": flag is not None
    }
    
    file_path = os.path.join(vault_dir, f"{payload.item_id.replace(' ', '_')}_{payload.counter_id}.json")
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(evidence_metadata, f, indent=4)
        
    return {"status": "success", "evidence_vaulted": True, "reconciliation_flag": flag}

@router.get("/count-sheet/{client_name}")
def get_count_sheet(client_name: str):
    db = SessionLocal()
    client = db.query(Client).filter(Client.name == client_name).first()
    if not client:
        db.close()
        raise HTTPException(status_code=404, detail="Client not found")
        
    transactions = db.query(Transaction).filter(Transaction.client_id == client.id).all()
    
    inventory_items = []
    seen = set()
    
    # 3. Mobile Data Provider processing Vault transactions looking for highly material stock
    for tx in transactions:
        if tx.raw_data:
            try:
                # Need to swap single to double quotes if it's a string repr of dict, but csv to json saves perfectly
                row = json.loads(tx.raw_data.replace("'", '"')) 
            except json.JSONDecodeError:
                continue

            item_name = row.get('item_name') or row.get('item')
            qty_str = str(row.get('quantity') or row.get('qty', '0')).replace(',', '')
            unit_cost_str = str(row.get('unit_cost') or row.get('cost', '0')).replace(',', '')
            
            if item_name and item_name not in seen:
                try:
                    qty = float(qty_str)
                    cost = float(unit_cost_str)
                    total_value = qty * cost
                    
                    # Target filters: Material stock overrides
                    if total_value > 100000 or cost > 50000:
                        inventory_items.append({
                            "item_id": item_name,
                            "system_quantity": qty,
                            "unit_cost": cost,
                            "total_system_value": total_value,
                            "risk_tier": "High Risk - Material Payload"
                        })
                        seen.add(item_name)
                except ValueError:
                    pass
                
    db.close()
    
    inventory_items.sort(key=lambda x: x["total_system_value"], reverse=True)
    return {"client": client_name, "total_target_items": len(inventory_items), "count_sheet": inventory_items}
