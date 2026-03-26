import csv
import random
import os

headers = ['date', 'vendor_name', 'amount', 'voucher_no', 'item_name', 'quantity', 'unit_cost', 'nrv', 'bank_account', 'nic']
rows = []

# 1. Standard rows
for i in range(1, 48):
    rows.append([
        f'2026-03-{i%28 + 1:02d}',
        f'Vendor {chr(65 + (i % 5))}',
        round(random.uniform(5000, 45000), 2),  # type: ignore
        f'V-{1000+i}',
        f'Inventory Item {i % 10}',
        random.randint(50, 600),
        random.randint(600, 1000),
        f"PK-BANK-{100 + (i % 15)}",
        f"NIC-42201-{5000 + (i % 20)}"
    ])

# 2. Duplicate Easter Egg
duplicate = rows[0].copy()
duplicate[3] = 'V-1048' # Different voucher identifier
duplicate[8] = 'PK-BANK-XXX'
rows.append(duplicate)

# 3. NRV Violation Easter Egg
rows.append(['2026-03-25', 'Tech Liquidators', 15000, 'V-1049', 'Obsolete Component', 150, 100, 40, 'PK-BANK-000', 'NIC-000'])

# 4. AML Cash Threshold Easter Egg
rows.append(['2026-03-26', 'cash', 2500000, 'V-1050', 'Cash Allocation', 1, 2500000, 2500000, 'PK-BANK-CASH', 'NIC-CASH'])

# 5. Split Transaction (Smurfing) Easter Egg
rows.append(['2026-03-27', 'Vendor Phantom', 1500000, 'V-1051', 'Consulting Services', 1, 1500000, 1500000, 'PK-BANK-999', 'NIC-42201-9999'])
rows.append(['2026-03-27', 'Vendor Phantom', 800000, 'V-1052', 'Logistics', 1, 800000, 800000, 'PK-BANK-999', 'NIC-42201-9999'])

# 6. Round Tripping Easter Egg
rows.append(['2026-03-01', 'Offshore Shell A', 500000, 'V-2001', 'Advisory', 1, 500000, 500000, 'PK-BANK-1001', 'NIC-42201-1001'])
rows.append(['2026-03-25', 'Offshore Base B', 495000, 'V-2002', 'Advisory Refund', 1, 495000, 495000, 'PK-BANK-1002', 'NIC-42201-1002'])

# 7. Ghost Entities Easter Egg (Same NIC, different Vendors)
rows.append(['2026-03-10', 'Legit Corp', 15000, 'V-3001', 'Supplies', 1, 15000, 15000, 'PK-BANK-1111', 'NIC-GHOST-777'])
rows.append(['2026-03-11', 'Shadow Corp', 12000, 'V-3002', 'Supplies', 1, 12000, 12000, 'PK-BANK-2222', 'NIC-GHOST-777'])

# 8. Synergy Kickback Test
rows.append(['2026-03-28', 'Tech Liquidators', 2100000, 'V-5000', 'Consulting Override', 1, 2100000, 2100000, 'PK-BANK-000', 'NIC-000'])

filepath = os.path.join(os.path.dirname(__file__), 'test_audit_data.csv')
with open(filepath, 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(headers)
    writer.writerows(rows)

print(f"Generated 50 realistic rows of Mock Data containing the 3 Easter Eggs at {filepath}")
