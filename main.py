# Importa a função que cria e configura o app Flask
from create_app import create_app

# Cria a instância da aplicação Flask
app = create_app()

# Variável exigida por servidores como o Gunicorn para reconhecer o app
application = app

# Executa o servidor local se o script for executado diretamente
if __name__ == "__main__":
    # Inicia o app Flask no endereço 0.0.0.0 (acessível na rede local), porta 5000, com modo debug ativado
    app.run(host="0.0.0.0", port=5000, debug=True)
