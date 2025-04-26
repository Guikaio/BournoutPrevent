from create_app import create_app

# Create the application instance
app = create_app()

# Required for Gunicorn
application = app

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)