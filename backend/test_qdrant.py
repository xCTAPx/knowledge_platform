
from qdrant_client import QdrantClient, models

client = QdrantClient(url="http://localhost:6333")

collection = "rag_demo"

if client.collection_exists(collection):
    client.delete_collection(collection)

client.create_collection(
    collection_name=collection,
    vectors_config=models.VectorParams(
        size=3,
        distance=models.Distance.COSINE,
    ),
)

client.upsert(
    collection_name=collection,
    points=[
        models.PointStruct(
            id=1,
            vector=[0.9, 0.1, 0.0],
            payload={"text": "Как восстановить пароль?"},
        ),
        models.PointStruct(
            id=2,
            vector=[0.8, 0.2, 0.0],
            payload={"text": "Как изменить пароль пользователя?"},
        ),
        models.PointStruct(
            id=3,
            vector=[0.0, 0.1, 0.9],
            payload={"text": "Как настроить подключение к БД?"},
        ),
    ],
)

results = client.query_points(
    collection_name=collection,
    query=[0.85, 0.15, 0.0],
    limit=2,
    with_payload=True,
).points

for point in results:
    print(point.score, point.payload["text"])
