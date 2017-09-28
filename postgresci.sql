CREATE OR REPLACE LANGUAGE plpython3u;

-- CREATE ROLE postgresci NOINHERIT NOLOGIN;
CREATE ROLE postgresci NOLOGIN;

CREATE SCHEMA postgresci;
GRANT ALL ON SCHEMA postgresci TO postgresci;

SET search_path = postgresci, pg_catalog;


CREATE FUNCTION check_python_module()
    RETURNS void
AS $BODY$
    '''
    This function makes sure the postgresci module is loaded and can be 
    imported. In a plpython3u Postgres function, use the following code:
    
    plpy.execute('SELECT postgresci.check_python_module();')
    import postgresci
    '''
    try:
        import postgresci
    except ImportError:
        import sys, types
        postgresci = types.ModuleType('postgresci')
        sys.modules['postgresci'] = postgresci
        module_script = '''
import os
import os.path as osp
import re

#debug = debug = open('/tmp/debug', 'w')

def find_new_changesets(plpy, project, component, database_schema):
    #import postgresci
    #print('!find_new_changesets!', project, component, database_schema, file=postgresci.debug)
    sql = "SELECT path, required_version FROM postgresci.project WHERE name = '{0}'".format(project)
    r = plpy.execute(sql)
    if r.nrows():
        path = r[0]['path']
        required_version = r[0]['required_version']
    else:
        raise ValueError('Cannot find postgresci project named "{0}"'.format(project))
    sql = "SELECT installed_version FROM postgresci.installed_component WHERE project = '{0}' AND component = '{1}' AND database_schema = '{2}'".format(project, component, database_schema)
    r = plpy.execute(sql)
    if r.nrows():
        installed_version = r[0]['installed_version']
        if installed_version is not None:
            installed_version_tuple = tuple(int(i) for i in row['installed_version'][1:-1].split(','))
        else:
            installed_version_tuple = None
    else:
        installed_version_tuple = None
    is_version = re.compile(r'^(\d+)\.(\d+)\.(\d+)$')
    if required_version in ('latest', 'devel'):
        required_version_tuple = None
    else:
        m = is_version.match(req_version)
        if m:
            required_version_tuple = tuple(int(i) for i in m.groups())
        else:
            raise ValueError('"%s" is not a valid version for project "%s" (use three '
                            'integers separated by dots (e.g. "4.5.6") or '
                            '"latest" or "devel")' % (required_version, project))
    versions = []
    #print('!find_new_changesets! listdir', path, os.listdir(path), file=postgresci.debug)
    for i in os.listdir(path):
        m = is_version.match(i)
        if m and osp.isdir(osp.join(path,i)):
            version_tuple = tuple(int(i) for i in m.groups())
            versions.append(version_tuple)
    if versions:
        versions = sorted(versions)
    #print('!find_new_changesets! versions', versions, file=postgresci.debug)
    for version_tuple in versions:
        if (installed_version_tuple is None or installed_version_tuple < version_tuple) and \
           (required_version_tuple is None or required_version_tuple >= version_tuple):
            sql_path = osp.join(path, '%d.%d.%d' % version_tuple, '%s.sql' % component)
            #print('!find_new_changesets! sql_path', sql_path, file=postgresci.debug)
            if osp.exists(sql_path):
                #print('!find_new_changesets! yield', (version_tuple, sql_path), file=postgresci.debug)
                yield (version_tuple, sql_path)
    if required_version == 'devel':
            sql_path = osp.join(path, 'devel', '%s.sql' % component)
            if osp  .exists(sql_path):
                #print('!find_new_changesets! yield', (None, sql_path), file=postgresci.debug)
                yield (None, sql_path)
'''
        # Postgresql adds indentation to the code above. I need to remove it.
        module_script = module_script.split('\n')
        indent = module_script[1].index('import')
        module_script = '\n'.join(i[indent:] for i in module_script)
        exec(module_script, postgresci.__dict__, postgresci.__dict__)
    #postgresci.debug.flush()
    
$BODY$
  LANGUAGE plpython3u;


CREATE TYPE version AS (
    major INTEGER,
    minor INTEGER,
    patch INTEGER
);

CREATE TABLE project
(
    name TEXT NOT NULL PRIMARY KEY,
    path TEXT NOT NULL,
    required_version text NOT NULL
--  required_version can be three integers separated by dots (e.g. "1.3.5") or the constants "latest" or "devel".
);
GRANT ALL ON TABLE project TO postgresci;

CREATE TABLE installed_component
(
    project TEXT NOT NULL REFERENCES project ( name ),
    component TEXT NOT NULL,
    database_schema TEXT NOT NULL,
    installed_version version,
--  if installed_version is NULL it means that unversioned devel changeset was installed.    
    PRIMARY KEY (project, component, database_schema)
);
GRANT ALL ON TABLE installed_component TO postgresci;


CREATE FUNCTION install_component()
    RETURNS TRIGGER
