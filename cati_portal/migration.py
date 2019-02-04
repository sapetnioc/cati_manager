import glob
import importlib
import os.path as osp
import re

_changesets_splitter = re.compile(r'\s*--\s*cati_portal\s+changeset\s*:\s*([^\s]*)')


def sql_changesets(module):
    '''
    Find all the SQL changesets defined in a given module. The module must be
    a Python package (i.e. a directory). The changesets are define in any
    *.sql.yaml files defined in the module (recursive search). An *.sql.yaml
    file must contains a dictionary with the following items:
      changesets: a list of dictionaries containing two items :
                  'id' is an identifier that must be unique among all the
                  identifier of the module.
                  'sql' is the SQL code that is executed to apply the
                  changeset.
    '''
    global _changesets_splitter
    basedir = osp.dirname(importlib.import_module(module).__file__)
    ids = dict()
    for sql_file in sorted(glob.iglob(osp.join(basedir, '**', '*.sql'),
                                      recursive=True)):
        changesets = _changesets_splitter.split(open(sql_file).read())
        if changesets[0].strip():
            raise ValueError('File %s does not start with "-- cati_portal changeset:"' % sql_file)
        del changesets[0]
        while changesets:
            id = changesets.pop(0)
            sql = changesets.pop(0)
            if id in ids:
                raise ValueError('In file %s, changeset "%s" already defined in %s' % (sql_file, id, ids[id]))
            ids[id] = sql_file
            yield (id, sql)
