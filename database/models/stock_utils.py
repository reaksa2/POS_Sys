# Version Claud AI 

# stock_utils.py — new file, no class, just a plain function
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
            "UPDATE stock SET quantity = ?, updated_at = CURRENT_TIMESTAMP WHERE product_id = ? AND brand_id = ?",
            (new_qty, product_id, brand_id)
        )
    else:
        cursor.execute(
            "INSERT INTO stock (product_id, brand_id, quantity) VALUES (?, ?, ?)",
            (product_id, brand_id, new_qty)
        )

    cursor.execute('''
        INSERT INTO stock_movements
            (product_id, brand_id, movement_type, quantity, reason, reference_order_id, created_by)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (product_id, brand_id, movement_type, quantity, reason, reference_order_id, created_by))

    return new_qty


# Version Grok AI 
# stock_utils.py



