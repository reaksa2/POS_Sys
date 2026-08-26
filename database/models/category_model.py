import sqlite3
from ..db_manager import DatabaseManager
class CategoryModel:
    def __init__(self):
        self.db = DatabaseManager()
        

    def get_all_category(self):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM categories")
        data = cursor.fetchall()

        conn.close()
        return data
    

    def add_category(self,data):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
                    INSERT INTO categories (name,description) VALUES(?,?)
        ''',(data["cate_name"],data["cate_des"]))
        conn.commit()
        conn.close()
    def update_category(self,id,data):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE categories SET name =?,description=?
            WHERE id=?
        ''',(data["cate_name"],data["cate_des"],id))
        conn.commit()
        conn.close()

    def delete_category(self,id):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            DELETE FROM categories WHERE id=?
        ''',(id))
        conn.commit()
        conn.close()
        
