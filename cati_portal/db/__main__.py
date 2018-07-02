# Initialize the database
import sys

import pgpy
import psycopg2

from cati_portal.migration import sql_changesets
from cati_portal.authentication import pgp_public_key

with psycopg2.connect(sys.argv[1]) as db:
    with db.cursor() as cur:
        for id, sql in sql_changesets('cati_portal.db'):
            cur.execute(sql)

        sql = "INSERT INTO cati_portal.pgp_public_keys (name, pgp_key) VALUES ('cati_portal', %s);"
        cur.execute(sql, [bytes(pgp_public_key())])
        
        #db.commit()
        
        #for id, sql in sql_changesets('cati_portal.install'):
            #print(sql)
            #cur.execute(sql)
        