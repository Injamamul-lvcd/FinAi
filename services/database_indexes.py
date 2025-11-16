"""
Database indexes initialization for MongoDB collections.

This module provides functions to create all required indexes for optimal
performance across all MongoDB collections used by the admin panel APIs.
"""

import logging
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import ConnectionFailure

logger = logging.getLogger(__name__)


def create_all_indexes(
    connection_string: str = "mongodb://localhost:27017/",
    database_name: str = "financial_chatbot"
) -> bool:
    """
    Create all required database indexes for optimal performance.
    
    This function creates indexes on:
    - users collection: username, email, is_admin, created_at, last_login
    - activity_logs collection: admin_id, timestamp, resource_type, resource_id
    - api_metrics collection: timestamp, endpoint
    - system_config collection: setting_name (unique)
    
    Args:
        connection_string: MongoDB connection string
        database_name: Name of the database
        
    Returns:
        bool: True if all indexes created successfully, False otherwise
    """
    try:
        # Connect to MongoDB
        client = MongoClient(connection_string, serverSelectionTimeoutMS=5000)
        client.admin.command('ping')
        logger.info(f"Connected to MongoDB at {connection_string}")
        
        db = client[database_name]
        
        # Create indexes for users collection
        success = create_users_indexes(db)
        if not success:
            logger.warning("Failed to create some users collection indexes")
        
        # Create indexes for activity_logs collection
        success = create_activity_logs_indexes(db)
        if not success:
            logger.warning("Failed to create some activity_logs collection indexes")
        
        # Create indexes for api_metrics collection
        success = create_api_metrics_indexes(db)
        if not success:
            logger.warning("Failed to create some api_metrics collection indexes")
        
        # Create indexes for system_config collection
        success = create_system_config_indexes(db)
        if not success:
            logger.warning("Failed to create some system_config collection indexes")
        
        client.close()
        logger.info("All database indexes created successfully")
        return True
        
    except ConnectionFailure as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        return False
    except Exception as e:
        logger.error(f"Error creating database indexes: {e}")
        return False


def create_users_indexes(db) -> bool:
    """
    Create indexes for the users collection.
    
    Indexes created:
    - username (unique)
    - email (unique)
    - is_admin
    - created_at
    - last_login
    - Compound index on (is_admin, last_login) for admin queries
    
    Args:
        db: MongoDB database instance
        
    Returns:
        bool: True if successful, False otherwise
    """
    users_collection = db['users']
    indexes_created = []
    
    # List of indexes to create
    indexes_to_create = [
        {
            "keys": [("username", ASCENDING)],
            "options": {"unique": True, "name": "username_1"},
            "description": "users.username"
        },
        {
            "keys": [("email", ASCENDING)],
            "options": {"unique": True, "name": "email_1"},
            "description": "users.email"
        },
        {
            "keys": [("is_admin", ASCENDING)],
            "options": {"name": "is_admin_idx"},
            "description": "users.is_admin"
        },
        {
            "keys": [("created_at", DESCENDING)],
            "options": {"name": "created_at_idx"},
            "description": "users.created_at"
        },
        {
            "keys": [("last_login", DESCENDING)],
            "options": {"name": "last_login_idx"},
            "description": "users.last_login"
        },
        {
            "keys": [("is_admin", ASCENDING), ("last_login", DESCENDING)],
            "options": {"name": "is_admin_last_login_idx"},
            "description": "users.(is_admin, last_login)"
        },
        {
            "keys": [("is_active", ASCENDING)],
            "options": {"name": "is_active_idx"},
            "description": "users.is_active"
        }
    ]
    
    # Create each index, skipping if it already exists
    for index_spec in indexes_to_create:
        try:
            users_collection.create_index(
                index_spec["keys"],
                **index_spec["options"]
            )
            logger.info(f"Created index on {index_spec['description']}")
            indexes_created.append(index_spec["description"])
        except Exception as e:
            # Index might already exist, which is fine
            if "already exists" in str(e).lower():
                logger.debug(f"Index on {index_spec['description']} already exists")
            else:
                logger.warning(f"Could not create index on {index_spec['description']}: {e}")
    
    logger.info(f"Users collection: {len(indexes_created)} indexes created/verified")
    return True


def create_activity_logs_indexes(db) -> bool:
    """
    Create indexes for the activity_logs collection.
    
    Indexes created:
    - admin_id
    - timestamp (descending)
    - resource_type
    - resource_id
    - action_type
    - Compound index on (admin_id, timestamp)
    - Compound index on (resource_type, resource_id, timestamp)
    
    Args:
        db: MongoDB database instance
        
    Returns:
        bool: True if successful, False otherwise
    """
    activity_logs_collection = db['activity_logs']
    indexes_created = []
    
    # List of indexes to create
    indexes_to_create = [
        {
            "keys": [("admin_id", ASCENDING)],
            "options": {"name": "admin_id_1"},
            "description": "activity_logs.admin_id"
        },
        {
            "keys": [("timestamp", DESCENDING)],
            "options": {"name": "timestamp_-1"},
            "description": "activity_logs.timestamp"
        },
        {
            "keys": [("resource_type", ASCENDING)],
            "options": {"name": "resource_type_1"},
            "description": "activity_logs.resource_type"
        },
        {
            "keys": [("resource_id", ASCENDING)],
            "options": {"name": "resource_id_1"},
            "description": "activity_logs.resource_id"
        },
        {
            "keys": [("action_type", ASCENDING)],
            "options": {"name": "action_type_1"},
            "description": "activity_logs.action_type"
        },
        {
            "keys": [("admin_id", ASCENDING), ("timestamp", DESCENDING)],
            "options": {"name": "admin_id_1_timestamp_-1"},
            "description": "activity_logs.(admin_id, timestamp)"
        },
        {
            "keys": [
                ("resource_type", ASCENDING),
                ("resource_id", ASCENDING),
                ("timestamp", DESCENDING)
            ],
            "options": {"name": "resource_type_1_resource_id_1_timestamp_-1"},
            "description": "activity_logs.(resource_type, resource_id, timestamp)"
        }
    ]
    
    # Create each index, skipping if it already exists
    for index_spec in indexes_to_create:
        try:
            activity_logs_collection.create_index(
                index_spec["keys"],
                **index_spec["options"]
            )
            logger.info(f"Created index on {index_spec['description']}")
            indexes_created.append(index_spec["description"])
        except Exception as e:
            # Index might already exist, which is fine
            if "already exists" in str(e).lower():
                logger.debug(f"Index on {index_spec['description']} already exists")
            else:
                logger.warning(f"Could not create index on {index_spec['description']}: {e}")
    
    logger.info(f"Activity logs collection: {len(indexes_created)} indexes created/verified")
    return True


