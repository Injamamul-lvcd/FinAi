#!/usr/bin/env python3
"""
Database Migration Script for Admin Panel APIs

This script migrates existing data to support the new admin panel features:
1. Adds is_admin field to all existing users (default False)
2. Designates the first admin user (interactive prompt)
3. Backfills user_id and username in ChromaDB document metadata
4. Adds file_size_bytes to existing document metadata

Usage:
    python migrate_admin_panel_data.py
    
    Optional flags:
    --skip-admin-creation: Skip the admin user creation step
    --admin-username <username>: Specify admin username (non-interactive)
"""

import sys
import os
import logging
import argparse
from datetime import datetime
from typing import Optional, Dict, Any
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.settings import get_settings
from services.vector_store import VectorStoreManager


def setup_logging():
    """Configure logging for the migration script."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)


def connect_mongodb(connection_string: str, database_name: str):
    """
    Connect to MongoDB and return client and database.
    
    Args:
        connection_string: MongoDB connection string
        database_name: Database name
        
    Returns:
        Tuple of (client, database)
        
    Raises:
        ConnectionFailure: If connection fails
    """
    try:
        client = MongoClient(connection_string, serverSelectionTimeoutMS=5000)
        client.admin.command('ping')
        db = client[database_name]
        return client, db
    except ConnectionFailure as e:
        raise ConnectionFailure(f"Failed to connect to MongoDB: {e}")


def migrate_user_admin_field(db, logger):
    """
    Add is_admin and password_reset_required fields to all existing users.
    
    Args:
        db: MongoDB database instance
        logger: Logger instance
        
    Returns:
        Number of users updated
    """
    logger.info("Step 1: Adding is_admin and password_reset_required fields to users...")
    
    users_collection = db['users']
    
    # Update all users that don't have is_admin field
    result = users_collection.update_many(
        {"is_admin": {"$exists": False}},
        {
            "$set": {
                "is_admin": False,
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    logger.info(f"  ✓ Added is_admin field to {result.modified_count} users")
    
    # Update all users that don't have password_reset_required field
    result2 = users_collection.update_many(
        {"password_reset_required": {"$exists": False}},
        {
            "$set": {
                "password_reset_required": False,
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    logger.info(f"  ✓ Added password_reset_required field to {result2.modified_count} users")
    
    return result.modified_count + result2.modified_count


def create_admin_user(db, logger, admin_username: Optional[str] = None):
    """
    Designate a user as admin or create a new admin user.
    
    Args:
        db: MongoDB database instance
        logger: Logger instance
        admin_username: Optional username to make admin (non-interactive)
        
    Returns:
        True if admin created/designated successfully
    """
    logger.info("Step 2: Designating admin user...")
    
    users_collection = db['users']
    
    # Check if an admin already exists
    existing_admin = users_collection.find_one({"is_admin": True})
    if existing_admin:
        logger.info(f"  ℹ Admin user already exists: {existing_admin['username']}")
        return True
    
    # Get all users
    all_users = list(users_collection.find({}, {"username": 1, "email": 1, "created_at": 1}))
    
    if not all_users:
        logger.warning("  ⚠ No users found in database. Skipping admin creation.")
        logger.warning("  ⚠ You can create an admin user later by registering a user and manually setting is_admin=True")
        return False
    
    # If admin_username provided, use it
    if admin_username:
        user = users_collection.find_one({"username": admin_username})
        if not user:
            logger.error(f"  ✗ User '{admin_username}' not found")
            return False
        
        # Make this user an admin
        users_collection.update_one(
            {"_id": user["_id"]},
            {
                "$set": {
                    "is_admin": True,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        logger.info(f"  ✓ User '{admin_username}' designated as admin")
        return True
    
    # Interactive mode
    print("\n" + "="*60)
    print("ADMIN USER DESIGNATION")
    print("="*60)
    print("\nExisting users:")
    print("-"*60)
    
    for i, user in enumerate(all_users, 1):
        created_at = user.get('created_at', 'Unknown')
        if isinstance(created_at, datetime):
            created_at = created_at.strftime('%Y-%m-%d %H:%M:%S')
        print(f"{i}. {user['username']} ({user['email']}) - Created: {created_at}")
    
    print("-"*60)
    print("\nSelect a user to designate as admin:")
    print("Enter the number (1-{}) or username, or 'skip' to skip this step".format(len(all_users)))
    
    while True:
        choice = input("\nYour choice: ").strip()
        
        if choice.lower() == 'skip':
            logger.info("  ℹ Skipping admin user designation")
            return False
        
        # Try as number
        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(all_users):
                selected_user = all_users[idx]
                break
        
        # Try as username
        selected_user = users_collection.find_one({"username": choice})
        if selected_user:
            break
        
        print("  ✗ Invalid choice. Please try again.")
    
    # Make selected user an admin
    users_collection.update_one(
        {"_id": selected_user["_id"]},
        {
            "$set": {
                "is_admin": True,
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    logger.info(f"  ✓ User '{selected_user['username']}' designated as admin")
    print(f"\n✓ User '{selected_user['username']}' is now an admin!")
    
    return True


def backfill_document_metadata(vector_store: VectorStoreManager, db, logger):
    """
    Backfill user_id, username, and file_size_bytes in ChromaDB document metadata.
    
    Args:
        vector_store: VectorStoreManager instance
        db: MongoDB database instance
        logger: Logger instance
        
    Returns:
        Number of documents updated
    """
    logger.info("Step 3: Backfilling document metadata in ChromaDB...")
    
    try:
        # Get all items from ChromaDB
        all_items = vector_store.collection.get()
        
        if not all_items['ids']:
            logger.info("  ℹ No documents found in ChromaDB")
            return 0
        
        # Group by document_id
        documents_map = {}
        for i, metadata in enumerate(all_items['metadatas']):
            doc_id = metadata.get('document_id')
            if doc_id and doc_id not in documents_map:
                documents_map[doc_id] = {
                    'metadata': metadata,
                    'chunk_ids': []
                }
            if doc_id:
                documents_map[doc_id]['chunk_ids'].append(all_items['ids'][i])
        
        logger.info(f"  Found {len(documents_map)} unique documents")
        
        updated_count = 0
        skipped_count = 0
        
        for doc_id, doc_info in documents_map.items():
            metadata = doc_info['metadata']
            chunk_ids = doc_info['chunk_ids']
            
            # Check if already has required fields
            has_user_id = 'user_id' in metadata
            has_username = 'username' in metadata
            has_file_size = 'file_size_bytes' in metadata
            
            if has_user_id and has_username and has_file_size:
                skipped_count += 1
                continue
            
            # Prepare updates
            updates = {}
            
            # Try to infer user_id and username (not possible without additional data)
            # For now, set to unknown if not present
            if not has_user_id:
                updates['user_id'] = 'unknown'
            if not has_username:
                updates['username'] = 'unknown'
            
            # Estimate file_size_bytes if not present
            # We can't get the original file size, so we'll estimate from chunk count
            # Average chunk is ~800 characters, ~1 byte per character
            if not has_file_size:
                estimated_size = len(chunk_ids) * 800  # Rough estimate
                updates['file_size_bytes'] = estimated_size
            
            # Update all chunks for this document
            if updates:
                for chunk_id in chunk_ids:
                    # Get current metadata
                    chunk_data = vector_store.collection.get(ids=[chunk_id])
                    if chunk_data['metadatas']:
                        current_metadata = chunk_data['metadatas'][0]
                        # Merge updates
                        updated_metadata = {**current_metadata, **updates}
                        
                        # Update the chunk
                        vector_store.collection.update(
                            ids=[chunk_id],
                            metadatas=[updated_metadata]
                        )
                
                updated_count += 1
                logger.info(f"  ✓ Updated document {doc_id} ({len(chunk_ids)} chunks)")
        
        logger.info(f"  ✓ Updated {updated_count} documents, skipped {skipped_count} (already complete)")
        logger.info(f"  ℹ Note: user_id and username set to 'unknown' for existing documents")
        logger.info(f"  ℹ Note: file_size_bytes estimated from chunk count")
        
        return updated_count
        
    except Exception as e:
        logger.error(f"  ✗ Failed to backfill document metadata: {e}")
        raise


def verify_migration(db, vector_store: VectorStoreManager, logger):
    """
    Verify that migration completed successfully.
    
    Args:
        db: MongoDB database instance
        vector_store: VectorStoreManager instance
        logger: Logger instance
    """
    logger.info("\nVerifying migration...")
    
    users_collection = db['users']
    
    # Check users
    total_users = users_collection.count_documents({})
    users_with_admin_field = users_collection.count_documents({"is_admin": {"$exists": True}})
    users_with_reset_field = users_collection.count_documents({"password_reset_required": {"$exists": True}})
    admin_users = users_collection.count_documents({"is_admin": True})
    
    print("\n" + "="*60)
    print("MIGRATION VERIFICATION")
    print("="*60)
    print(f"\nUsers:")
    print(f"  Total users: {total_users}")
    print(f"  Users with is_admin field: {users_with_admin_field}")
    print(f"  Users with password_reset_required field: {users_with_reset_field}")
    print(f"  Admin users: {admin_users}")
    
    # Check documents
    try:
        all_items = vector_store.collection.get()
        total_chunks = len(all_items['ids'])
        
        chunks_with_user_id = sum(1 for m in all_items['metadatas'] if 'user_id' in m)
        chunks_with_username = sum(1 for m in all_items['metadatas'] if 'username' in m)
        chunks_with_file_size = sum(1 for m in all_items['metadatas'] if 'file_size_bytes' in m)
        
        # Count unique documents
        unique_docs = len(set(m.get('document_id') for m in all_items['metadatas'] if m.get('document_id')))
        
        print(f"\nDocuments:")
        print(f"  Total chunks: {total_chunks}")
        print(f"  Unique documents: {unique_docs}")
        print(f"  Chunks with user_id: {chunks_with_user_id}")
        print(f"  Chunks with username: {chunks_with_username}")
        print(f"  Chunks with file_size_bytes: {chunks_with_file_size}")
        
    except Exception as e:
        logger.warning(f"  ⚠ Could not verify document metadata: {e}")
    
    print("="*60)
    
    # Check if migration is complete
    if users_with_admin_field == total_users and users_with_reset_field == total_users:
        print("\n✓ Migration completed successfully!")
        return True
    else:
        print("\n⚠ Migration may be incomplete. Please review the results above.")
        return False


def main():
    """Main migration function."""
    parser = argparse.ArgumentParser(description='Migrate database for admin panel features')
    parser.add_argument('--skip-admin-creation', action='store_true',
                       help='Skip the admin user creation step')
    parser.add_argument('--admin-username', type=str,
                       help='Specify admin username (non-interactive)')
    
    args = parser.parse_args()
    
    logger = setup_logging()
    
    print("\n" + "="*60)
    print("ADMIN PANEL DATA MIGRATION")
    print("="*60)
    print("\nThis script will:")
    print("1. Add is_admin field to all existing users")
    print("2. Designate an admin user (interactive)")
    print("3. Backfill document metadata in ChromaDB")
    print("="*60)
    
    try:
        # Load settings
        logger.info("\nLoading application settings...")
        settings = get_settings()
        
        # Connect to MongoDB
        logger.info("Connecting to MongoDB...")
        client, db = connect_mongodb(
            settings.mongodb_connection_string,
            settings.mongodb_database_name
        )
        logger.info("  ✓ Connected to MongoDB")
        
        # Initialize vector store
        logger.info("Connecting to ChromaDB...")
        vector_store = VectorStoreManager(
            persist_directory=settings.chroma_persist_dir,
            collection_name=settings.chroma_collection_name
        )
        logger.info("  ✓ Connected to ChromaDB")
        
        print("\n" + "-"*60)
        print("Starting migration...")
        print("-"*60 + "\n")
        
        # Step 1: Migrate user admin field
        migrate_user_admin_field(db, logger)
        
        # Step 2: Create admin user
        if not args.skip_admin_creation:
            create_admin_user(db, logger, args.admin_username)
        else:
            logger.info("Step 2: Skipping admin user creation (--skip-admin-creation flag)")
        
        # Step 3: Backfill document metadata
        backfill_document_metadata(vector_store, db, logger)
        
        # Verify migration
        success = verify_migration(db, vector_store, logger)
        
        # Close connections
        client.close()
        logger.info("\nMongoDB connection closed")
        
        if success:
            print("\n" + "="*60)
            print("✓ Migration completed successfully!")
            print("="*60)
            return 0
        else:
            return 1
        
    except Exception as e:
        logger.error(f"\n✗ Migration failed: {e}")
        print(f"\n✗ Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
