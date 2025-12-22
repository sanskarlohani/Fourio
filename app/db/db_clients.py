from typing import Tuple, Optional
from app.models.model import DBClient
from app.utils.utils import GetEnv
from .mongo_client import NewMongoClient
from .sqlite_client import NewSQLiteClient


# DBtype = GetEnv("DB_TYPE", "sqlite")

def NewDBClient() -> Tuple[Optional[DBClient], Optional[Exception]]:
    DBtype = GetEnv("DB_TYPE", "sqlite")  # evaluate dynamically each call
    print("DB_TYPE =", DBtype)

    if DBtype == "mongo":
        dbUsername = GetEnv("DB_USER")
        dbPassword = GetEnv("DB_PASS")
        dbName     = GetEnv("DB_NAME")
        dbHost     = GetEnv("DB_HOST")
        dbPort     = GetEnv("DB_PORT")

        if dbUsername and dbPassword:
            dbUri = f"mongodb://{dbUsername}:{dbPassword}@{dbHost}:{dbPort}/{dbName}?authSource=admin"
        else:
            dbUri = "mongodb://localhost:27017" # default 

        return NewMongoClient(dbUri)
            
    elif DBtype == "sqlite":
        return NewSQLiteClient("db/db.sqlite3")

    else:
        return None, Exception(f"unsupported database type: {DBtype}")