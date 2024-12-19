# app/tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import date, timedelta
from jose import jwt
from app.dependencies import create_access_token, get_password_hash

from app.database import Base, get_db
from app.main import app
from app.models.chores import Child, Chore, ChoreAssignment
from app.models.user import User

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

@pytest.fixture(scope="function")
def test_user(db_session):
    """Create a test user for authentication"""
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password=get_password_hash("testpassword"),
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def auth_headers(test_user):
    """Create authentication headers for test user"""
    access_token = create_access_token(data={"sub": test_user.username})
    return {"Authorization": f"Bearer {access_token}"}

@pytest.fixture
def authenticated_client(client, auth_headers):
    """Create a client with authentication headers"""
    client.headers.update(auth_headers)
    return client

@pytest.fixture
def sample_data(db_session, test_user):
    # Create test children
    alice = Child(name="Alice", weekly_allowance=10.0, user_id=test_user.id)
    bob = Child(name="Bob", weekly_allowance=15.0, user_id=test_user.id)
    db_session.add_all([alice, bob])
    db_session.commit()

    # Create test chores
    chores = [
        Chore(
            name="Clean Room",
            description="Make bed and organize",
            frequency_per_week=1,
            user_id=test_user.id
        ),
        Chore(
            name="Do Dishes",
            description="Load/unload dishwasher",
            frequency_per_week=7,
            user_id=test_user.id
        ),
        Chore(
            name="Take Out Trash",
            description="Empty all trash bins",
            frequency_per_week=2,
            user_id=test_user.id
        )
    ]
    db_session.add_all(chores)
    db_session.commit()

    # Create some assignments
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    
    assignments = []
    
    # Basic assignment for alice
    assignments.append(
        ChoreAssignment(
            child_id=alice.id,
            chore_id=chores[0].id,
            week_start=week_start,
            occurrence_number=1,
            user_id=test_user.id
        )
    )
    
    # Multiple assignments for Bob's dishes (frequency=7)
    for i in range(7):
        assignments.append(
            ChoreAssignment(
                child_id=bob.id,
                chore_id=chores[1].id,
                week_start=week_start,
                occurrence_number=i+1,
                user_id=test_user.id
            )
        )
    
    db_session.add_all(assignments)
    db_session.commit()

    return {
        "children": {"alice": alice, "bob": bob},
        "chores": chores,
        "assignments": assignments,
        "user": test_user
    }