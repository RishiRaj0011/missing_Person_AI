#!/usr/bin/env python3
"""
Manual file cleanup script
Run this to immediately clean up orphaned files and enforce storage limits
"""

from app import create_app
from app.file_manager import cleanup_orphaned_files, enforce_storage_limits, get_upload_directory_size

def main():
    """Run file cleanup operations"""
    app = create_app()
    
    with app.app_context():
        print("🔄 Starting file cleanup...")
        
        # Show current storage usage
        current_size = get_upload_directory_size()
        print(f"📊 Current storage usage: {current_size / (1024*1024):.2f} MB")
        
        # Clean up orphaned files
        print("🧹 Cleaning up orphaned files...")
        orphaned_count = cleanup_orphaned_files()
        print(f"✅ Removed {orphaned_count} orphaned files")
        
        # Enforce storage limits
        print("📦 Enforcing storage limits...")
        removed_count = enforce_storage_limits()
        if removed_count > 0:
            print(f"✅ Removed {removed_count} old files to enforce storage limits")
        else:
            print("✅ Storage within limits, no files removed")
        
        # Show final storage usage
        final_size = get_upload_directory_size()
        print(f"📊 Final storage usage: {final_size / (1024*1024):.2f} MB")
        print(f"💾 Space freed: {(current_size - final_size) / (1024*1024):.2f} MB")
        
        print("🎉 File cleanup completed!")

if __name__ == "__main__":
    main()