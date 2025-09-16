#!/usr/bin/env python3
"""
SecurNote Admin Panel Server
Runs the administrative interface for PKI management.
"""
try:
    import uvicorn
    from securnote.web.admin import admin_app

    if __name__ == "__main__":
        print("🔧 Starting SecurNote Admin Panel...")
        print("📋 Admin Credentials:")
        print("   Username: admin")
        print("   Password: securnote_admin_2024")
        print("🌐 Admin Panel: http://localhost:8001")
        print("=" * 50)

        uvicorn.run(
            admin_app,
            host="0.0.0.0",
            port=8001,
            log_level="info"
        )

except ImportError:
    print("⚠️ uvicorn not installed. Install with: pip install uvicorn")
    print("📝 For testing admin panel functionality:")
    print("   1. Install uvicorn: pip install uvicorn")
    print("   2. Run: python3 run_admin.py")
    print("   3. Access: http://localhost:8001")
    print("   4. Credentials: admin / securnote_admin_2024")