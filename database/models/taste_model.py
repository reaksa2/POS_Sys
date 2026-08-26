import sqlite3
from ..db_manager import DatabaseManager
class TasteModel:
    def __init__(self):
        self.db = DatabaseManager()
        

    def get_all_taste(self):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM taste")
        data = cursor.fetchall()

        conn.close()
        return data
    

    def add_taste(self,data):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
                    INSERT INTO taste (name,description) VALUES(?,?)
        ''',(data["taste_name"],data["taste_des"]))
        conn.commit()
        conn.close()

    def update_taste(self,id,data):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE taste SET name =?,description=?
            WHERE id=?
        ''',(data["taste_name"],data["taste_des"],id))
        conn.commit()
        conn.close()

    def delete_taste(self,id):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            DELETE FROM taste WHERE id=?
        ''',(id))
        conn.commit()
        conn.close()
        
        
