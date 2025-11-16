"""
Configuration Manager service for dynamic system configuration.

This module provides the ConfigManager class for managing system configuration
settings with validation, type checking, and activity logging.
"""

import logging
from datetime import datetime
from typing import Optional, Dict, Any, Tuple, List
from pymongo import MongoClient, ASCENDING
from pymongo.errors import ConnectionFailure

logger = logging.getLogger(__name__)


class ConfigManager:
    """
    Manages dynamic system configuration settings.
    
    Provides methods to retrieve, update, and validate configuration settings
    stored in MongoDB with activity logging for all changes.
    """
    
    def __init__(
        self,
        connection_string: str = "mongodb://localhost:27017/",
        database_name: str = "financial_chatbot",
        activity_logger: Optional[Any] = None
    ):
        """
        Initialize the ConfigManager.
        
        Args:
            connection_string: MongoDB connection string
            database_name: Name of the database to use
            activity_logger: Optional ActivityLogger instance for logging changes
        """
        self.connection_string = connection_string
        self.database_name = database_name
        self.activity_logger = activity_logger
        
        try:
            # Initialize MongoDB client
            self.client = MongoClient(connection_string, serverSelectionTimeoutMS=5000)
            
            # Test connection
            self.client.admin.command('ping')
            logger.info(f"ConfigManager connected to MongoDB at {connection_string}")
            
            # Get database and collection
            self.db = self.client[database_name]
            self.system_config_collection = self.db['system_config']
            
            # Create indexes for better performance
            self._create_indexes()
            
        except ConnectionFailure as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
        except Exception as e:
            logger.error(f"Error initializing ConfigManager: {e}")
            raise
    
    def _create_indexes(self):
        """Create database indexes for better query performance."""
        try:
            # Unique index on setting_name
            self.system_config_collection.create_index(
                [("setting_name", ASCENDING)],
                unique=True
            )
            
            # Index on category for filtering
            self.system_config_collection.create_index([("category", ASCENDING)])
            
            logger.info("ConfigManager indexes created successfully")
            
        except Exception as e:
            logger.warning(f"Error creating ConfigManager indexes: {e}")
    
    def get_all_settings(self) -> Dict:
        """
        Retrieve all configuration settings.
        
        Returns:
            Dict: Dictionary containing all settings with their current and default values
        """
        try:
            settings_cursor = self.system_config_collection.find()
            
            settings = []
            for setting in settings_cursor:
                setting_data = {
                    "setting_name": setting["setting_name"],
                    "value": setting["value"],
                    "default_value": setting["default_value"],
                    "data_type": setting["data_type"],
                    "description": setting["description"],
                    "category": setting["category"],
                    "min_value": setting.get("min_value"),
                    "max_value": setting.get("max_value"),
                    "updated_at": setting.get("updated_at").isoformat() if setting.get("updated_at") else None,
                    "updated_by": setting.get("updated_by")
                }
                settings.append(setting_data)
            
            logger.info(f"Retrieved {len(settings)} configuration settings")
            
            return {
                "settings": settings,
                "total": len(settings)
            }
            
        except Exception as e:
            logger.error(f"Error retrieving all settings: {e}")
            return {
                "settings": [],
                "total": 0
            }
    
    def get_setting(self, setting_name: str) -> Optional[Dict]:
        """
        Retrieve a specific configuration setting.
        
        Args:
            setting_name: Name of the setting to retrieve
            
        Returns:
            Optional[Dict]: Setting data or None if not found
        """
        try:
            setting = self.system_config_collection.find_one(
                {"setting_name": setting_name}
            )
            
            if setting is None:
                logger.warning(f"Setting not found: {setting_name}")
                return None
            
            setting_data = {
                "setting_name": setting["setting_name"],
                "value": setting["value"],
                "default_value": setting["default_value"],
                "data_type": setting["data_type"],
                "description": setting["description"],
                "category": setting["category"],
                "min_value": setting.get("min_value"),
                "max_value": setting.get("max_value"),
                "updated_at": setting.get("updated_at").isoformat() if setting.get("updated_at") else None,
                "updated_by": setting.get("updated_by")
            }
            
            logger.info(f"Retrieved setting: {setting_name}")
            
            return setting_data
            
        except Exception as e:
            logger.error(f"Error retrieving setting {setting_name}: {e}")
            return None
    
    def update_setting(
        self,
        setting_name: str,
        value: Any,
        admin_id: str,
        admin_username: Optional[str] = None
    ) -> bool:
        """
        Update a configuration setting with validation.
        
        Args:
            setting_name: Name of the setting to update
            value: New value for the setting
            admin_id: User ID of the admin making the change
            admin_username: Optional username of the admin
            
        Returns:
            bool: True if update successful, False otherwise
        """
        try:
            # Get current setting
            current_setting = self.system_config_collection.find_one(
                {"setting_name": setting_name}
            )
            
            if current_setting is None:
                logger.warning(f"Cannot update non-existent setting: {setting_name}")
                return False
            
            # Validate the new value
            is_valid, error_message = self.validate_setting_value(setting_name, value)
            
            if not is_valid:
                logger.warning(
                    f"Invalid value for setting {setting_name}: {error_message}"
                )
                return False
            
            # Store old value for logging
            old_value = current_setting["value"]
            
            # Update the setting
            result = self.system_config_collection.update_one(
                {"setting_name": setting_name},
                {
                    "$set": {
                        "value": value,
                        "updated_at": datetime.utcnow(),
                        "updated_by": admin_username or admin_id
                    }
                }
            )
            
            if result.modified_count > 0:
                logger.info(
                    f"Setting {setting_name} updated from {old_value} to {value} "
                    f"by admin {admin_id}"
                )
                
                # Log the activity
                if self.activity_logger:
                    self.activity_logger.log_action(
                        admin_id=admin_id,
                        action_type="config_updated",
                        resource_type="config",
                        resource_id=setting_name,
                        details={
                            "setting_name": setting_name,
                            "old_value": old_value,
                            "new_value": value
                        },
                        admin_username=admin_username,
                        result="success"
                    )
                
                return True
            else:
                logger.warning(f"No changes made to setting {setting_name}")
                return False
            
        except Exception as e:
            logger.error(f"Error updating setting {setting_name}: {e}")
            
            # Log failed attempt
            if self.activity_logger:
                self.activity_logger.log_action(
                    admin_id=admin_id,
                    action_type="config_updated",
                    resource_type="config",
                    resource_id=setting_name,
                    details={
                        "setting_name": setting_name,
                        "attempted_value": value,
                        "error": str(e)
                    },
                    admin_username=admin_username,
                    result="failure"
                )
            
            return False
    
    def validate_setting_value(
        self,
        setting_name: str,
        value: Any
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate a setting value against its constraints.
        
        Args:
            setting_name: Name of the setting
            value: Value to validate
            
        Returns:
            Tuple[bool, Optional[str]]: (is_valid, error_message)
        """
        try:
            # Get setting definition
            setting = self.system_config_collection.find_one(
                {"setting_name": setting_name}
            )
            
            if setting is None:
                return False, f"Setting '{setting_name}' not found"
            
            data_type = setting["data_type"]
            min_value = setting.get("min_value")
            max_value = setting.get("max_value")
            
            # Type validation
            if data_type == "int":
                if not isinstance(value, int):
                    try:
                        value = int(value)
                    except (ValueError, TypeError):
                        return False, f"Value must be an integer"
                
                # Range validation for integers
                if min_value is not None and value < min_value:
                    return False, f"Value must be at least {min_value}"
                if max_value is not None and value > max_value:
                    return False, f"Value must be at most {max_value}"
            
            elif data_type == "float":
                if not isinstance(value, (int, float)):
                    try:
                        value = float(value)
                    except (ValueError, TypeError):
                        return False, f"Value must be a number"
                
                # Range validation for floats
                if min_value is not None and value < min_value:
                    return False, f"Value must be at least {min_value}"
                if max_value is not None and value > max_value:
                    return False, f"Value must be at most {max_value}"
            
            elif data_type == "str":
                if not isinstance(value, str):
                    return False, f"Value must be a string"
                
                # Length validation for strings (using min/max as length constraints)
                if min_value is not None and len(value) < min_value:
                    return False, f"String length must be at least {min_value}"
                if max_value is not None and len(value) > max_value:
                    return False, f"String length must be at most {max_value}"
            
            elif data_type == "bool":
                if not isinstance(value, bool):
                    # Try to convert string to bool
                    if isinstance(value, str):
                        if value.lower() in ["true", "1", "yes"]:
                            value = True
                        elif value.lower() in ["false", "0", "no"]:
                            value = False
                        else:
                            return False, f"Value must be a boolean (true/false)"
                    else:
                        return False, f"Value must be a boolean"
            
            else:
                return False, f"Unknown data type: {data_type}"
            
            return True, None
            
        except Exception as e:
            logger.error(f"Error validating setting value: {e}")
            return False, f"Validation error: {str(e)}"
    
    def get_settings_by_category(self, category: str) -> List[Dict]:
        """
        Retrieve all settings in a specific category.
        
        Args:
            category: Category name (e.g., "rag", "document", "api")
            
        Returns:
            List[Dict]: List of settings in the category
        """
        try:
            settings_cursor = self.system_config_collection.find(
                {"category": category}
            )
            
            settings = []
            for setting in settings_cursor:
                setting_data = {
                    "setting_name": setting["setting_name"],
                    "value": setting["value"],
                    "default_value": setting["default_value"],
                    "data_type": setting["data_type"],
                    "description": setting["description"],
                    "category": setting["category"],
                    "min_value": setting.get("min_value"),
                    "max_value": setting.get("max_value"),
                    "updated_at": setting.get("updated_at").isoformat() if setting.get("updated_at") else None,
                    "updated_by": setting.get("updated_by")
                }
                settings.append(setting_data)
            
            logger.info(f"Retrieved {len(settings)} settings in category '{category}'")
            
            return settings
            
        except Exception as e:
            logger.error(f"Error retrieving settings by category: {e}")
            return []
    
    def reset_setting_to_default(
        self,
        setting_name: str,
        admin_id: str,
        admin_username: Optional[str] = None
    ) -> bool:
        """
        Reset a setting to its default value.
        
        Args:
            setting_name: Name of the setting to reset
            admin_id: User ID of the admin making the change
            admin_username: Optional username of the admin
            
        Returns:
            bool: True if reset successful, False otherwise
        """
        try:
            # Get current setting
            setting = self.system_config_collection.find_one(
                {"setting_name": setting_name}
            )
            
            if setting is None:
                logger.warning(f"Cannot reset non-existent setting: {setting_name}")
                return False
            
            default_value = setting["default_value"]
            old_value = setting["value"]
            
            # Update to default value
            result = self.system_config_collection.update_one(
                {"setting_name": setting_name},
                {
                    "$set": {
                        "value": default_value,
                        "updated_at": datetime.utcnow(),
                        "updated_by": admin_username or admin_id
                    }
                }
            )
            
            if result.modified_count > 0:
                logger.info(
                    f"Setting {setting_name} reset to default value {default_value} "
                    f"by admin {admin_id}"
                )
                
                # Log the activity
                if self.activity_logger:
                    self.activity_logger.log_action(
                        admin_id=admin_id,
                        action_type="config_reset",
                        resource_type="config",
                        resource_id=setting_name,
                        details={
                            "setting_name": setting_name,
                            "old_value": old_value,
                            "default_value": default_value
                        },
                        admin_username=admin_username,
                        result="success"
                    )
                
                return True
            else:
                return False
            
        except Exception as e:
            logger.error(f"Error resetting setting {setting_name}: {e}")
            return False
    
    def close(self):
        """Close the MongoDB connection."""
        try:
            self.client.close()
            logger.info("ConfigManager MongoDB connection closed")
        except Exception as e:
            logger.error(f"Error closing MongoDB connection: {e}")
