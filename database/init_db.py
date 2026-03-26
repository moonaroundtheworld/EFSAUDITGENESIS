import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.models import Base, engine  # type: ignore

def init():
    print("Activating Genesis Vault...")
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully for Clients, Transactions, Audit_Trails, and Regulatory_Flags.")

if __name__ == "__main__":
    init()
