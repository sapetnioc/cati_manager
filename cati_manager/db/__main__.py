# Initialize the database
import sys

import pgpy
import psycopg2

from cati_manager.migration import sql_changesets

with psycopg2.connect(sys.argv[1]) as db:
    with db.cursor() as cur:
        for id, sql in sql_changesets('cati_manager.db'):
            cur.execute(sql)

        public_key, other = pgpy.PGPKey.from_file('/cati_portal/gpg/public.key')
        sql = "INSERT INTO cati_manager.pgp_public_keys (name, pgp_key) VALUES ('cati_manager', %s);"
        cur.execute(sql, [bytes(public_key)])
        
        db.commit()
        
        for id, sql in sql_changesets('cati_manager.install'):
            print(sql)
            cur.execute(sql)
        