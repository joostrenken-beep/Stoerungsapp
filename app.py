"""Startpunkt der Kanalbetriebsdatenbank.

Entwicklung:  flask --app app run --debug
Produktion:   waitress-serve --port 8000 app:app   (oder gunicorn "app:create_app()")
"""
from kanaldb import create_app

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
