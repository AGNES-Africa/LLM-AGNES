import psycopg2

def get_urls_from_db(conn_str):
    urls = []

    try:
        conn = psycopg2.connect(conn_str)
        
        cur = conn.cursor()
        cur.execute('SELECT url FROM public."Article";')
        
        urls = [row[0] for row in cur.fetchall()]  
        
        cur.close()
        conn.close()
        
        return urls
    except psycopg2.DatabaseError as e:
        print(f"Database error: {e}")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None