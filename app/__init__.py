"""
CineBook Application Factory
Initializes the Flask application, session secret, and route blueprints.
"""

import os
from flask import Flask
from dotenv import load_dotenv

load_dotenv()


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "cinebook_dev_secret_key_12345")
    
    # Custom Jinja filters
    @app.template_filter("format_currency")
    def format_currency(value):
        try:
            return f"₹{float(value):.2f}"
        except (ValueError, TypeError):
            return f"₹{value}"

    @app.template_filter("format_time")
    def format_time(value):
        if not value:
            return ""
        # If timedelta or string
        s = str(value)
        parts = s.split(":")
        if len(parts) >= 2:
            hour = int(parts[0])
            minute = parts[1]
            period = "AM" if hour < 12 else "PM"
            display_hour = hour if hour <= 12 else hour - 12
            if display_hour == 0:
                display_hour = 12
            return f"{display_hour}:{minute} {period}"
        return s

    from app.routes import main_bp
    app.register_blueprint(main_bp)

    return app
