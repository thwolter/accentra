import os

import pytest

# Provide default test-friendly configuration values.
os.environ.setdefault('POSTGRES_URL', 'sqlite:///:memory:')
os.environ.setdefault('REDIS_URL', 'redis://localhost:6379/0')
os.environ.setdefault('OPENAI_API_KEY', 'test-key')
os.environ.setdefault('TAVILY_API_KEY', 'test-key')
os.environ.setdefault('INTERNAL_AUTH_TOKEN', 'test-token')


@pytest.fixture(scope='session')
def anyio_backend():
    return 'asyncio'

