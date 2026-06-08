web: gunicorn run:app --workers 4 --bind 0.0.0.0:$PORT --log-file -
release: flask db upgrade
