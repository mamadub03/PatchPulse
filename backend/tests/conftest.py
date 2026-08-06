import os

os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+psycopg://patchpulse:patchpulse@localhost:5432/patchpulse_test",
)
