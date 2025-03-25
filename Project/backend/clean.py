from models import db
db.session.commit()
db.session.flush()
db.Model.metadata.reflect(bind=db.engine)
