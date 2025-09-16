#!/usr/bin/env python3
"""
SecurNote Admin Panel Server
Runs the administrative interface for PKI management.
"""
import sys

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

except ImportError as e:
    print(f"⚠️ Missing dependencies: {e}")
    print("📝 Admin panel requires FastAPI and uvicorn")
    print("💡 Alternative: Use Docker container which has all dependencies")
    print("   docker run -p 8001:8001 securnote python3 run_admin.py")
    print()
    print("📋 Admin Panel Implementation Ready:")
    print("   - File: securnote/web/admin.py")
    print("   - Authentication: admin / securnote_admin_2024")
    print("   - Endpoints: Certificate management, revocation, cleanup")
    sys.exit(1)