from fastapi import FastAPI, UploadFile, File  # type: ignore
from fastapi.middleware.cors import CORSMiddleware  # type: ignore
import csv
import io
import json
from reporting import generate_audit_opinion  # type: ignore
from fastapi import Request  # type: ignore
from fastapi.responses import JSONResponse, FileResponse  # type: ignore
from fastapi.staticfiles import StaticFiles  # type: ignore
from starlette.middleware.base import BaseHTTPMiddleware  # type: ignore
from fraud_agent import analyze_benfords_law, identify_duplicates  # type: ignore
from regulatory_agent import get_regulatory_flags_for_dataset  # type: ignore
from agents.inventory import analyze_inventory  # type: ignore
from agents.cash import analyze_cash_transactions  # type: ignore
from database.models import ensure_client, AuditTrail, Client, Transaction, SessionLocal, RegulatoryFlag  # type: ignore
from sqlalchemy import func, desc  # type: ignore
import os
from datetime import datetime
from pydantic import BaseModel  # type: ignore
from crypto_utils import decrypt_cryptojs_aes  # type: ignore
from logic.planning import APMGenerator  # type: ignore
from api.inventory_app import router as inventory_router  # type: ignore

app = FastAPI(title="Audit Genesis API")
app.include_router(inventory_router, prefix="/api/inventory")

class EncryptedUpload(BaseModel):
    filename: str
    encrypted_data: str
    encryption_key: str

class APMRequest(BaseModel):
    overall_materiality: float
    performance_materiality: float

class ClientLockMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path not in ["/docs", "/openapi.json"] and request.method != "OPTIONS":
            if "x-client-id" not in request.headers:
                return JSONResponse(
                    status_code=403, 
                    content={"error": "Vault Lock Active", "details": "Missing X-Client-ID Header. Connection Refused."}
                )
        return await call_next(request)

app.add_middleware(ClientLockMiddleware)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"error": "Malformed Internal Request / Critical Syntax Fault", "details": str(exc)}
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://everyfinancialsolution.com",
        "https://www.everyfinancialsolution.com",
        "http://localhost:5173" # For local testing
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Welcome to Audit Genesis API"}

@app.get("/api/health")
def health_check():
    return {"status": "healthy"}

@app.post("/audit/upload")
async def upload_audit_file(file: UploadFile = File(...)):
    contents = await file.read()
    # Decode contents safely
    try:
        decoded = contents.decode('utf-8')
    except UnicodeDecodeError:
        decoded = contents.decode('latin-1')
        
    reader = csv.DictReader(io.StringIO(decoded))
    data = [row for row in reader]
    
    client_id = ensure_client("Stealth Client 1")
    benford_results = analyze_benfords_law(data)
    duplicates = identify_duplicates(data, client_id)
    regulatory_issues = get_regulatory_flags_for_dataset(data, client_id)
    
    # Calculate a simple risk score based on duplicates and regulatory flags
    risk_score = min(100, (len(duplicates) * 15) + (len(regulatory_issues) * 20))
    
    return {
        "filename": file.filename,
        "total_records": len(data),
        "risk_score": risk_score,
        "benfords_law": benford_results,
        "flagged_entries": duplicates,
        "regulatory_issues": regulatory_issues
    }

@app.post("/audit/upload_encrypted", tags=["Audit Vault Engine"], summary="Deploy Encrypted External DB Artifacts")
async def upload_encrypted_file(deployment: EncryptedUpload):
    # Multi-Client Vault Isolation (Folder-Level Partitioning)
    client_name = "Stealth Client 1"
    vault_dir = os.path.join(os.path.dirname(__file__), "vault", client_name.replace(" ", "_"))
    os.makedirs(vault_dir, exist_ok=True)
    
    file_path = os.path.join(vault_dir, f"{deployment.filename}_{datetime.now().strftime('%Y%m%d%H%M%S')}.enc")
    with open(file_path, "w", encoding='utf-8') as f:
        f.write(deployment.encrypted_data)

    try:
        decoded = decrypt_cryptojs_aes(deployment.encrypted_data, deployment.encryption_key)
    except Exception as e:
        return {"error": str(e), "risk_score": 0}
        
    reader = csv.DictReader(io.StringIO(decoded))
    data = [row for row in reader]
    
    client_id = ensure_client("Stealth Client 1")
    benford_results = analyze_benfords_law(data)
    duplicates = identify_duplicates(data, client_id)
    regulatory_issues = get_regulatory_flags_for_dataset(data, client_id)
    
    risk_score = min(100, (len(duplicates) * 15) + (len(regulatory_issues) * 20))
    
    return {
        "filename": deployment.filename,
        "total_records": len(data),
        "risk_score": risk_score,
        "benfords_law": benford_results,
        "flagged_entries": duplicates,
        "regulatory_issues": regulatory_issues
    }

@app.post("/audit/inventory", tags=["Inventory Agent"], summary="Deploy Inventory Artifacts")
async def upload_inventory_file(file: UploadFile = File(...)):
    contents = await file.read()
    try:
        decoded = contents.decode('utf-8')
    except UnicodeDecodeError:
        decoded = contents.decode('latin-1')
        
    reader = csv.DictReader(io.StringIO(decoded))
    data = [row for row in reader]
    
    client_id = ensure_client("Stealth Client 1")
    results = analyze_inventory(data, client_id)
    results["filename"] = file.filename
    results["total_records"] = len(data)
    
    return results

