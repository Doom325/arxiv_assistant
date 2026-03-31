
import psycopg2
import os

try:
    conn = psycopg2.connect('postgresql://user:password@192.168.1.49:5434/arxiv_db')
    cur = conn.cursor()
    cur.execute("SELECT pid, state, wait_event_type, wait_event, query_start, query FROM pg_stat_activity WHERE datname = 'arxiv_db' AND pid <> pg_backend_pid()")
    
    with open('db_activity.txt', 'w') as f:
        for row in cur.fetchall():
            f.write(str(row) + '\n')
            
    # Also check pg_locks specific to our table if possible (oid of papers table?)
    # But stat_activity is usually enough to see 'active' + 'Lock'
    
    cur.close()
    conn.close()
    print("db_activity.txt written.")
except Exception as e:
    print(e)
