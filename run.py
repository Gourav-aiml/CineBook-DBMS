"""
CineBook Entrypoint
Starts the local development server for the CineBook Movie Ticket Booking System.
"""

from app import create_app

app = create_app()

if __name__ == "__main__":
    print("=======================================================")
    print("  CineBook - Movie Ticket Booking System (DBMS Project)")
    print("  Running on: http://127.0.0.1:5000")
    print("=======================================================")
    app.run(host="127.0.0.1", port=5000, debug=True)
