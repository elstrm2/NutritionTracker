cd "$(dirname "$0")/."
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
python3 -m create_db
