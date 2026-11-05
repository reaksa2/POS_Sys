# Version Claud AI 

# stock_utils.py — new file, no class, just a plain function
# NOTE: timestamps are written in LOCAL time explicitly. The table default
# CURRENT_TIMESTAMP is UTC, which put movements 7h off (wrong day before 7am)
# while every filter compares against datetime('now', 'localtime').
def adjust_stock_in_transaction(cursor, product_id, brand_id, movement_type,
                                  quantity, reason="", reference_order_id=None, created_by=None):
    cursor.execute(
        "SELECT quantity FROM stock WHERE product_id = ? AND brand_id = ?",
        (product_id, brand_id)
    )
    row = cursor.fetchone()
    current_qty = row['quantity'] if row else 0
    delta = quantity if movement_type == 'in' else -quantity
    new_qty = current_qty + delta

    if row:
        cursor.execute(
            "UPDATE stock SET quantity = ?, updated_at = datetime('now', 'localtime') WHERE product_id = ? AND brand_id = ?",
            (new_qty, product_id, brand_id)
        )
    else:
        cursor.execute(
            "INSERT INTO stock (product_id, brand_id, quantity, updated_at) VALUES (?, ?, ?, datetime('now', 'localtime'))",
            (product_id, brand_id, new_qty)
        )

    cursor.execute('''
        INSERT INTO stock_movements
            (product_id, brand_id, movement_type, quantity, reason, reference_order_id, created_by, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now', 'localtime'))
    ''', (product_id, brand_id, movement_type, quantity, reason, reference_order_id, created_by))

    return new_qty


# Version Grok AI 
# stock_utils.py



