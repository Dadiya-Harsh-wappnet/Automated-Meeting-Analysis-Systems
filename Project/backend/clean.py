# from models import db
# db.session.commit()
# db.session.flush()
# db.Model.metadata.reflect(bind=db.engine)
import secrets
print(secrets.token_hex(32))  # Secure 64-character key
