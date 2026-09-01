"""Publish a RAG release: snapshot → draft → build → validate → publish."""
import sys, time, uuid
sys.path.insert(0, "C:/Users/jvrincon/Documents/chatbot_sst/chatbot-sst/app/back/src")

import psycopg2

conn = psycopg2.connect(host="127.0.0.1", dbname="chatbot_sst", user="postgres", password="Fitomega4366_syc")
conn.autocommit = True
cur = conn.cursor()

# Discover project_id + rag_variant_id + document revision IDs
cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='rag_projects' ORDER BY ordinal_position")
print("=== rag_projects columns ===")
for r in cur.fetchall(): print(f"  {r[0]}")

cur.execute("SELECT * FROM rag_projects")
print("\n=== rag_projects ===")
for r in cur.fetchall():
    print(f"  {r}")

cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='rag_variants' ORDER BY ordinal_position")
print("\n=== rag_variants columns ===")
for r in cur.fetchall(): print(f"  {r[0]}")

cur.execute("SELECT * FROM rag_variants")
print("\n=== rag_variants ===")
for r in cur.fetchall():
    print(f"  {r}")

# Document revisions (needed for snapshot)
cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='project_documents' ORDER BY ordinal_position")
print("\n=== project_documents columns ===")
for r in cur.fetchall(): print(f"  {r[0]}")

cur.execute("SELECT * FROM project_documents LIMIT 3")
print("\n=== project_documents (sample) ===")
for r in cur.fetchall():
    print(f"  {r}")

cur.execute("SELECT COUNT(*) FROM project_documents")
print(f"\n  total raw docs = {cur.fetchone()[0]}")

# Check for any existing build steps
cur.execute("SELECT build_run_id, rag_release_id, state, started_at, completed_at FROM rag_build_steps ORDER BY started_at DESC LIMIT 3")
print("\n=== rag_build_steps (recent) ===")
for r in cur.fetchall():
    print(f"  run={r[0]} release={r[1]} state={r[2]} started={r[3]} completed={r[4]}")

# Build jobs
cur.execute("SELECT build_job_id, rag_release_id, state FROM release_build_jobs ORDER BY created_at DESC LIMIT 3")
print("\n=== release_build_jobs ===")
for r in cur.fetchall():
    print(f"  job={r[0]} release={r[1]} state={r[2]}")

conn.close()
