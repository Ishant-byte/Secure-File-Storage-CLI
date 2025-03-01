import os
import shutil
import mysql.connector
import database_setup as db

def get_db_connection():
    return mysql.connector.connect(
        host=db.DB_HOST,
        user=db.DB_USER,
        password=db.DB_PASSWORD,
        database=db.DB_NAME
    )

def download_file(email, filename):
    # Connect to database
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get user_id and file information
    cursor.execute("""
        SELECT f.id, f.file_path 
        FROM files f 
        JOIN users u ON f.user_id = u.id 
        WHERE u.email = %s AND f.filename = %s AND f.is_hidden = 0
    """, (email, filename))
    
    file_result = cursor.fetchone()
    
    if not file_result:
        print(f"❌ File '{filename}' not found or is hidden!")
        cursor.close()
        conn.close()
        return False
    
    file_id, file_path = file_result
    
    # Check if the file exists in the filesystem
    if not os.path.exists(file_path):
        print(f"❌ File not found on server! Please contact administrator.")
        cursor.close()
        conn.close()
        return False
    
    # Create downloads directory if it doesn't exist
    downloads_dir = "downloads"
    if not os.path.exists(downloads_dir):
        os.makedirs(downloads_dir)
    
    # Copy file to downloads directory
    destination = os.path.join(downloads_dir, filename)
    try:
        shutil.copy2(file_path, destination)
        print(f"📁 File saved to: {os.path.abspath(destination)}")
    except Exception as e:
        print(f"❌ Error downloading file: {e}")
        cursor.close()
        conn.close()
        return False
    
    # Update download count (optional)
    try:
        cursor.execute("UPDATE files SET download_count = download_count + 1 WHERE id = %s", (file_id,))
        conn.commit()
    except Exception:
        # Not critical if this fails
        pass
    
    cursor.close()
    conn.close()
    return True