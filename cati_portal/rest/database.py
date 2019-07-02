from typing import List, NoReturn

def init_api(api):
    @api.schema
    class SqlChangeset:
        name: str
        sql_changesets: List[str]

    @api.schema
    class SqlModel:
        name: str
        sql_changesets: List[SqlChangeset]

    sql_models = api.path('/sql_models')

    @sql_models
    def get() -> List[str]:
        "list all SQL model names"
        with get_cursor() as cursor:
            cursor.execute('SELECT name FROM cati_portal.sql_model')
            result = [i[0] for i in cursor]
        return result
                

    @sql_models(param_in_body=True)
    def post(sql_model: SqlModel) -> NoReturn:
        "create a new SQL model"

    sql_model = api.path('/sql_models/{sql_model_id}')

    @sql_model
    def get(sql_model_id: str) -> SqlModel:
        "get SQL model content"

    @sql_model(param_in_body=True)
    def post(sql_model_id: str, sql_changeset: str) -> NoReturn:
        "adds a new SQL changeset to an SQL model"

    @sql_model
    def delete(sql_model_id: str) -> NoReturn:
        "delete an SQL model"
