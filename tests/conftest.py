import os

import pytest
from sqlmodel import SQLModel

from core.db import get_engine

# Provide default test-friendly configuration values.
os.environ.setdefault('POSTGRES_URL', 'sqlite:///:memory:')
os.environ.setdefault('REDIS_URL', 'redis://localhost:6379/0')
os.environ.setdefault('OPENAI_API_KEY', 'test-key')
os.environ.setdefault('TAVILY_API_KEY', 'test-key')
os.environ.setdefault('INTERNAL_AUTH_TOKEN', 'test-token')


@pytest.fixture(scope='session')
def anyio_backend():
    return 'asyncio'


@pytest.fixture(scope='session', autouse=True)
def create_database():
    engine = get_engine()
    SQLModel.metadata.create_all(engine)
    yield
    SQLModel.metadata.drop_all(engine)
