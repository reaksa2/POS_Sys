import sqlite3
from ..db_manager import DatabaseManager
class UnitModel:
    def __init__(self):
        self.db = DatabaseManager()
        

    def get_all_unit(self):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM units")
        data = cursor.fetchall()

        conn.close()
        return data
    

    def add_unit(self,data):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
                    INSERT INTO units (name,description) VALUES(?,?)
        ''',(data["unit_name"],data["unit_des"]))
        conn.commit()
        conn.close()

    def update_unit(self,id,data):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE units SET name =?,description=?
            WHERE id=?
        ''',(data["unit_name"],data["unit_des"],id))
        conn.commit()
        conn.close()

    def delete_unit(self,id):
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            DELETE FROM units WHERE id=?
        ''',(id))
        conn.commit()
        conn.close()
        
