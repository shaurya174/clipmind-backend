from database import Base, engine

# Import ALL SQLAlchemy models here
from models import Job
from app.auth.models import AuthToken, User, UserVideoHistory, Video


def init_db():
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully.")


if __name__ == "__main__":
    init_db()