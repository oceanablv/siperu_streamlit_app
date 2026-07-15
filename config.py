from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
ASSETS_DIR = BASE_DIR / "assets"
PDFS_DIR = ASSETS_DIR / "pdfs"

USERS_FILE = DATA_DIR / "users.json"
BOOKS_FILE = DATA_DIR / "books.json"
CATEGORIES_FILE = DATA_DIR / "categories.json"
ROOMS_FILE = DATA_DIR / "rooms.json"
LOANS_FILE = DATA_DIR / "loans.json"
QUEUES_FILE = DATA_DIR / "queues.json"
RESERVATIONS_FILE = DATA_DIR / "reservations.json"

def ensure_data_dir() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    PDFS_DIR.mkdir(parents=True, exist_ok=True)
