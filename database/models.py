from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, DateTime  # type: ignore
from sqlalchemy.orm import declarative_base, sessionmaker, relationship  # type: ignore
import os
import hashlib
from datetime import datetime

DATABASE_URL = "sqlite:///d:/EFS_Audit_Genesis/backend/genesis_vault.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Client(Base):
    __tablename__ = "clients"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    transactions = relationship("Transaction", back_populates="client")

class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"))
    hash_key = Column(String, unique=True, index=True)
    date = Column(String)
    amount = Column(Float)
    vendor = Column(String)
    description = Column(String)
    raw_data = Column(String)
    
    client = relationship("Client", back_populates="transactions")
    audit_trails = relationship("AuditTrail", back_populates="transaction")
    regulatory_flags = relationship("RegulatoryFlag", back_populates="transaction")

class AuditTrail(Base):
    __tablename__ = "audit_trails"
    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(Integer, ForeignKey("transactions.id"))
    agent_source = Column(String)  # type: ignore
    severity_level = Column(String)  # type: ignore
    legal_reference = Column(String)  # type: ignore
    reasoning = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    transaction = relationship("Transaction", back_populates="audit_trails")

class MasterAuditReport(Base):
    __tablename__ = "master_audit_reports"
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"))
    report_data = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

class RegulatoryFlag(Base):
    __tablename__ = "regulatory_flags"
    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(Integer, ForeignKey("transactions.id"))
    rule_cited = Column(String)
    description = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    transaction = relationship("Transaction", back_populates="regulatory_flags")

Base.metadata.create_all(bind=engine)

def _generate_hash(amount: float, date: str, vendor: str) -> str:
    s = f"{amount}|{date}|{vendor}".lower()
    return hashlib.sha256(s.encode('utf-8')).hexdigest()

def ensure_client(name: str) -> int:
    db = SessionLocal()
    client = db.query(Client).filter(Client.name == name).first()
    if not client:
        client = Client(name=name)  # type: ignore
        db.add(client)
        db.commit()
        db.refresh(client)
    
    client_id = int(client.id) if client.id else 0
    db.close()
    return client_id

def upsert_transaction(client_id: int, amount: float, date: str, vendor: str, description: str, raw_data: str) -> int:
    hash_key = _generate_hash(amount, date, vendor)
    db = SessionLocal()
    
    tx = db.query(Transaction).filter(Transaction.hash_key == hash_key).first()
    if tx:
        tx.description = description
        tx.raw_data = raw_data
        db.commit()
        db.refresh(tx)
        tx_id = int(tx.id) if tx.id else 0
    else:
        tx = Transaction(client_id=client_id, hash_key=hash_key, date=date, amount=amount, vendor=vendor, description=description, raw_data=raw_data)  # type: ignore
        db.add(tx)
        db.commit()
        db.refresh(tx)
        tx_id = int(tx.id) if tx.id else 0
        
    db.close()
    return tx_id

def log_audit_trail(transaction_id: int, agent_source: str, reasoning: str, severity_level: str = "Medium", legal_reference: str = "N/A") -> None:
    db = SessionLocal()
    trail = AuditTrail(transaction_id=transaction_id, agent_source=agent_source, severity_level=severity_level, legal_reference=legal_reference, reasoning=reasoning)  # type: ignore
    db.add(trail)
    db.commit()
    db.close()

def log_regulatory_flag(transaction_id: int, rule_cited: str, description: str) -> None:
    db = SessionLocal()
    flag = RegulatoryFlag(transaction_id=transaction_id, rule_cited=rule_cited, description=description)  # type: ignore
    db.add(flag)
    db.commit()
    db.close()

def save_master_report(client_id: int, report_data: str) -> None:
    db = SessionLocal()
    report = MasterAuditReport(client_id=client_id, report_data=report_data)  # type: ignore
    db.add(report)
    db.commit()
    db.close()
