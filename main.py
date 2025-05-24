import os
from create_app import create_app

app = create_app()

if __name__ == "__main__":
    # pegar a porta da variável ou usar 5000
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
