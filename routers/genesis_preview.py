from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database.models import SessionLocal, Client, Workpaper, Transaction

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 1. Accounting Portal Mappings
@router.get("/genesis/accounting-data/{client_id}")
def get_accounting_data(client_id: int, db: Session = Depends(get_db)):
    # Basic mock mapped structure representing DB stats mapped for #ovKpis, `#ledgerContent`, `#txBody` etc.
    return {
        "client_id": client_id,
        "kpis": {
            "revenue": 5000000,
            "expenses": 1200000,
            "net_profit": 3800000,
            "cash_position": 850000
        },
        "ledgerContent": [
            {"date": "2026-03-25", "ref": "JRN-001", "account": "Cash", "debit": 500000, "credit": 0, "balance": 850000},
            {"date": "2026-03-26", "ref": "JRN-002", "account": "Sales", "debit": 0, "credit": 500000, "balance": -500000}
        ],
        "transactions": [
            {"date": "2026-03-26", "ref": "INV-001", "type": "Revenue", "narration": "Software License", "debit_acc": "Cash", "credit_acc": "Sales", "amount": 500000, "tax": 0, "by": "System", "status": "Posted"}
        ]
    }

# 2. Money Manager Mappings
@router.get("/genesis/money-manager-data/{client_id}")
def get_money_manager_data(client_id: int, db: Session = Depends(get_db)):
    return {
        "quickStats": {
            "today_income": 45000,
            "today_expense": 12000,
            "month_net": 120000,
            "net_worth": 5600000,
            "cc_outstanding": 15000
        },
        "accountsOverview": [
            {"id": "A1", "name": "Main Checking", "type": "Bank", "balance": 1200000, "currency": "PKR"},
            {"id": "A2", "name": "Tax Reserve", "type": "Savings", "balance": 500000, "currency": "PKR"}
        ],
        "recentTransactions": [
            {"date": "2026-03-26", "category": "Software", "amount": 12000, "account": "Main Checking"}
        ]
    }

# 3. PSX Platform Mappings
@router.get("/genesis/psx-data/{client_id}")
def get_psx_data(client_id: int, db: Session = Depends(get_db)):
    return {
        "tickerStrip": [
            {"symbol": "SYS", "price": "450.00", "change": "+5.50", "direction": "up"},
            {"symbol": "TRG", "price": "120.00", "change": "-2.10", "direction": "down"}
        ],
        "watchlist": [
            {"symbol": "SYS", "name": "Systems Limited", "price": "450.00", "change_pct": "1.2%"}
        ],
        "portfolio": [
            {"symbol": "LUCK", "qty": 1000, "avg_cost": "750.00", "current_price": "800.00", "pnl": "50000"}
        ]
    }
