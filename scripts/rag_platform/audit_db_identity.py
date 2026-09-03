from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "indexing"))

from prepare_postgres_indexing import load_env_file  # noqa: E402


_DB_NAME = re.compile(r"^[a-z_][a-z0-9_]{0,62}$")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit local PostgreSQL database identity without printing secrets."
    )
    parser.add_argument("--env-file", default="secrets.env")
    parser.add_argument("--expected-db", default="rag_platform")
    parser.add_argument("--legacy-db", default="chatbot_sst")
    parser.add_argument(
        "--rename-legacy-db",
        action="store_true",
        help="Rename legacy database to expected name when it is the only matching DB.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    for database_name in (args.expected_db, args.legacy_db):
        if not _DB_NAME.fullmatch(database_name):
            print("status=blocked reason=invalid_database_name")
            return 2
    env = load_env_file(ROOT / args.env_file)
    host = env.get("POSTGRES_HOST") or "localhost"
    port = env.get("POSTGRES_PORT") or "5432"
    user = env.get("POSTGRES_USER") or "postgres"
    password = env.get("POSTGRES_PASSWORD") or None

    try:
        import psycopg2
    except ImportError:
        print("status=blocked reason=psycopg2_missing")
        return 2

    connection = psycopg2.connect(
        host=host,
        port=port,
        dbname="postgres",
        user=user,
        password=password,
    )
    connection.autocommit = True
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                select datname
                from pg_database
                where datname in (%s, %s)
                order by datname
                """,
                (args.legacy_db, args.expected_db),
            )
            databases = [row[0] for row in cursor.fetchall()]

            cursor.execute(
                """
                select datname, count(*)
                from pg_stat_activity
                where datname in (%s, %s)
                group by datname
                order by datname
                """,
                (args.legacy_db, args.expected_db),
            )
            active = dict(cursor.fetchall())

            if (
                args.rename_legacy_db
                and args.legacy_db in databases
                and args.expected_db not in databases
            ):
                cursor.execute(
                    """
                    select pg_terminate_backend(pid)
                    from pg_stat_activity
                    where datname = %s
                      and pid <> pg_backend_pid()
                    """,
                    (args.legacy_db,),
                )
                cursor.execute(
                    f'alter database "{args.legacy_db}" rename to "{args.expected_db}"'
                )
                databases = [args.expected_db]
                active = {}
    finally:
        connection.close()

    print(f"expected_db={args.expected_db}")
    print(f"legacy_db={args.legacy_db}")
    print(f"databases={','.join(databases) if databases else 'none'}")
    print(
        "active_connections="
        + (
            ",".join(f"{name}:{active[name]}" for name in sorted(active))
            if active
            else "none"
        )
    )
    if args.expected_db in databases and args.legacy_db not in databases:
        print("status=ok")
        return 0
    if args.expected_db in databases and args.legacy_db in databases:
        print("status=review reason=both_expected_and_legacy_exist")
        return 1
    if args.legacy_db in databases:
        print("status=blocked reason=legacy_db_exists_without_expected_db")
        return 2
    print("status=blocked reason=expected_db_missing")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
