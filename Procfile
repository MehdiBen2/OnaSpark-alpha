web: gunicorn --workers 4 --threads 2 --bind 0.0.0.0:$PORT app:create_app()
worker: python worker.py
release: flask db upgrade
