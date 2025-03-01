import mysql.connector
import os

# Database configuration
DB_HOST = "localhost"
DB_USER = "root"
DB_PASSWORD = ""  # Set your MySQL password here
DB_NAME = "secure_file_storage"

def setup_database():
    """Create the database and required tables if they don't exist."""
    # First connect without specifying a database
    conn = mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD
    )
    cursor = conn.cursor()
    
    # Create database if it doesn't exist
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
    cursor.execute(f"USE {DB_NAME}")
    
    # Create users table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INT AUTO_INCREMENT PRIMARY KEY,
        username VARCHAR(50) NOT NULL,
        email VARCHAR(100) NOT NULL UNIQUE,
        password_hash VARCHAR(255) NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Create files table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS files (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT NOT NULL,
        filename VARCHAR(255) NOT NULL,
        file_size BIGINT NOT NULL,
        file_path VARCHAR(512) NOT NULL,
        is_hidden TINYINT(1) DEFAULT 0,
        download_count INT DEFAULT 0,
        upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        UNIQUE KEY user_file (user_id, filename)
    )
    """)
    
    # Create OTP table for the local_otp module
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS otps (
        id INT AUTO_INCREMENT PRIMARY KEY,
        email VARCHAR(100) NOT NULL,
        otp VARCHAR(10) NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        INDEX (email)
    )
    """)
    
    # Commit changes and close connection
    conn.commit()
    cursor.close()
    conn.close()
    
    # Create upload and download directories
    os.makedirs("uploads", exist_ok=True)
    os.makedirs("downloads", exist_ok=True)
    
    print("✅ Database and tables setup complete!")

if __name__ == "__main__":
    setup_database()