from fastapi import APIRouter, HTTPException, Depends  # type: ignore
from sqlalchemy.orm import Session  # type: ignore
from database.models import SessionLocal, Client

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/clients")
def get_all_clients(db: Session = Depends(get_db)):
    clients = db.query(Client).all()
    return [
        {
            "id": c.id,
            "name": c.name,
            "industry": c.industry,
            "status": c.status,
            "engagement_type": c.engagement_type,
            "year_end": c.year_end_date.strftime("%Y-%m-%d") if c.year_end_date else "2026-12-31",
            "external_id": c.external_portal_id
        }
        for c in clients
    ]

@router.post("/clients")
def create_client(payload: dict, db: Session = Depends(get_db)):
    try:
        new_client = Client(
            name=payload.get("name", "Unknown Entity"),
            industry=payload.get("industry", "General"),
            engagement_type=payload.get("engagement_type", "Statutory Audit"),
            external_portal_id=payload.get("external_id")
        )
        db.add(new_client)
        db.commit()
        db.refresh(new_client)
        return {"status": "success", "id": new_client.id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
