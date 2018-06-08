class StudyManager:
    @staticmethod
    def create(db, id, label, description, properties):
        pass

    def __init__(self, db, id):
        with db:
            with db.cursor() as cur:
                sql = 'SELECT label, description, properties FROM cati_manager.study WHERE id=%s;'
                cur.execute(sql, [id])
                if cur.rowcount == 0:
                    raise ValueError('Unknown study identifier : %s' % id)
                row = cur.fetchone()
        for k, v in row[2].items():
            setattr(self, k, v)
        self.id = id
        self.label = row[0]
        self.description = row[1]
        
    def update(self, db):
        pass
    