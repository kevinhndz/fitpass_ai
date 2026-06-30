from werkzeug.security import generate_password_hash

password_secreta = "mi_clave_secreta_123"


hash_seguro = generate_password_hash(password_secreta)

print(hash_seguro)