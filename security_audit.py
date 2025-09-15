#!/usr/bin/env python3
"""
Security Audit Script for Missing Person Finder
Verifies that all Phase 1 security measures are properly implemented
"""

import os
import re
from pathlib import Path

def check_configuration_security():
    """Check if configuration is properly secured"""
    print("🔍 Checking Configuration Security...")
    
    # Check .env file
    env_path = Path(".env")
    if env_path.exists():
        with open(env_path, 'r') as f:
            env_content = f.read()
            
        if "FLASK_DEBUG=False" in env_content:
            print("✅ Debug mode disabled in .env")
        else:
            print("❌ Debug mode not properly disabled")
            
        if "SECRET_KEY=" in env_content and len(env_content.split("SECRET_KEY=")[1].split('\n')[0]) > 20:
            print("✅ Secret key configured")
        else:
            print("❌ Secret key not properly configured")
    else:
        print("❌ .env file not found")
    
    # Check config.py
    config_path = Path("config.py")
    if config_path.exists():
        with open(config_path, 'r') as f:
            config_content = f.read()
            
        if "os.environ.get(\"SECRET_KEY\")" in config_content:
            print("✅ Config uses environment variables")
        else:
            print("❌ Config not using environment variables")
            
        if "WTF_CSRF_ENABLED = True" in config_content:
            print("✅ CSRF protection enabled")
        else:
            print("❌ CSRF protection not enabled")
    else:
        print("❌ config.py not found")

def check_csrf_protection():
    """Check if CSRF protection is implemented on all forms"""
    print("\n🔍 Checking CSRF Protection...")
    
    template_dir = Path("app/templates")
    if not template_dir.exists():
        print("❌ Templates directory not found")
        return
    
    form_files = []
    for template_file in template_dir.rglob("*.html"):
        with open(template_file, 'r', encoding='utf-8') as f:
            content = f.read()
            if '<form' in content and 'method="POST"' in content:
                form_files.append(template_file)
    
    csrf_protected = 0
    for form_file in form_files:
        with open(form_file, 'r', encoding='utf-8') as f:
            content = f.read()
            if '{{ form.hidden_tag() }}' in content or 'csrf_token' in content:
                csrf_protected += 1
                print(f"✅ CSRF protected: {form_file.name}")
            else:
                print(f"❌ Missing CSRF protection: {form_file.name}")
    
    print(f"📊 CSRF Protection: {csrf_protected}/{len(form_files)} forms protected")

def check_authorization():
    """Check if authorization decorators are properly implemented"""
    print("\n🔍 Checking Authorization...")
    
    routes_file = Path("app/routes.py")
    admin_file = Path("app/admin.py")
    
    if routes_file.exists():
        with open(routes_file, 'r') as f:
            routes_content = f.read()
            
        if "@case_owner_required" in routes_content:
            print("✅ Case owner authorization implemented")
        else:
            print("❌ Case owner authorization missing")
            
        if "abort(403)" in routes_content:
            print("✅ Proper authorization error handling")
        else:
            print("❌ Authorization error handling missing")
    
    if admin_file.exists():
        with open(admin_file, 'r') as f:
            admin_content = f.read()
            
        admin_routes = admin_content.count("@admin_required")
        if admin_routes > 10:
            print(f"✅ Admin authorization: {admin_routes} routes protected")
        else:
            print(f"❌ Insufficient admin authorization: {admin_routes} routes")

def check_file_upload_security():
    """Check if file upload security is properly implemented"""
    print("\n🔍 Checking File Upload Security...")
    
    routes_file = Path("app/routes.py")
    utils_file = Path("app/utils.py")
    
    if routes_file.exists():
        with open(routes_file, 'r') as f:
            routes_content = f.read()
            
        if "secure_filename" in routes_content:
            print("✅ secure_filename usage found")
        else:
            print("❌ secure_filename not used")
            
        if "_is_allowed_image_file" in routes_content:
            print("✅ File type validation implemented")
        else:
            print("❌ File type validation missing")
            
        if "validate_file_content" in routes_content:
            print("✅ File content validation implemented")
        else:
            print("❌ File content validation missing")
    
    if utils_file.exists():
        with open(utils_file, 'r') as f:
            utils_content = f.read()
            
        if "sanitize_filename" in utils_content:
            print("✅ Filename sanitization utilities found")
        else:
            print("❌ Filename sanitization utilities missing")

def check_input_sanitization():
    """Check if input sanitization is implemented"""
    print("\n🔍 Checking Input Sanitization...")
    
    utils_file = Path("app/utils.py")
    models_file = Path("app/models.py")
    
    if utils_file.exists():
        with open(utils_file, 'r') as f:
            utils_content = f.read()
            
        if "sanitize_input" in utils_content:
            print("✅ Input sanitization functions found")
        else:
            print("❌ Input sanitization functions missing")
            
        if "sanitize_log_input" in utils_content:
            print("✅ Log injection prevention implemented")
        else:
            print("❌ Log injection prevention missing")
    
    if models_file.exists():
        with open(models_file, 'r') as f:
            models_content = f.read()
            
        if "sanitize_input" in models_content:
            print("✅ Model sanitization implemented")
        else:
            print("❌ Model sanitization missing")

def main():
    """Run complete security audit"""
    print("🛡️  MISSING PERSON FINDER - SECURITY AUDIT")
    print("=" * 50)
    
    check_configuration_security()
    check_csrf_protection()
    check_authorization()
    check_file_upload_security()
    check_input_sanitization()
    
    print("\n" + "=" * 50)
    print("🎯 AUDIT COMPLETE")
    print("📋 Review any ❌ items above and fix before deployment")

if __name__ == "__main__":
    main()