def create_api_metrics_indexes(db) -> bool:
    """
    Create indexes for the api_metrics collection.
    
    Indexes created:
    - timestamp (descending)
    - endpoint
    - Compound index on (timestamp, endpoint)
    - status_code for error filtering
    
    Args:
        db: MongoDB database instance
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        api_metrics_collection = db['api_metrics']
        
        # Index on timestamp for time-based queries
        api_metrics_collection.create_index(
            [("timestamp", DESCENDING)],
            name="timestamp_idx"
        )
        logger.info("Created index on api_metrics.timestamp")
        
        # Index on endpoint for filtering by endpoint
        api_metrics_collection.create_index(
            [("endpoint", ASCENDING)],
            name="endpoint_idx"
        )
        logger.info("Created index on api_metrics.endpoint")
        
        # Compound index for efficient endpoint metrics queries
        api_metrics_collection.create_index(
            [("timestamp", DESCENDING), ("endpoint", ASCENDING)],
            name="timestamp_endpoint_idx"
        )
        logger.info("Created compound index on api_metrics.(timestamp, endpoint)")
        
        # Index on status_code for error filtering
        api_metrics_collection.create_index(
            [("status_code", ASCENDING)],
            name="status_code_idx"
        )
        logger.info("Created index on api_metrics.status_code")
        
        # Index on response_time_ms for performance analysis
        api_metrics_collection.create_index(
            [("response_time_ms", DESCENDING)],
            name="response_time_idx"
        )
        logger.info("Created index on api_metrics.response_time_ms")
        
        return True
        
    except Exception as e:
        logger.error(f"Error creating api_metrics collection indexes: {e}")
        return False


def create_system_config_indexes(db) -> bool:
    """
    Create indexes for the system_config collection.
    
    Indexes created:
    - setting_name (unique)
    - category for filtering by category
    
    Args:
        db: MongoDB database instance
        
    Returns:
        bool: True if successful, False otherwise
    """
    system_config_collection = db['system_config']
    indexes_created = []
    
    # List of indexes to create
    indexes_to_create = [
        {
            "keys": [("setting_name", ASCENDING)],
            "options": {"unique": True, "name": "setting_name_1"},
            "description": "system_config.setting_name"
        },
        {
            "keys": [("category", ASCENDING)],
            "options": {"name": "category_1"},
            "description": "system_config.category"
        }
    ]
    
    # Create each index, skipping if it already exists
    for index_spec in indexes_to_create:
        try:
            system_config_collection.create_index(
                index_spec["keys"],
                **index_spec["options"]
            )
            logger.info(f"Created index on {index_spec['description']}")
            indexes_created.append(index_spec["description"])
        except Exception as e:
            # Index might already exist, which is fine
            if "already exists" in str(e).lower():
                logger.debug(f"Index on {index_spec['description']} already exists")
            else:
                logger.warning(f"Could not create index on {index_spec['description']}: {e}")
    
    logger.info(f"System config collection: {len(indexes_created)} indexes created/verified")
    return True


def verify_indexes(
    connection_string: str = "mongodb://localhost:27017/",
    database_name: str = "financial_chatbot"
) -> dict:
    """
    Verify that all required indexes exist.
    
    Args:
        connection_string: MongoDB connection string
        database_name: Name of the database
        
    Returns:
        dict: Dictionary with collection names as keys and list of index names as values
    """
    try:
        client = MongoClient(connection_string, serverSelectionTimeoutMS=5000)
        client.admin.command('ping')
        
        db = client[database_name]
        
        indexes_info = {}
        
        # Get indexes for each collection
        collections = ['users', 'activity_logs', 'api_metrics', 'system_config']
        
        for collection_name in collections:
            collection = db[collection_name]
            indexes = collection.list_indexes()
            index_names = [idx['name'] for idx in indexes]
            indexes_info[collection_name] = index_names
            logger.info(f"{collection_name} indexes: {', '.join(index_names)}")
        
        client.close()
        return indexes_info
        
    except Exception as e:
        logger.error(f"Error verifying indexes: {e}")
        return {}


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create all indexes
    print("Creating database indexes...")
    success = create_all_indexes()
    
    if success:
        print("\nAll indexes created successfully!")
        
        # Verify indexes
        print("\nVerifying indexes...")
        indexes_info = verify_indexes()
        
        if indexes_info:
            print("\nIndex verification complete:")
            for collection, indexes in indexes_info.items():
                print(f"\n{collection}:")
                for idx in indexes:
                    print(f"  - {idx}")
        else:
            print("\nFailed to verify indexes")
    else:
        print("\nFailed to create some indexes. Check logs for details.")
