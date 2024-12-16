# app/tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import date, timedelta

from app.database import Base, get_db
from app.main import app
from app.models.chores import Child, Chore, ChoreAssignment

# Use SQLite for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session")
def db_engine():
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def db_session(db_engine):
    connection = db_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()

@pytest.fixture
def sample_data(db_session):
    # Create test children
    alice = Child(name="Alice", weekly_allowance=10.0)
    bob = Child(name="Bob", weekly_allowance=15.0)
    db_session.add_all([alice, bob])
    db_session.commit()

    # Create test chores
    chores = [
        Chore(name="Clean Room", description="Make bed and organize", points=5),
        Chore(name="Do Dishes", description="Load/unload dishwasher", points=3),
        Chore(name="Take Out Trash", description="Empty all trash bins", points=2)
    ]
    db_session.add_all(chores)
    db_session.commit()

    # Create some assignments
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    
    assignments = [
        ChoreAssignment(
            child_id=alice.id,
            chore_id=chores[0].id,
            week_start_date=week_start
        ),
        ChoreAssignment(
            child_id=bob.id,
            chore_id=chores[1].id,
            week_start_date=week_start
        )
    ]
    db_session.add_all(assignments)
    db_session.commit()

    return {
        "children": {"alice": alice, "bob": bob},
        "chores": chores,
        "assignments": assignments
    }