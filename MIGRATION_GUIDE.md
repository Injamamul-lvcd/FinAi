# Admin Panel Data Migration Guide

This guide explains how to migrate your existing Financial Chatbot RAG System database to support the new admin panel features.

## Overview

The migration script (`migrate_admin_panel_data.py`) performs the following operations:

1. **User Schema Updates**: Adds `is_admin` and `password_reset_required` fields to all existing users
2. **Admin User Designation**: Allows you to designate an existing user as an administrator
3. **Document Metadata Backfill**: Updates ChromaDB document metadata with `user_id`, `username`, and `file_size_bytes` fields

## Prerequisites

- Python 3.8 or higher
- MongoDB running and accessible
- ChromaDB data directory accessible
- All required Python packages installed (`pip install -r requirements.txt`)
- `.env` file configured with database connection strings

## Usage

### Interactive Mode (Recommended)

Run the migration script in interactive mode to select an admin user from a list:

```bash
python migrate_admin_panel_data.py
```

The script will:
1. Display all existing users
2. Prompt you to select a user to designate as admin
3. Complete the migration

### Non-Interactive Mode

If you know which user should be the admin, you can specify it directly:

```bash
python migrate_admin_panel_data.py --admin-username <username>
```

Example:
```bash
python migrate_admin_panel_data.py --admin-username john_doe
```

### Skip Admin Creation

If you want to skip the admin user creation step (e.g., you'll create an admin later):

```bash
python migrate_admin_panel_data.py --skip-admin-creation
```

## What the Migration Does

### 1. User Schema Updates

**Before:**
```json
{
  "_id": "507f1f77bcf86cd799439011",
  "username": "john_doe",
  "email": "john@example.com",
  "hashed_password": "...",
  "is_active": true,
  "created_at": "2024-11-09T10:30:00"
}
```

**After:**
```json
{
  "_id": "507f1f77bcf86cd799439011",
  "username": "john_doe",
  "email": "john@example.com",
  "hashed_password": "...",
  "is_active": true,
  "is_admin": false,
  "password_reset_required": false,
  "created_at": "2024-11-09T10:30:00",
  "updated_at": "2024-11-16T15:30:00"
}
```

### 2. Admin User Designation

The selected user will have `is_admin` set to `true`:

```json
{
  "is_admin": true,
  ...
}
```

### 3. Document Metadata Backfill

**Before:**
```json
{
  "document_id": "doc_123",
  "filename": "report.pdf",
  "chunk_index": 0,
  "upload_date": "2024-11-14T10:30:00",
  "file_type": "pdf"
}
```

**After:**
```json
{
  "document_id": "doc_123",
  "filename": "report.pdf",
  "chunk_index": 0,
  "upload_date": "2024-11-14T10:30:00",
  "file_type": "pdf",
  "user_id": "unknown",
  "username": "unknown",
  "file_size_bytes": 33600
}
```

**Note:** For existing documents, `user_id` and `username` are set to "unknown" because this information wasn't tracked before. The `file_size_bytes` is estimated based on the number of chunks (chunks × 800 bytes).

## Verification

After the migration completes, the script will display a verification summary:

```
MIGRATION VERIFICATION
============================================================

Users:
  Total users: 10
  Users with is_admin field: 10
  Users with password_reset_required field: 10
  Admin users: 1

Documents:
  Total chunks: 523
  Unique documents: 15
  Chunks with user_id: 523
  Chunks with username: 523
  Chunks with file_size_bytes: 523
============================================================

✓ Migration completed successfully!
```

## Troubleshooting

### MongoDB Connection Failed

**Error:** `Failed to connect to MongoDB`

**Solution:** 
- Verify MongoDB is running
- Check your `.env` file has the correct `MONGODB_CONNECTION_STRING`
- Ensure MongoDB is accessible from your machine

### ChromaDB Not Found

**Error:** `Could not verify document metadata`

**Solution:**
- Verify the `CHROMA_PERSIST_DIR` in your `.env` file points to the correct directory
- Ensure ChromaDB data exists in that directory

### No Users Found

**Warning:** `No users found in database. Skipping admin creation.`

**Solution:**
- This is normal if you haven't registered any users yet
- You can create an admin user later by:
  1. Registering a user through the API
  2. Manually setting `is_admin: true` in MongoDB
  3. Or running the migration script again

### Admin Already Exists

**Info:** `Admin user already exists: <username>`

**Solution:**
- This is normal if you've already run the migration
- The script will skip admin creation
- No action needed

## Post-Migration Steps

After successful migration:

1. **Verify Admin Access**: Test logging in with the admin user credentials
2. **Test Admin Endpoints**: Verify admin API endpoints are accessible
3. **Review Logs**: Check application logs for any issues
4. **Backup Database**: Create a backup of your MongoDB database

## Rolling Back

If you need to roll back the migration:

### Remove Admin Fields from Users

```javascript
// In MongoDB shell or Compass
db.users.updateMany(
  {},
  {
    $unset: {
      is_admin: "",
      password_reset_required: ""
    }
  }
)
```

### Remove Document Metadata Fields

Unfortunately, ChromaDB doesn't support bulk metadata updates easily. You would need to:
1. Export your documents
2. Delete the ChromaDB collection
3. Re-import documents with original metadata

**Recommendation:** Create a backup before running the migration.

## Creating Additional Admin Users

After migration, you can create additional admin users by:

### Option 1: Using MongoDB

```javascript
// In MongoDB shell or Compass
db.users.updateOne(
  { username: "new_admin_username" },
  {
    $set: {
      is_admin: true,
      updated_at: new Date()
    }
  }
)
```

### Option 2: Using the Admin API (Future)

Once the admin panel is fully implemented, you'll be able to promote users to admin through the admin API.

## Support

If you encounter issues during migration:

1. Check the logs for detailed error messages
2. Verify all prerequisites are met
3. Ensure database connections are working
4. Review the troubleshooting section above

For additional help, refer to the main project documentation or contact the development team.
