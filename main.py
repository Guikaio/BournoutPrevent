from create_app import create_app

# Criar a instância da aplicação
app = create_app()

# Necessário para o Gunicorn
application = app

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
