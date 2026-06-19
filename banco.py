from upstash_redis import Redis

UPSTASH_URL = "https://patient-weevil-151275.upstash.io"
UPSTASH_TOKEN = "gQAAAAAAAk7rAAIgcDE4MWU3NDVhY2FiZGQ0YmE3OWFlNTMwNGE2ZDdiMWNmOQ"

# A instância do banco é criada aqui e exportada
db = Redis(url=UPSTASH_URL, token=UPSTASH_TOKEN)