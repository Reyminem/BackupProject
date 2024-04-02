from cryptography.fernet import Fernet

# Função para gerar a chave
def generate_key():
    key = Fernet.generate_key()
    return key

# Função para salvar a chave no arquivo
def save_key_to_file(key, filename):
    with open(filename, "wb") as file:
        file.write(key)

# Gera a chave
fernet_key = generate_key()

# Salva a chave em um arquivo
filename = "fernet.key"
save_key_to_file(fernet_key, filename)
print(f"Chave Fernet gerada e salva em '{filename}'.")