AS $BODY$
    plpy.execute('SELECT postgresci.check_python_module();')
    import postgresci
    
    project = TD['new']['project']
    component = TD['new']['component']
    database_schema = TD['new']['database_schema']
    if TD['new']['installed_version'] is not None:
        raise ValueError('No installed_version value must be given when inserting in installed_component table. This value is set automatically by a trigger function')
    
    # Check that schema exists
    r = plpy.execute("select EXISTS(SELECT * FROM information_schema.schemata WHERE schema_name='%s') AS found_schema;" % database_schema)
    if not r[0]['found_schema']:
        raise ValueError('Schema "%s" does not exist' % database_schema)
    # Temporarily modify search_path to put the targeted schema first
    search_path = plpy.execute('SHOW search_path;')[0]['search_path']
    try:
        plpy.execute('SET search_path = %s, pg_catalog;' % database_schema)
        
        version = None
        for version, sql_file in postgresci.find_new_changesets(plpy, project, component, database_schema):
            plpy.execute(open(sql_file).read().replace('{{target_schema}}', database_schema))
        if version is not None:
            result = 'MODIFY'
            TD['new']['installed_version'] = version
        else:
            result = 'OK'
    finally:
        plpy.execute('SET search_path = %s;' % search_path)
    return result

$BODY$
  LANGUAGE plpython3u;


CREATE TRIGGER install_component
  BEFORE INSERT
  ON installed_component
  FOR EACH ROW
  EXECUTE PROCEDURE install_component();

  
CREATE FUNCTION update_schema(schema_name_p TEXT DEFAULT NULL, 
                              postgresci_name TEXT DEFAULT NULL,
                              required_version text DEFAULT NULL)
    RETURNS void
AS $BODY$
    import os
    import re
    import os.path as osp
    import glob

    if required_version:
        # In postgresql functions parameters should be consider as read-only. 
        # Therefore req_version is used instead of required_version.
        req_version = required_version.lower()
        if req_version in ('latest', 'devel'):
            version_tuple = None
        else:
            m = re.match(r'^(\d+)\.(\d+)\.(\d+)$', req_version)
            if m:
                version_tuple = tuple(int(i) for i in m.groups())
            else:
                raise ValueError('"%s" is not a valid version request (use three '
                                'integers separated by dots (e.g. "4.5.6") or '
                                '"latest" or "devel")' % required_version)
    else:
        req_version = None
        version_tuple = None
                                
    # Find installed postgresci
    where = []
    if schema_name_p:
        where.append("schema_name='%s'" % schema_name_p)
    if postgresci_name:
        where.append("name='%s'" % postgresci_name)
    if where:
        where = ' WHERE %s' % ' AND '.join(where)
    else:
        where =''
    for row in plpy.execute('SELECT * FROM postgresci.installed_schema%s;' % where):
        schema_name = row['database_schema']
        name = row['name']
        path = row['path']
        if row['installed_version'] is None:
            if req_version and req_version != 'devel':
                raise ValueError('Impossible to update changing schema "%s" to version "%s" in Postgres schema "%s" because "devel" version is already installed and there is no way to uninstall it.' % (row['name'], req_version, schema_name))
            else:
                continue
        installed_version_tuple = tuple(int(i) for i in row['installed_version'][1:-1].split(','))
        installed_version_str = '%d.%d.%d' % installed_version_tuple
        if version_tuple and installed_version_tuple > version_tuple:
            raise ValueError('Impossible to update changing schema "%s" to version "%s" in Postgres schema "%s" because "%s" version is already installed and there is no way to uninstall it.' % (row['name'], req_version, schema_name, installed_version_str))    
    
        if not req_version and row['required_version'] not in ('latest', 'devel'):
            continue

        if req_version and row['required_version'] != req_version:
            plpy.execute("UPDATE postgresci.installed_schema SET required_version='{2}' WHERE database_schema='{0}' AND name='{1}'".format(schema_name, name, req_version))
        
        
        # Update the schema
        search_path = plpy.execute('SHOW search_path;')[0]['search_path']
        try:
            plpy.execute('SET search_path = %s, pg_catalog;' % schema_name)
            sql_files = glob.glob(osp.join(path, '%s-*.sql' % name))
            changesets = []
            version_re = re.compile(r'.*%s%s-(\d+)\.(\d+)\.(\d+)\.sql$' % (osp.sep, name))
            for file in sql_files:
                m = version_re.match(file)
                if m:
                    changeset_version = tuple(int(i) for i in m.groups())
                    if (version_tuple and changeset_version > version_tuple) or (installed_version_tuple >= changeset_version):
                        continue
                changesets.append((changeset_version, file))
            changesets = sorted(changesets)
            for version, file in changesets:
                plpy.execute(open(file).read().replace('{{target_schema}}', schema_name))
                plpy.execute("UPDATE postgresci.installed_schema SET installed_version={2} WHERE database_schema='{0}' AND name='{1}'".format(schema_name, name, '(%d,%d,%d)' % version))
            devel_changeset_file = osp.join(path, '%s.sql' % name)
            if req_version == 'devel' and osp.exists(devel_changeset_file):
                plpy.execute(open(devel_changeset_file).read().replace('{{target_schema}}', schema_name))
                plpy.execute("UPDATE postgresci.installed_schema SET installed_version=NULL WHERE database_schema='{0}' AND name='{1}'".format(schema_name, name))
            elif req_version == 'devel':
                raise RuntimeError(devel_changeset_file)
        finally:
            plpy.execute('SET search_path = %s;' % search_path)
$BODY$
  LANGUAGE plpython3u;
