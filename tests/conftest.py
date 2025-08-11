# tests/conftest.py
import socket
import subprocess
import time
import logging
from typing import Generator, Dict, List
from contextlib import contextmanager

import pytest
import requests
from faker import Faker
from sqlalchemy import text
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from playwright.sync_api import sync_playwright, Browser, Page

from app.database import Base, get_engine, get_sessionmaker
from app.core.config import settings

# Import all model modules so Base.metadata is fully populated
from app.models.user import User
from app.models.calculation import Calculation
# If you have more models, import them here

# ======================================================================================
# Logging
# ======================================================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# ======================================================================================
# Database setup
# ======================================================================================
fake = Faker()
Faker.seed(12345)

test_engine = get_engine(database_url=settings.DATABASE_URL)
TestingSessionLocal = get_sessionmaker(engine=test_engine)

# ======================================================================================
# Helpers
# ======================================================================================
def create_fake_user() -> Dict[str, str]:
    return {
        "first_name": fake.first_name(),
        "last_name": fake.last_name(),
        "email": fake.unique.email(),
        "username": fake.unique.user_name(),
        "password": fake.password(length=12),
    }

@contextmanager
def managed_db_session():
    session = TestingSessionLocal()
    try:
        yield session
    except SQLAlchemyError as e:
        logger.error(f"Database error: {str(e)}")
        session.rollback()
        raise
    finally:
        session.close()

def wait_for_server(url: str, timeout: int = 30) -> bool:
    start_time = time.time()
    while (time.time() - start_time) < timeout:
        try:
            r = requests.get(url)
            if r.status_code == 200:
                return True
        except requests.exceptions.ConnectionError:
            time.sleep(1)
    return False

class ServerStartupError(Exception):
    pass

# ======================================================================================
# Schema lifecycle
# ======================================================================================
@pytest.fixture(scope="session", autouse=True)
def setup_test_database(request):
    """
    Hard reset the Postgres schema at session start and end.
    This avoids FK drop ordering issues.
    """
    logger.info("Resetting test schema at session start...")
    with test_engine.begin() as conn:
        conn.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
        conn.execute(text("CREATE SCHEMA public"))

    # Create tables from SQLAlchemy metadata
    Base.metadata.create_all(bind=test_engine)
    logger.info("Tables created.")

    # If you have a data seeding function that does not run DDL, you can call it here.
    # from app.database_init import init_db  # noqa
    # init_db()

    yield

    if not request.config.getoption("--preserve-db"):
        logger.info("Resetting test schema at session end...")
        with test_engine.begin() as conn:
            conn.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
            conn.execute(text("CREATE SCHEMA public"))
        logger.info("Schema reset complete.")

# Truncate data before each test
@pytest.fixture(autouse=True)
def clean_db():
    """
    Truncate all tables and reset sequences before each test.
    Requires all models to be imported so Base.metadata is complete.
    """
    table_names = [t.name for t in Base.metadata.sorted_tables]
    if table_names:
        sql = "TRUNCATE TABLE " + ", ".join(table_names) + " RESTART IDENTITY CASCADE"
        with test_engine.begin() as conn:
            conn.execute(text(sql))
    yield

# ======================================================================================
# DB session fixtures
# ======================================================================================
@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    session = TestingSessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

@pytest.fixture
def fake_user_data() -> Dict[str, str]:
    return create_fake_user()

@pytest.fixture
def test_user(db_session: Session) -> User:
    user_data = create_fake_user()
    user = User(**user_data)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    logger.info(f"Created test user ID: {user.id}")
    return user

@pytest.fixture
def seed_users(db_session: Session, request) -> List[User]:
    num_users = getattr(request, "param", 5)
    users = [User(**create_fake_user()) for _ in range(num_users)]
    db_session.add_all(users)
    db_session.commit()
    logger.info(f"Seeded {len(users)} users.")
    return users

# ======================================================================================
# FastAPI server
# ======================================================================================
def find_available_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]

@pytest.fixture(scope="session")
def fastapi_server():
    base_port = 8000
    server_url = f"http://127.0.0.1:{base_port}/"
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        if s.connect_ex(("127.0.0.1", base_port)) == 0:
            base_port = find_available_port()
            server_url = f"http://127.0.0.1:{base_port}/"

    logger.info(f"Starting FastAPI server on port {base_port}...")
    process = subprocess.Popen(
        ["uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", str(base_port)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd=".",
    )

    health_url = f"{server_url}health"
    if not wait_for_server(health_url, timeout=30):
        stderr = process.stderr.read() if process.stderr is not None else ""
        logger.error(f"Server failed to start. Uvicorn error: {stderr}")
        process.terminate()
        raise ServerStartupError(f"Failed to start test server on {health_url}")

    logger.info(f"Test server running on {server_url}.")
    yield server_url

    logger.info("Stopping test server...")
    process.terminate()
    try:
        process.wait(timeout=5)
        logger.info("Test server stopped.")
    except subprocess.TimeoutExpired:
        process.kill()
        logger.warning("Test server forcefully stopped.")

# ======================================================================================
# Playwright
# ======================================================================================
@pytest.fixture(scope="session")
def browser_context():
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"],
        )
        logger.info("Playwright browser launched.")
        try:
            yield browser
        finally:
            logger.info("Closing Playwright browser.")
            browser.close()

@pytest.fixture
def page(browser_context: Browser):
    context = browser_context.new_context(
        viewport={"width": 1920, "height": 1080},
        ignore_https_errors=True,
    )
    page = context.new_page()
    logger.info("New browser page created.")
    try:
        yield page
    finally:
        logger.info("Closing browser page and context.")
        page.close()
        context.close()

# ======================================================================================
# Pytest CLI
# ======================================================================================
def pytest_addoption(parser):
    parser.addoption("--preserve-db", action="store_true", help="Keep test database after tests")
    parser.addoption("--run-slow", action="store_true", help="Run tests marked as slow")

def pytest_collection_modifyitems(config, items):
    if not config.getoption("--run-slow"):
        skip_slow = pytest.mark.skip(reason="use --run-slow to run")
        for item in items:
            if "slow" in item.keywords:
                item.add_marker(skip_slow)
