import sqlite3

def init_db():
    try:
        conn = sqlite3.connect("tokens.db")
        print("Verbindung aufgebaut.")

        table_creation_query = """
            CREATE TABLE IF NOT EXISTS user_tokens (
                user_id VARCHAR(255) PRIMARY KEY,
                access_token VARCHAR(255),
                refresh_token VARCHAR(255),
                expires_at INT
            );
        """

        conn.execute(table_creation_query)
        print("Database Table erstellt.")

        conn.commit()
        print("Änderungen gespeichert.")
    except sqlite3.Error as error:
        print("Failed to connect with sqlite3 database", error)
    finally:
        if conn:
            conn.close()
            print("Verbindung geschlossen.")
            

def save_tokens(user_id: str, access_token: str, refresh_token: str, expires_at: int):
    try:
        
        conn = sqlite3.connect("tokens.db")
        print("Verbindung aufgebaut.")
        
        query = """
            INSERT INTO user_tokens (user_id, access_token, refresh_token, expires_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT (user_id)
            DO UPDATE SET
                access_token = EXCLUDED.access_token,
                refresh_token = EXCLUDED.refresh_token,
                expires_at = EXCLUDED.expires_at;
        """
        conn.execute(query, (user_id, access_token, refresh_token, expires_at))
        
        conn.commit()
    except sqlite3.Error as error:
        print("Failed to connect with sqlite3 database", error)
    finally:
        if conn:
            conn.close()
            print("Verbindung geschlossen.")
            
            
def get_tokens(user_id: str):
    try:
        conn = sqlite3.connect("tokens.db")
        print("Verbindung aufgebaut.")
        
        conn.row_factory = sqlite3.Row
        
        cursor = conn.cursor()
        
        query = """
            SELECT access_token, refresh_token, expires_at
            FROM user_tokens
            WHERE user_id = ?;
        """
        
        cursor.execute(query, (user_id,))
        row = cursor.fetchone()
        
        if row:
            data_dict = dict(row)
            print(data_dict)
            return data_dict
        else:
            return None
        
    except sqlite3.Error as error:
        print("Failed to connect with sqlite3 database", error)
    finally:
        if conn:
            conn.close()
            print("Verbindung geschlossen.")