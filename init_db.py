import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def init_database():
    database_url = os.getenv('DATABASE_URL')
    
    if not database_url:
        print("❌ DATABASE_URL not found in environment variables")
        return
    
    try:
        conn = psycopg2.connect(database_url)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Create tables
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS karyawan (
                id SERIAL PRIMARY KEY,
                nama VARCHAR(100) NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                divisi VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS presensi (
                id SERIAL PRIMARY KEY,
                karyawan_id INTEGER REFERENCES karyawan(id),
                tanggal DATE DEFAULT CURRENT_DATE,
                waktu_masuk TIME,
                waktu_keluar TIME,
                status VARCHAR(20) DEFAULT 'Hadir',
                keterangan TEXT,
                lokasi VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Insert sample data
        cursor.execute('''
            INSERT INTO karyawan (nama, email, divisi) 
            VALUES 
            ('Ahmad Rizki', 'ahmad@company.com', 'IT'),
            ('Sari Dewi', 'sari@company.com', 'HR'),
            ('Budi Santoso', 'budi@company.com', 'Marketing'),
            ('Dewi Lestari', 'dewi@company.com', 'Finance'),
            ('Rizky Pratama', 'rizky@company.com', 'Operations')
            ON CONFLICT (email) DO NOTHING
        ''')
        
        print("✅ Database initialized successfully!")
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error initializing database: {e}")

if __name__ == "__main__":
    init_database()