#!/usr/bin/env python3
"""
Migration script to update orders table for guest orders support.
This script modifies the user_id column to allow NULL values for guest orders.
"""

import sqlite3
import os
from pathlib import Path

def migrate_sqlite():
    """Migrate SQLite database to support guest orders."""
    db_path = Path("ecommerce.db")
    
    if not db_path.exists():
        print("Database file not found. Creating new database...")
        return
    
    print("Migrating SQLite database for guest orders support...")
    
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if the orders table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='orders'")
        if not cursor.fetchone():
            print("Orders table not found. Skipping migration.")
            return
        
        # Check if user_id column already allows NULL
        cursor.execute("PRAGMA table_info(orders)")
        columns = cursor.fetchall()
        user_id_column = None
        
        for col in columns:
            if col[1] == 'user_id':
                user_id_column = col
                break
        
        if user_id_column:
            # Check if the column already allows NULL
            if user_id_column[3] == 0:  # 0 means NOT NULL, 1 means NULL allowed
                print("Updating user_id column to allow NULL values...")
                
                # Create a temporary table with the new schema
                cursor.execute("""
                    CREATE TABLE orders_temp (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
                        total_amount REAL NOT NULL,
                        status TEXT NOT NULL DEFAULT 'pending',
                        shipping_address TEXT NOT NULL,
                        contact_name TEXT NOT NULL,
                        contact_email TEXT NOT NULL,
                        contact_phone TEXT,
                        payment_method TEXT NOT NULL,
                        special_instructions TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users (id)
                    )
                """)
                
                # Copy data from old table to new table
                cursor.execute("""
                    INSERT INTO orders_temp 
                    SELECT * FROM orders
                """)
                
                # Drop the old table
                cursor.execute("DROP TABLE orders")
                
                # Rename the new table
                cursor.execute("ALTER TABLE orders_temp RENAME TO orders")
                
                print("Migration completed successfully!")
            else:
                print("user_id column already allows NULL values. No migration needed.")
        else:
            print("user_id column not found in orders table.")
            
    except Exception as e:
        print(f"Migration failed: {e}")
        conn.rollback()
    finally:
        conn.commit()
        conn.close()

def migrate_postgresql():
    """Migrate PostgreSQL database to support guest orders."""
    print("For PostgreSQL migration, please run the following SQL command:")
    print("ALTER TABLE orders ALTER COLUMN user_id DROP NOT NULL;")
    print("This will allow NULL values in the user_id column for guest orders.")

if __name__ == "__main__":
    print("Guest Orders Migration Script")
    print("=" * 40)
    
    # Check if we're using SQLite or PostgreSQL
    if os.path.exists("ecommerce.db"):
        migrate_sqlite()
    else:
        migrate_postgresql()
    
    print("\nMigration script completed!")
