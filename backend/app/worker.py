import logging
import threading

from redis import Redis
from rq import Queue, SimpleWorker

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.embeddings import load_embedder
from app.core.indexing import QUEUE, relay, resume


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    load_embedder()
    db = SessionLocal()
    try:
        resume(db)
    finally:
        db.close()
    threading.Thread(target=relay, daemon=True).start()
    connection = Redis.from_url(settings.redis_url)
    # SimpleWorker keeps the loaded CUDA model in this process. The default RQ worker forks.
    SimpleWorker([Queue(QUEUE, connection=connection)], connection=connection).work()


if __name__ == "__main__":
    main()
