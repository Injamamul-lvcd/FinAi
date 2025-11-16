#!/usr/bin/env python3
"""
Database Indexes Initialization Script

This script creates all required MongoDB indexes for the Financial Chatbot
RAG System admin panel APIs. Run this script after setting up MongoDB to
ensure optimal query performance.

Usage:
    python init_database_indexes.py
"""

import sys
import logging
from config.settings import get_settings
from services.database_indexes import create_all_indexes, verify_indexes


def main():
    """Main function to initialize database indexes."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger = logging.getLogger(__name__)
    
    try:
        # Load settings
        logger.info("Loading application settings...")
        settings = get_settings()
        
        # Create all indexes
        logger.info("Creating database indexes...")
        logger.info(f"MongoDB connection: {settings.mongodb_connection_string}")
        logger.info(f"Database name: {settings.mongodb_database_name}")
        
        success = create_all_indexes(
            connection_string=settings.mongodb_connection_string,
            database_name=settings.mongodb_database_name
        )
        
        if success:
            print("\n" + "="*60)
            print("✓ All indexes created successfully!")
            print("="*60)
            
            # Verify indexes
            logger.info("\nVerifying indexes...")
            indexes_info = verify_indexes(
                connection_string=settings.mongodb_connection_string,
                database_name=settings.mongodb_database_name
            )
            
            if indexes_info:
                print("\nIndex verification complete:")
                print("-"*60)
                
                for collection, indexes in indexes_info.items():
                    print(f"\n{collection} collection:")
                    for idx in indexes:
                        print(f"  ✓ {idx}")
                
                print("\n" + "="*60)
                print("Database indexes are ready for use!")
                print("="*60)
                
                return 0
            else:
                print("\n✗ Failed to verify indexes")
                return 1
        else:
            print("\n✗ Failed to create some indexes. Check logs for details.")
            return 1
            
    except Exception as e:
        logger.error(f"Error initializing database indexes: {e}")
        print(f"\n✗ Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