@app.post("/audit/cash", tags=["Cash Agent"], summary="Deploy Cash Artifacts")
async def upload_cash_file(file: UploadFile = File(...)):
    contents = await file.read()
    try:
        decoded = contents.decode('utf-8')
    except UnicodeDecodeError:
        decoded = contents.decode('latin-1')
        
    reader = csv.DictReader(io.StringIO(decoded))
    data = [row for row in reader]
    
    client_id = ensure_client("Stealth Client 1")
    results = analyze_cash_transactions(data, client_id)
    results["filename"] = file.filename
    results["total_records"] = len(data)
    
    return results

@app.get("/api/audit-trail/{client_name}", tags=["Audit Log Extraction"], summary="Target Client Immutable Event Paths")
def get_audit_trail(client_name: str):
    db = SessionLocal()
    client = db.query(Client).filter(Client.name == client_name).first()
    if not client:
        db.close()
        return {"error": "Client not found", "audit_trail": []}
        
    transactions = db.query(Transaction).filter(Transaction.client_id == client.id).all()
    tx_ids = [t.id for t in transactions]
    
    trails = db.query(AuditTrail).filter(AuditTrail.transaction_id.in_(tx_ids)).order_by(AuditTrail.created_at.desc()).all()
    
    results = []
    for tr in trails:
        results.append({
            "id": tr.id,
            "agent": tr.agent_source,
            "severity": tr.severity_level,
            "legal_ref": tr.legal_reference,
            "reasoning": tr.reasoning,
            "date": tr.created_at.strftime("%Y-%m-%d %H:%M:%S")
        })
    db.close()
    return {"client": client_name, "trail": results}

@app.get("/api/executive-summary/{client_name}", tags=["Executive Dashboard"], summary="Render Massive Quantitative Risk Arrays")
def get_executive_summary(client_name: str):
    db = SessionLocal()
    client = db.query(Client).filter(Client.name == client_name).first()
    if not client:
        db.close()
        return {"error": "Client not found"}
        
    transactions = db.query(Transaction).filter(Transaction.client_id == client.id).all()
    tx_ids = [t.id for t in transactions]
    
    # 1. Total Risk Exposure
    flagged_tx_ids = set()
    trails = db.query(AuditTrail.transaction_id).filter(AuditTrail.transaction_id.in_(tx_ids)).all()
    regs = db.query(RegulatoryFlag.transaction_id).filter(RegulatoryFlag.transaction_id.in_(tx_ids)).all()
    
    for t in trails: flagged_tx_ids.add(t[0])
    for r in regs: flagged_tx_ids.add(r[0])
    
    total_exposure = 0.0
    for tx in transactions:
        if tx.id in flagged_tx_ids:
            total_exposure += float(tx.amount)  # type: ignore
            
    # 2. Top 5 Critical Flags
    top_flags = db.query(AuditTrail).filter(
        AuditTrail.transaction_id.in_(tx_ids),
        AuditTrail.severity_level == "Critical"
    ).order_by(AuditTrail.created_at.desc()).limit(5).all()
    
    top_5 = [{"reasoning": f.reasoning, "agent": f.agent_source} for f in top_flags]
    if not top_5:
        high_flags = db.query(AuditTrail).filter(
            AuditTrail.transaction_id.in_(tx_ids),
            AuditTrail.severity_level == "High"
        ).order_by(AuditTrail.created_at.desc()).limit(5).all()
        top_5 = [{"reasoning": f.reasoning, "agent": f.agent_source} for f in high_flags]
        
    # 3. Regulatory Heatmap
    heatmap_query = db.query(
        RegulatoryFlag.rule_cited, 
        func.count(RegulatoryFlag.id).label('hit_count')
    ).filter(RegulatoryFlag.transaction_id.in_(tx_ids)).group_by(RegulatoryFlag.rule_cited).order_by(desc('hit_count')).all()
    
    heatmap = {}
    for rule, count in heatmap_query:
        heatmap[rule] = count
        
    db.close()
    
    # Fetch specific Synergy Metric directly from Master JSON
    from database.models import MasterAuditReport  # type: ignore
    master = db.query(MasterAuditReport).filter(MasterAuditReport.client_id == client.id).order_by(desc(MasterAuditReport.created_at)).first()
    synergy_score = 0
    if master and master.report_data:
        try:
            report_data = json.loads(master.report_data)
            synergy_score = report_data.get("synergy_risk_score", 0)
        except Exception:
            pass

    draft_opinion = generate_audit_opinion(total_exposure, heatmap)

    return {
        "client": client_name,
        "total_risk_exposure": total_exposure,
        "synergy_risk_score": synergy_score,
        "draft_audit_opinion": draft_opinion,
        "top_5_flags": top_5,
        "regulatory_heatmap": heatmap
    }

@app.post("/api/generate-apm/{client_name}", tags=["Strategy Module APM"], summary="Draft Structural Audit Planning Guidelines")
def generate_apm(client_name: str, payload: APMRequest):
    apm = APMGenerator(client_name, payload.overall_materiality, payload.performance_materiality)
    return apm.generate()

# ==========================================
# React WSGI Native Asset Delivery Interceptor
# ==========================================
public_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "public")
if os.path.exists(public_dir):
    app.mount("/assets", StaticFiles(directory=os.path.join(public_dir, "assets")), name="assets")

    @app.get("/{catchall:path}", tags=["Frontend Asset Delivery"], summary="WSGI React Router Bypass")
    def serve_react_app(catchall: str):
        # Bypass absolute file mappings automatically
        file_path = os.path.join(public_dir, catchall)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        # Re-route structural UI navigation directly to React DOM
        return FileResponse(os.path.join(public_dir, "index.html"))
