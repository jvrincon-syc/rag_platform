"""Discover rag_releases columns + docs_with_embeds."""
import sys
sys.path.insert(0, "C:/Users/jvrincon/Documents/chatbot_sst/chatbot-sst/app/back/src")
import psycopg2

conn = psycopg2.connect(host="127.0.0.1", dbname="chatbot_sst", user="postgres", password="Fitomega4366_syc")
conn.autocommit = True
cur = conn.cursor()

# Discover rag_releases columns
cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'rag_releases' ORDER BY ordinal_position")
cols = cur.fetchall()
print("=== rag_releases columns ===")
for c in cols:
    print(f"  {c[0]:30s} {c[1]}")

# List ALL tables matching 'rag' or 'release'
cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND (table_name LIKE 'rag%' OR table_name LIKE 'release%' OR table_name LIKE 'idx%') ORDER BY table_name")
print("\n=== rag/release/index tables ===")
for row in cur.fetchall():
    print(f"  {row[0]}")

# chunk_bundles column names
cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'chunk_bundles' ORDER BY ordinal_position")
print("\n=== chunk_bundles columns ===")
for c in cur.fetchall():
    print(f"  {c[0]:30s} {c[1]}")

# embedding_bundles column names
cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'embedding_bundles' ORDER BY ordinal_position")
print("\n=== embedding_bundles columns ===")
for c in cur.fetchall():
    print(f"  {c[0]:30s} {c[1]}")

# physical vector tables
cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND table_name LIKE 'idx_%' ORDER BY table_name")
print("\n=== idx_ vector tables ===")
for row in cur.fetchall():
    print(f"  {row[0]}")
    cur2 = conn.cursor()
    cur2.execute(f"SELECT COUNT(*) FROM {row[0]}")
    print(f"    rows = {cur2.fetchone()[0]}")
    cur2.close()

# indexing_nodes breakdown
cur.execute("SELECT node_role, COUNT(*) FROM indexing_nodes GROUP BY node_role ORDER BY node_role")
print("\n=== indexing_nodes by role ===")
for row in cur.fetchall():
    print(f"  {row[0]:20s} = {row[1]}")

conn.close()
