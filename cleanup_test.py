from app import get_db
con = get_db()
con.execute("DELETE FROM suggestions")
con.commit()
print("Suggestions table cleaned")
