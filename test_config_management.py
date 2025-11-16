"""
Test script for configuration management endpoints.

This script tests the ConfigManager service and configuration API endpoints.
"""

import logging
from services.config_manager import ConfigManager
from services.activity_logger import ActivityLogger
from config.settings import get_settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_config_manager():
    """Test ConfigManager service functionality."""
    try:
        settings = get_settings()
        
        # Initialize activity logger
        activity_logger = ActivityLogger(
            connection_string=settings.mongodb_connection_string,
            database_name=settings.mongodb_database_name
        )
        
        # Initialize config manager
        config_manager = ConfigManager(
            connection_string=settings.mongodb_connection_string,
            database_name=settings.mongodb_database_name,
            activity_logger=activity_logger
        )
        
        logger.info("✓ ConfigManager initialized successfully")
        
        # Test 1: Get all settings
        logger.info("\n--- Test 1: Get all settings ---")
        all_settings = config_manager.get_all_settings()
        logger.info(f"Retrieved {all_settings['total']} settings")
        assert all_settings['total'] > 0, "Should have settings"
        logger.info("✓ Get all settings works")
        
        # Test 2: Get specific setting
        logger.info("\n--- Test 2: Get specific setting ---")
        chunk_size_setting = config_manager.get_setting("chunk_size")
        assert chunk_size_setting is not None, "chunk_size setting should exist"
        logger.info(f"chunk_size: {chunk_size_setting['value']}")
        logger.info("✓ Get specific setting works")
        
        # Test 3: Validate setting value (valid)
        logger.info("\n--- Test 3: Validate setting value (valid) ---")
        is_valid, error = config_manager.validate_setting_value("chunk_size", 1000)
        assert is_valid, f"1000 should be valid for chunk_size: {error}"
        logger.info("✓ Valid value validation works")
        
        # Test 4: Validate setting value (invalid - too small)
        logger.info("\n--- Test 4: Validate setting value (invalid - too small) ---")
        is_valid, error = config_manager.validate_setting_value("chunk_size", 50)
        assert not is_valid, "50 should be invalid for chunk_size (min 100)"
        logger.info(f"Validation error (expected): {error}")
        logger.info("✓ Invalid value validation works")
        
        # Test 5: Validate setting value (invalid - too large)
        logger.info("\n--- Test 5: Validate setting value (invalid - too large) ---")
        is_valid, error = config_manager.validate_setting_value("chunk_size", 3000)
        assert not is_valid, "3000 should be invalid for chunk_size (max 2000)"
        logger.info(f"Validation error (expected): {error}")
        logger.info("✓ Invalid value validation works")
        
        # Test 6: Update setting
        logger.info("\n--- Test 6: Update setting ---")
        original_value = chunk_size_setting['value']
        new_value = 1200
        success = config_manager.update_setting(
            setting_name="chunk_size",
            value=new_value,
            admin_id="test_admin",
            admin_username="test_admin_user"
        )
        assert success, "Update should succeed"
        
        # Verify update
        updated_setting = config_manager.get_setting("chunk_size")
        assert updated_setting['value'] == new_value, f"Value should be {new_value}"
        logger.info(f"Updated chunk_size from {original_value} to {new_value}")
        logger.info("✓ Update setting works")
        
        # Test 7: Get settings by category
        logger.info("\n--- Test 7: Get settings by category ---")
        rag_settings = config_manager.get_settings_by_category("rag")
        assert len(rag_settings) > 0, "Should have RAG settings"
        logger.info(f"Found {len(rag_settings)} RAG settings")
        logger.info("✓ Get settings by category works")
        
        # Test 8: Reset setting to default
        logger.info("\n--- Test 8: Reset setting to default ---")
        success = config_manager.reset_setting_to_default(
            setting_name="chunk_size",
            admin_id="test_admin",
            admin_username="test_admin_user"
        )
        assert success, "Reset should succeed"
        
        # Verify reset
        reset_setting = config_manager.get_setting("chunk_size")
        assert reset_setting['value'] == reset_setting['default_value'], "Value should be default"
        logger.info(f"Reset chunk_size to default: {reset_setting['value']}")
        logger.info("✓ Reset setting to default works")
        
        # Test 9: Verify activity logging
        logger.info("\n--- Test 9: Verify activity logging ---")
        logs = activity_logger.get_activity_logs(
            user_id="test_admin",
            action_type="config_updated"
        )
        assert logs['total'] > 0, "Should have activity logs"
        logger.info(f"Found {logs['total']} activity log entries")
        logger.info("✓ Activity logging works")
        
        # Cleanup
        config_manager.close()
        activity_logger.close()
        
        logger.info("\n" + "="*50)
        logger.info("✓ All tests passed successfully!")
        logger.info("="*50)
        
        return True
        
    except AssertionError as e:
        logger.error(f"✗ Test failed: {e}")
        return False
    except Exception as e:
        logger.error(f"✗ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    logger.info("Starting configuration management tests...\n")
    success = test_config_manager()
    
    if success:
        logger.info("\n✓ Configuration management implementation verified!")
    else:
        logger.error("\n✗ Configuration management tests failed")
        exit(1)
