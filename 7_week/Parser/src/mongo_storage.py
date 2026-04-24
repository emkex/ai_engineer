from config import logger
from Interfaces import DatabaseStorage
from motor.motor_asyncio import AsyncIOMotorClient


class MongoStorage(DatabaseStorage):
    def __init__(self, mongo_uri, db_name, collection_name):
        self.mongo_uri = mongo_uri
        self.db_name = db_name
        self.collection_name = collection_name
        self._client = None  # создаётся при первом обращении

    async def connect(self):
        if self._client is None:
            self._client = AsyncIOMotorClient(self.mongo_uri)
        return self._client.get_database(self.db_name)

    async def save(self, news_entry):
        try:
            db = await self.connect()
            await db.get_collection(self.collection_name).insert_one(news_entry)
            logger.info("News saved")
        except Exception as error:
            logger.error(f"Can't save news to mongo: {error}")

    async def find_news(self, reference):
        try:
            db = await self.connect()
            return await db.get_collection(self.collection_name).count_documents({"reference": reference}) > 0
        except Exception as error:
            logger.error(f"Can't check mongo for existing news: {error}")
            return False
