from typing import Tuple, Optional
from app.models.model import DBClient
from app.utils.utils import GetEnv
from .mongo_client import NewMongoClient
from .sqlite_client import NewSQLiteClient
from .hybrid_client import NewHybridClient


def NewDBClient() -> Tuple[Optional[DBClient], Optional[Exception]]:
    DBtype = GetEnv("DB_TYPE", "sqlite")
    print("DB_TYPE =", DBtype)

    if DBtype == "mongo" or DBtype == "hybrid":
        dbUsername = GetEnv("DB_USER")
        dbPassword = GetEnv("DB_PASS")
        dbName     = GetEnv("DB_NAME")
        dbHost     = GetEnv("DB_HOST")
        dbPort     = GetEnv("DB_PORT")
        mongoUri   = GetEnv("MONGO_URL")
        redisUri   = GetEnv("REDIS_URL")
        
        if mongoUri:
            dbUri = mongoUri
        elif dbUsername and dbPassword:
            dbUri = f"mongodb://{dbUsername}:{dbPassword}@{dbHost}:{dbPort}/{dbName}?authSource=admin"
        else:
            dbUri = "mongodb://localhost:27017"

        if DBtype == "mongo":
            return NewMongoClient(dbUri)

        if DBtype == "hybrid":
            return NewHybridClient(dbUri, redisUri)  

    elif DBtype == "sqlite":
        return NewSQLiteClient("db/db.sqlite3")

    return None, Exception(f"unsupported database type: {DBtype}")