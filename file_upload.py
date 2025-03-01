import os
import mysql.connector
import database_setup as db
import shutil

def get_db_connection():
    return mysql.connector.connect(
        host=db.DB_HOST,
        user=db.DB_USER,
        password=db.DB_PASSWORD,
        database=db.DB_NAME
    )

def upload_file(email, file_path):
    # Get file information
    filename = os.path.basename(file_path)
    
    # Connect to database
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check database structure to see available columns
    cursor.execute("DESCRIBE files")
    columns = [column[0] for column in cursor.fetchall()]
    
    # Get user_id from email
    cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
    user_result = cursor.fetchone()
    
    if not user_result:
        print("❌ User not found!")
        cursor.close()
        conn.close()
        return False
    
    user_id = user_result[0]
    
    # Check if file with same name already exists for this user
    cursor.execute("SELECT id FROM files WHERE user_id = %s AND filename = %s", (user_id, filename))
    if cursor.fetchone():
        print(f"❌ A file with the name '{filename}' already exists!")
        cursor.close()
        conn.close()
        return False
    
    # Create user directory if it doesn't exist
    user_dir = os.path.join("uploads", str(user_id))
    if not os.path.exists(user_dir):
        os.makedirs(user_dir)
    
    # Copy file to user directory
    destination = os.path.join(user_dir, filename)
    try:
        shutil.copy2(file_path, destination)
    except Exception as e:
        print(f"❌ Error copying file: {e}")
        cursor.close()
        conn.close()
        return False
    
    # Add file record to database - adapt this to match your actual table structure
    try:
        # Check if file_size exists in the table
        if 'file_size' in columns:
            file_size = os.path.getsize(file_path)
            cursor.execute(
                "INSERT INTO files (user_id, filename, file_size, file_path, is_hidden) VALUES (%s, %s, %s, %s, %s)",
                (user_id, filename, file_size, destination, 0)
            )
        else:
            # If file_size doesn't exist, use only available columns
            cursor.execute(
                "INSERT INTO files (user_id, filename, file_path, is_hidden) VALUES (%s, %s, %s, %s)",
                (user_id, filename, destination, 0)
            )
        conn.commit()
    except Exception as e:
        print(f"❌ Database error: {e}")
        os.remove(destination)  # Remove the copied file if database insert fails
        cursor.close()
        conn.close()
        return False
    
    cursor.close()
    conn.close()
    return True