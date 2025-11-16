"""
Seed script for initial configuration settings.

This script populates the system_config MongoDB collection with all current
environment variable settings including RAG configuration, document processing,
and LLM settings.
"""

import logging
from pymongo import MongoClient
from config.settings import get_settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def seed_configuration_settings():
    """
    Seed initial configuration settings to MongoDB.
    
    Adds all current environment variable settings to system_config collection.
    """
    try:
        # Get current settings
        settings = get_settings()
        
        # Connect to MongoDB
        client = MongoClient(
            settings.mongodb_connection_string,
            serverSelectionTimeoutMS=5000
        )
        
        # Test connection
        client.admin.command('ping')
        logger.info(f"Connected to MongoDB at {settings.mongodb_connection_string}")
        
        # Get database and collection
        db = client[settings.mongodb_database_name]
        system_config_collection = db['system_config']
        
        # Define configuration settings
        config_settings = [
            # RAG Configuration
            {
                "setting_name": "chunk_size",
                "value": settings.chunk_size,
                "default_value": 800,
                "data_type": "int",
                "min_value": 100,
                "max_value": 2000,
                "description": "Size of text chunks in characters for document processing",
                "category": "rag"
            },
            {
                "setting_name": "chunk_overlap",
                "value": settings.chunk_overlap,
                "default_value": 100,
                "data_type": "int",
                "min_value": 0,
                "max_value": 500,
                "description": "Overlap between chunks in characters to maintain context",
                "category": "rag"
            },
            {
                "setting_name": "top_k_chunks",
                "value": settings.top_k_chunks,
                "default_value": 5,
                "data_type": "int",
                "min_value": 1,
                "max_value": 20,
                "description": "Number of most relevant chunks to retrieve for context",
                "category": "rag"
            },
            {
                "setting_name": "max_conversation_turns",
                "value": settings.max_conversation_turns,
                "default_value": 20,
                "data_type": "int",
                "min_value": 1,
                "max_value": 100,
                "description": "Maximum conversation turns to keep in history",
                "category": "rag"
            },
            
            # Document Processing Configuration
            {
                "setting_name": "max_file_size_mb",
                "value": settings.max_file_size_mb,
                "default_value": 10,
                "data_type": "int",
                "min_value": 1,
                "max_value": 100,
                "description": "Maximum file size for document uploads in megabytes",
                "category": "document"
            },
            
            # LLM Configuration
            {
                "setting_name": "gemini_temperature",
                "value": settings.gemini_temperature,
                "default_value": 0.7,
                "data_type": "float",
                "min_value": 0.0,
                "max_value": 2.0,
                "description": "Temperature for LLM generation (0.0-2.0). Higher values make output more random",
                "category": "llm"
            },
            {
                "setting_name": "gemini_max_tokens",
                "value": settings.gemini_max_tokens,
                "default_value": 500,
                "data_type": "int",
                "min_value": 1,
                "max_value": 8192,
                "description": "Maximum tokens for LLM response generation",
                "category": "llm"
            },
            {
                "setting_name": "gemini_chat_model",
                "value": settings.gemini_chat_model,
                "default_value": "models/gemini-2.5-flash",
                "data_type": "str",
                "min_value": 1,
                "max_value": 100,
                "description": "Gemini chat model name to use for response generation",
                "category": "llm"
            },
            {
                "setting_name": "gemini_embedding_model",
                "value": settings.gemini_embedding_model,
                "default_value": "models/text-embedding-004",
                "data_type": "str",
                "min_value": 1,
                "max_value": 100,
                "description": "Gemini embedding model name for document vectorization",
                "category": "llm"
            },
            
            # API Configuration
            {
                "setting_name": "jwt_access_token_expire_minutes",
                "value": settings.jwt_access_token_expire_minutes,
                "default_value": 30,
                "data_type": "int",
                "min_value": 1,
                "max_value": 1440,
                "description": "JWT access token expiration time in minutes",
                "category": "api"
            },
            {
                "setting_name": "api_port",
                "value": settings.api_port,
                "default_value": 8000,
                "data_type": "int",
                "min_value": 1,
                "max_value": 65535,
                "description": "API server port number",
                "category": "api"
            },
            {
                "setting_name": "log_level",
                "value": settings.log_level,
                "default_value": "INFO",
                "data_type": "str",
                "min_value": 3,
                "max_value": 10,
                "description": "Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
                "category": "api"
            },
            
            # Vector Database Configuration
            {
                "setting_name": "chroma_collection_name",
                "value": settings.chroma_collection_name,
                "default_value": "financial_docs",
                "data_type": "str",
                "min_value": 1,
                "max_value": 100,
                "description": "ChromaDB collection name for document storage",
                "category": "vector_db"
            }
        ]
        
        # Insert or update settings
        inserted_count = 0
        updated_count = 0
        
        for setting in config_settings:
            # Check if setting already exists
            existing = system_config_collection.find_one(
                {"setting_name": setting["setting_name"]}
            )
            
            if existing:
                # Update only if value changed
                if existing.get("value") != setting["value"]:
                    system_config_collection.update_one(
                        {"setting_name": setting["setting_name"]},
                        {"$set": setting}
                    )
                    updated_count += 1
                    logger.info(f"Updated setting: {setting['setting_name']}")
                else:
                    logger.info(f"Setting unchanged: {setting['setting_name']}")
            else:
                # Insert new setting
                system_config_collection.insert_one(setting)
                inserted_count += 1
                logger.info(f"Inserted setting: {setting['setting_name']}")
        
        logger.info(
            f"Configuration seeding complete. "
            f"Inserted: {inserted_count}, Updated: {updated_count}"
        )
        
        # Close connection
        client.close()
        
        return True
        
    except Exception as e:
        logger.error(f"Error seeding configuration settings: {e}")
        return False


if __name__ == "__main__":
    logger.info("Starting configuration settings seed...")
    success = seed_configuration_settings()
    
    if success:
        logger.info("Configuration settings seeded successfully!")
    else:
        logger.error("Failed to seed configuration settings")
        exit(1)
