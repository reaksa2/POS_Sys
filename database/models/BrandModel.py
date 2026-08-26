# BrandModel.py
class BrandModel:
    def __init__(self, db):
        self.db = db

    def get_brands(self):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, name, phone, telegram, facebook, address
            FROM brands
            WHERE is_active = 1
            ORDER BY id
        """)
        rows = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return rows

    def create_brands(self, brands_data: list[dict]):
        """
        Full sync:
        - Update existing brands (by id if present)
        - Insert new ones
        - Soft-delete brands that are no longer in the list
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()

        try:
            # 1. Get current active brand ids
            cursor.execute("SELECT id FROM brands WHERE is_active = 1")
            existing_ids = {row["id"] for row in cursor.fetchall()}

            kept_ids = set()

            for b in brands_data:
                name = b.get("name", "").strip()
                if not name:
                    continue

                brand_id = b.get("id")   # ← important: UI must send id when editing

                if brand_id and brand_id in existing_ids:
                    # UPDATE
                    cursor.execute("""
                        UPDATE brands SET
                            name = ?, phone = ?, telegram = ?, facebook = ?, address = ?
                        WHERE id = ?
                    """, (
                        name,
                        b.get("phone", ""),
                        b.get("telegram", ""),
                        b.get("facebook", ""),
                        b.get("address", ""),
                        brand_id
                    ))
                    kept_ids.add(brand_id)
                else:
                    # INSERT
                    cursor.execute("""
                        INSERT INTO brands (name, phone, telegram, facebook, address)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        name,
                        b.get("phone", ""),
                        b.get("telegram", ""),
                        b.get("facebook", ""),
                        b.get("address", "")
                    ))
                    kept_ids.add(cursor.lastrowid)

            # 2. Soft-delete brands that were removed from the form
            to_delete = existing_ids - kept_ids
            if to_delete:
                cursor.execute(
                    f"UPDATE brands SET is_active = 0 WHERE id IN ({','.join('?' * len(to_delete))})",
                    tuple(to_delete)
                )

            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()