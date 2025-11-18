from flask import Flask, render_template, request, jsonify
import os
from datetime import datetime, date
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Database configuration - Support both SQLite and PostgreSQL
def get_db_connection():
    database_url = os.getenv('DATABASE_URL')
    
    # Jika di Railway (ada DATABASE_URL PostgreSQL)
    if database_url and database_url.startswith('postgresql://'):
        try:
            import psycopg2
            conn = psycopg2.connect(database_url)
            print("🚀 Using PostgreSQL (Railway)")
            return conn
        except ImportError:
            print("⚠️ psycopg2 not available, falling back to SQLite")
            return create_sqlite_connection()
    else:
        # Untuk development pakai SQLite
        print("💻 Using SQLite (Development)")
        return create_sqlite_connection()

def create_sqlite_connection():
    import sqlite3
    conn = sqlite3.connect('presensi.db', check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

# Initialize database
def init_database():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check database type
        database_url = os.getenv('DATABASE_URL')
        is_postgres = database_url and database_url.startswith('postgresql://')
        
        if is_postgres:
            # PostgreSQL syntax
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
            
            # Insert sample employees
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
        else:
            # SQLite syntax
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS karyawan (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nama VARCHAR(100) NOT NULL,
                    email VARCHAR(100) UNIQUE NOT NULL,
                    divisi VARCHAR(50),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS presensi (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
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
            
            # Insert sample employees
            cursor.execute('''
                INSERT OR IGNORE INTO karyawan (nama, email, divisi) 
                VALUES 
                ('Ahmad Rizki', 'ahmad@company.com', 'IT'),
                ('Sari Dewi', 'sari@company.com', 'HR'),
                ('Budi Santoso', 'budi@company.com', 'Marketing'),
                ('Dewi Lestari', 'dewi@company.com', 'Finance'),
                ('Rizky Pratama', 'rizky@company.com', 'Operations')
            ''')
        
        conn.commit()
        cursor.close()
        conn.close()
        print("✅ Database initialized successfully!")
    except Exception as e:
        print(f"❌ Database initialization error: {e}")

# Initialize database before first request
@app.before_request
def before_first_request():
    init_database()

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/presensi')
def presensi():
    conn = get_db_connection()
    
    database_url = os.getenv('DATABASE_URL')
    is_postgres = database_url and database_url.startswith('postgresql://')
    
    try:
        if is_postgres:
            import psycopg2.extras
            cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cursor.execute('SELECT id, nama, email, divisi FROM karyawan ORDER BY nama')
            karyawan = cursor.fetchall()
            # Convert to list of dicts
            karyawan_list = []
            for row in karyawan:
                karyawan_list.append(dict(row))
        else:
            cursor = conn.cursor()
            cursor.execute('SELECT id, nama, email, divisi FROM karyawan ORDER BY nama')
            karyawan = cursor.fetchall()
            # Convert to list of dicts
            karyawan_list = []
            for row in karyawan:
                karyawan_list.append({
                    'id': row[0],
                    'nama': row[1],
                    'email': row[2],
                    'divisi': row[3]
                })
        
        cursor.close()
        conn.close()
        
        return render_template('presensi.html', karyawan=karyawan_list)
        
    except Exception as e:
        print(f"Error in presensi route: {e}")
        return render_template('presensi.html', karyawan=[])

@app.route('/dashboard')
def dashboard():
    conn = get_db_connection()
    
    database_url = os.getenv('DATABASE_URL')
    is_postgres = database_url and database_url.startswith('postgresql://')
    
    today = date.today()
    
    try:
        if is_postgres:
            import psycopg2.extras
            cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            
            # Get statistics
            cursor.execute('''
                SELECT 
                    COUNT(DISTINCT karyawan_id) as total_hadir,
                    (SELECT COUNT(*) FROM karyawan) as total_karyawan,
                    COUNT(CASE WHEN status != 'Hadir' THEN 1 END) as total_tidak_hadir
                FROM presensi 
                WHERE tanggal = %s
            ''', (today,))
            stats = cursor.fetchone()
            
            # Get today's attendance
            cursor.execute('''
                SELECT k.nama, k.divisi, p.waktu_masuk, p.waktu_keluar, p.status, p.keterangan
                FROM presensi p
                JOIN karyawan k ON p.karyawan_id = k.id
                WHERE p.tanggal = %s
                ORDER BY p.waktu_masuk DESC
            ''', (today,))
            presensi_hari_ini = cursor.fetchall()
            
            # Convert to list of dicts
            presensi_list = []
            for row in presensi_hari_ini:
                presensi_list.append(dict(row))
                
            stats_dict = dict(stats) if stats else {
                'total_hadir': 0,
                'total_karyawan': 0,
                'total_tidak_hadir': 0
            }
            
        else:
            cursor = conn.cursor()
            
            # Get statistics
            cursor.execute('''
                SELECT 
                    COUNT(DISTINCT karyawan_id) as total_hadir,
                    (SELECT COUNT(*) FROM karyawan) as total_karyawan,
                    COUNT(CASE WHEN status != "Hadir" THEN 1 END) as total_tidak_hadir
                FROM presensi 
                WHERE tanggal = ?
            ''', (today,))
            stats = cursor.fetchone()
            
            # Get today's attendance
            cursor.execute('''
                SELECT k.nama, k.divisi, p.waktu_masuk, p.waktu_keluar, p.status, p.keterangan
                FROM presensi p
                JOIN karyawan k ON p.karyawan_id = k.id
                WHERE p.tanggal = ?
                ORDER BY p.waktu_masuk DESC
            ''', (today,))
            presensi_hari_ini = cursor.fetchall()
            
            # Convert to list of dicts
            presensi_list = []
            for row in presensi_hari_ini:
                presensi_list.append({
                    'nama': row[0],
                    'divisi': row[1],
                    'waktu_masuk': row[2],
                    'waktu_keluar': row[3],
                    'status': row[4],
                    'keterangan': row[5]
                })
                
            stats_dict = {
                'total_hadir': stats[0] if stats else 0,
                'total_karyawan': stats[1] if stats else 0,
                'total_tidak_hadir': stats[2] if stats else 0
            }
        
        cursor.close()
        conn.close()
        
        return render_template('dashboard.html', 
                             stats=stats_dict, 
                             presensi_hari_ini=presensi_list,
                             today=today.strftime('%d %B %Y'))
        
    except Exception as e:
        print(f"Error in dashboard route: {e}")
        return render_template('dashboard.html', 
                             stats={'total_hadir': 0, 'total_karyawan': 0, 'total_tidak_hadir': 0}, 
                             presensi_hari_ini=[],
                             today=today.strftime('%d %B %Y'))

# API Routes
@app.route('/api/checkin', methods=['POST'])
def checkin():
    data = request.get_json()
    
    conn = get_db_connection()
    database_url = os.getenv('DATABASE_URL')
    is_postgres = database_url and database_url.startswith('postgresql://')
    
    try:
        cursor = conn.cursor()
        
        # Check if already checked in today
        if is_postgres:
            cursor.execute('SELECT id FROM presensi WHERE karyawan_id = %s AND tanggal = %s', 
                          (data['karyawan_id'], date.today()))
        else:
            cursor.execute('SELECT id FROM presensi WHERE karyawan_id = ? AND tanggal = ?', 
                          (data['karyawan_id'], date.today()))
        
        existing = cursor.fetchone()
        
        if existing:
            return jsonify({'success': False, 'message': 'Sudah check-in hari ini'})
        
        # Insert check-in record
        if is_postgres:
            cursor.execute('''
                INSERT INTO presensi (karyawan_id, waktu_masuk, status, keterangan, lokasi)
                VALUES (%s, %s, %s, %s, %s)
            ''', (data['karyawan_id'], 
                  datetime.now().strftime('%H:%M:%S'), 
                  data.get('status', 'Hadir'), 
                  data.get('keterangan', ''), 
                  data.get('lokasi', 'Kantor')))
        else:
            cursor.execute('''
                INSERT INTO presensi (karyawan_id, waktu_masuk, status, keterangan, lokasi)
                VALUES (?, ?, ?, ?, ?)
            ''', (data['karyawan_id'], 
                  datetime.now().strftime('%H:%M:%S'), 
                  data.get('status', 'Hadir'), 
                  data.get('keterangan', ''), 
                  data.get('lokasi', 'Kantor')))
        
        conn.commit()
        return jsonify({'success': True, 'message': 'Check-in berhasil'})
        
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'message': str(e)})
    finally:
        cursor.close()
        conn.close()

@app.route('/api/checkout', methods=['POST'])
def checkout():
    data = request.get_json()
    
    conn = get_db_connection()
    database_url = os.getenv('DATABASE_URL')
    is_postgres = database_url and database_url.startswith('postgresql://')
    
    try:
        cursor = conn.cursor()
        
        # Update check-out time
        if is_postgres:
            cursor.execute('''
                UPDATE presensi 
                SET waktu_keluar = %s 
                WHERE karyawan_id = %s AND tanggal = %s AND waktu_keluar IS NULL
            ''', (datetime.now().strftime('%H:%M:%S'), 
                  data['karyawan_id'], 
                  date.today()))
        else:
            cursor.execute('''
                UPDATE presensi 
                SET waktu_keluar = ? 
                WHERE karyawan_id = ? AND tanggal = ? AND waktu_keluar IS NULL
            ''', (datetime.now().strftime('%H:%M:%S'), 
                  data['karyawan_id'], 
                  date.today()))
        
        if cursor.rowcount == 0:
            return jsonify({'success': False, 'message': 'Belum check-in hari ini'})
        
        conn.commit()
        return jsonify({'success': True, 'message': 'Check-out berhasil'})
        
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'message': str(e)})
    finally:
        cursor.close()
        conn.close()

