"""Quick read-only inventory of pipeline tables in chatbot_sst DB."""
import sys
sys.path.insert(0, "C:/Users/jvrincon/Documents/chatbot_sst/chatbot-sst/app/back/src")

import psycopg2

conn = psycopg2.connect(host="127.0.0.1", dbname="chatbot_sst", user="postgres", password="Fitomega4366_syc")
conn.autocommit = True
cur = conn.cursor()

tables = [
    ("raw",                "project_documents"),
    ("normalized",         "project_normalized_documents"),
    ("indexing_norm",      "indexing_normalized_documents"),
    ("chunk_bundles",      "chunk_bundles"),
    ("embedding_bundles",  "embedding_bundles"),
    ("embedding_chunks",   "embedding_bundle_chunks"),
    ("indexing_nodes",     "indexing_nodes"),
    ("releases",           "rag_releases"),
    ("release_docs",       "rag_release_documents"),
    ("indexing_runs",      "indexing_runs"),
]

print("=== PIPELINE TABLE COUNTS ===")
for label, table in tables:
    try:
        cur.execute(f"SELECT COUNT(*) FROM {table}")
        count = cur.fetchone()[0]
        print(f"  {label:20s} = {count}")
    except Exception as e:
        print(f"  {label:20s} = TABLE NOT FOUND")

# Chunk detail
try:
    cur.execute("SELECT COUNT(*) FROM chunk_bundles WHERE node_type = 'child'")
    print(f"  {'child_chunks':20s} = {cur.fetchone()[0]}")
    cur.execute("SELECT COUNT(*) FROM chunk_bundles WHERE node_type = 'parent'")
    print(f"  {'parent_chunks':20s} = {cur.fetchone()[0]}")
except:
    print("  chunk detail: table not found or error")

# Embedding status breakdown
try:
    cur.execute("SELECT status, COUNT(*) FROM embedding_bundles GROUP BY status ORDER BY status")
    for row in cur.fetchall():
        print(f"  {'embed_'+row[0]:20s} = {row[1]}")
except:
    print("  embedding status: error")

# Releases detail
try:
    cur.execute("SELECT id, version, status, created_at FROM rag_releases ORDER BY created_at DESC LIMIT 3")
    rows = cur.fetchall()
    print(f"\n=== RELEASES ===")
    for r in rows:
        print(f"  id={r[0]}, version={r[1]}, status={r[2]}, created={r[3]}")
except Exception as e:
    print(f"\n=== RELEASES === table not found: {e}")

# Physical vectors
try:
    cur.execute("SELECT COUNT(*) FROM idx_vec_local_bge_m3_v1")
    print(f"  {'physical_vectors':20s} = {cur.fetchone()[0]}")
except Exception as e:
    print(f"  physical_vectors = table not found")

# Embedding coverage: how many docs have embeddings vs total
try:
    cur.execute("""
        SELECT COUNT(DISTINCT pnd.document_id) as docs_with_norm,
               (SELECT COUNT(*) FROM project_documents) as total_raw
        FROM indexing_normalized_documents pnd
    """)
    norm, total_raw = cur.fetchone()
    print(f"\n=== COVERAGE ===")
    print(f"  docs with normalized = {norm} / {total_raw} raw")
except Exception as e:
    print(f"\n  normalized coverage: {e}")
    total_raw = 55

try:
    cur.execute("SELECT COUNT(DISTINCT source_document_id) FROM embedding_bundles")
    docs_with_embed = cur.fetchone()[0]
    print(f"  docs with embeddings = {docs_with_embed} / {total_raw} raw")
except:
    print("  docs with embeddings = error")

try:
    cur.execute("SELECT COUNT(DISTINCT source_document_id) FROM chunk_bundles")
    docs_with_chunks = cur.fetchone()[0]
    print(f"  docs with chunks     = {docs_with_chunks} / {total_raw} raw")
except:
    print("  docs with chunks = error")

# Vector index detail
try:
    cur.execute("SELECT source_bundle_id, COUNT(*) FROM idx_vec_local_bge_m3_v1 GROUP BY source_bundle_id ORDER BY source_bundle_id LIMIT 5")
    rows = cur.fetchall()
    print(f"\n=== VECTORS PER BUNDLE (sample) ===")
    for r in rows:
        print(f"  bundle={r[0]}  vectors={r[1]}")
    cur.execute("SELECT COUNT(*) FROM idx_vec_local_bge_m3_v1")
    print(f"  TOTAL physical vectors = {cur.fetchone()[0]}")
except Exception as e:
    print(f"\n  vector index table: not found")

conn.close()
