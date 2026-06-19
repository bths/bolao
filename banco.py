from upstash_redis import Redis

UPSTASH_URL = "https://patient-weevil-151275.upstash.io"
UPSTASH_TOKEN = "gQAAAAAAAk7rAAIgcDE4MWU3NDVhY2FiZGQ0YmE3OWFlNTMwNGE2ZDdiMWNmOQ"

# A instância do banco é criada aqui e exportada
db = Redis(url=UPSTASH_URL, token=UPSTASH_TOKEN)

def salvar_no_banco(chave, dados):
    """
    Recebe o nome da chave e os dados (lista ou dicionário)
    e salva no Upstash Redis.
    """
    try:
        db.set(chave, dados)
        return True
    except Exception as e:
        print(f"Erro ao salvar no banco: {e}")
        return False

def ler_do_banco(chave):
    """
    Busca a chave no Upstash e retorna os dados prontos.
    Retorna None se a chave não existir.
    """
    try:
        return db.get(chave)
    except Exception as e:
        print(f"Erro ao ler do banco: {e}")
        return None