@app.route('/api/presensi/<int:karyawan_id>')
def get_presensi(karyawan_id):
    conn = get_db_connection()
    database_url = os.getenv('DATABASE_URL')
    is_postgres = database_url and database_url.startswith('postgresql://')
    
    try:
        if is_postgres:
            import psycopg2.extras
            cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cursor.execute('''
                SELECT tanggal, waktu_masuk, waktu_keluar, status 
                FROM presensi 
                WHERE karyawan_id = %s 
                ORDER BY tanggal DESC 
                LIMIT 10
            ''', (karyawan_id,))
            presensi_data = cursor.fetchall()
            result = [dict(row) for row in presensi_data]
        else:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT tanggal, waktu_masuk, waktu_keluar, status 
                FROM presensi 
                WHERE karyawan_id = ? 
                ORDER BY tanggal DESC 
                LIMIT 10
            ''', (karyawan_id,))
            presensi_data = cursor.fetchall()
            result = []
            for row in presensi_data:
                result.append({
                    'tanggal': row[0],
                    'waktu_masuk': row[1],
                    'waktu_keluar': row[2],
                    'status': row[3]
                })
        
        cursor.close()
        conn.close()
        return jsonify(result)
        
    except Exception as e:
        print(f"Error getting presensi: {e}")
        return jsonify([])

@app.route('/api/dashboard/stats')
def dashboard_stats():
    conn = get_db_connection()
    database_url = os.getenv('DATABASE_URL')
    is_postgres = database_url and database_url.startswith('postgresql://')
    
    today = date.today()
    
    try:
        cursor = conn.cursor()
        
        # Total karyawan
        if is_postgres:
            cursor.execute('SELECT COUNT(*) as total FROM karyawan')
            total_karyawan = cursor.fetchone()[0]
            
            # Hadir hari ini
            cursor.execute('''
                SELECT COUNT(DISTINCT karyawan_id) as hadir 
                FROM presensi 
                WHERE tanggal = %s AND status = 'Hadir'
            ''', (today,))
            hadir_hari_ini = cursor.fetchone()[0]
            
            # Total presensi all time
            cursor.execute('SELECT COUNT(*) as total FROM presensi')
            total_presensi = cursor.fetchone()[0]
        else:
            cursor.execute('SELECT COUNT(*) as total FROM karyawan')
            total_karyawan = cursor.fetchone()[0]
            
            # Hadir hari ini
            cursor.execute('''
                SELECT COUNT(DISTINCT karyawan_id) as hadir 
                FROM presensi 
                WHERE tanggal = ? AND status = "Hadir"
            ''', (today,))
            hadir_hari_ini = cursor.fetchone()[0]
            
            # Total presensi all time
            cursor.execute('SELECT COUNT(*) as total FROM presensi')
            total_presensi = cursor.fetchone()[0]
        
        # Calculate attendance rate
        attendance_rate = round((hadir_hari_ini / total_karyawan * 100) if total_karyawan > 0 else 0)
        
        stats = {
            'total_karyawan': total_karyawan,
            'hadir_hari_ini': hadir_hari_ini,
            'total_presensi': total_presensi,
            'rata_kehadiran': attendance_rate
        }
        
        cursor.close()
        conn.close()
        return jsonify(stats)
        
    except Exception as e:
        print(f"Error getting stats: {e}")
        return jsonify({
            'total_karyawan': 0,
            'hadir_hari_ini': 0,
            'total_presensi': 0,
            'rata_kehadiran': 0
        })

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint tidak ditemukan'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Terjadi kesalahan internal server'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)