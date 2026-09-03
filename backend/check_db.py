import sqlite3

# Connect to the database
conn = sqlite3.connect('database.db')
cursor = conn.cursor()

# Query equipment table
cursor.execute("SELECT id, name, image_filename FROM equipment")
equipment_rows = cursor.fetchall()

print("Equipment in database:")
for row in equipment_rows:
    print(f"ID: {row[0]}, Name: {row[1]}, Image: {row[2]}")

conn.close()