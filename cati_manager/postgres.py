import psycopg2

connections = {}
def connect(database_url, database_user, database_password, target_user):
    global connections
    
    connection = connections.get((database_url, target_user))
    if connection is None:
        connection = psycopg2.connect(database_url, user=database_user, password=database_password)
        if target_user is not None:
            connection.cursor().execute('SET ROLE ?;', (target_user,))
            connection.commit()
            connections[(database_url, target_user)] = connection
    return connection

def rconnect(request, user=None):
    database_url = request.registry.settings['cati_manager.database']
    database_user = request.registry.settings['cati_manager.database_user']
    database_password = request.registry.settings['cati_manager.database_password']
    return connect(database_url, database_user, database_password, user)

def authentication_callback(login, request):
    '''
    ldap_authentication_callback can be used as callback for
    AuthTktAuthenticationPolicy. It checks user password and 
    returns either None if the user is not authenticated or a
    list composed of the user login and the groups it
    belongs to (each group name is added a prefix 'group:').
    '''
    with rconnect(request) as db:
        with db.cursor() as cur:
            cur.execute('SELECT DISTINCT credential.project, credential.id FROM identity, granting, project, credential WHERE identity.login=%s AND granting.login = identity.login AND credential.id = granting.credential', (login,))
            principals = ['%s_%s' % i for i in cur]
    return [ login ] + principals
 