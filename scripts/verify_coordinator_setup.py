#!/usr/bin/env python3
"""
Verify Network Coordinator Setup
This script checks if all required dependencies and files are present
"""

import sys
import os
import importlib

def check_import(module_name, description=""):
    """Check if a module can be imported"""
    try:
        importlib.import_module(module_name)
        print(f"✅ {module_name} - {description}")
        return True
    except ImportError as e:
        print(f"❌ {module_name} - {description} - ERROR: {e}")
        return False

def check_file(file_path, description=""):
    """Check if a file exists"""
    if os.path.exists(file_path):
        print(f"✅ {file_path} - {description}")
        return True
    else:
        print(f"❌ {file_path} - {description} - FILE NOT FOUND")
        return False

def main():
    print("🔍 PlayerGold Network Coordinator - Setup Verification")
    print("=" * 60)
    
    # Check Python version
    python_version = sys.version_info
    print(f"🐍 Python version: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 7):
        print("❌ Python 3.7+ required")
        return False
    else:
        print("✅ Python version OK")
    
    print("\n📦 Checking Python dependencies...")
    
    # Core dependencies
    deps_ok = True
    deps_ok &= check_import("fastapi", "FastAPI web framework")
    deps_ok &= check_import("uvicorn", "ASGI server")
    deps_ok &= check_import("pydantic", "Data validation")
    deps_ok &= check_import("cryptography", "Cryptographic functions")
    deps_ok &= check_import("aiohttp", "Async HTTP client")
    deps_ok &= check_import("aiofiles", "Async file operations")
    
    # Standard library modules
    deps_ok &= check_import("asyncio", "Async programming")
    deps_ok &= check_import("sqlite3", "SQLite database")
    deps_ok &= check_import("json", "JSON handling")
    deps_ok &= check_import("datetime", "Date/time handling")
    deps_ok &= check_import("logging", "Logging")
    
    print(f"\n📁 Checking coordinator source files...")
    
    # Check source files
    files_ok = True
    base_path = "/opt/playergold" if os.path.exists("/opt/playergold") else "."
    
    coordinator_files = [
        f"{base_path}/src/network_coordinator/server.py",
        f"{base_path}/src/network_coordinator/models.py", 
        f"{base_path}/src/network_coordinator/registry.py",
        f"{base_path}/src/network_coordinator/encryption.py",
        f"{base_path}/src/network_coordinator/backup_manager.py",
        f"{base_path}/src/network_coordinator/fork_detector.py"
    ]
    
    for file_path in coordinator_files:
        files_ok &= check_file(file_path, "Coordinator source file")
    
    # Check startup script
    startup_script = f"{base_path}/scripts/start_network_coordinator.py"
    files_ok &= check_file(startup_script, "Startup script")
    
    print(f"\n🔧 Checking system configuration...")
    
    # Check systemd service (Linux only)
    if os.name == 'posix':
        service_file = "/etc/systemd/system/playergold-coordinator.service"
        check_file(service_file, "Systemd service file")
    
    # Check data directories
    data_dirs = [
        f"{base_path}/data",
        f"{base_path}/logs"
    ]
    
    for dir_path in data_dirs:
        if os.path.exists(dir_path):
            print(f"✅ {dir_path} - Data directory")
        else:
            print(f"⚠️  {dir_path} - Data directory (will be created)")
    
    print(f"\n🧪 Testing coordinator import...")
    
    # Try to import the coordinator server
    try:
        sys.path.insert(0, base_path)
        from src.network_coordinator.server import app
        print("✅ Coordinator server can be imported")
        
        # Try to access the FastAPI app
        if hasattr(app, 'routes'):
            route_count = len(app.routes)
            print(f"✅ FastAPI app has {route_count} routes")
        
    except Exception as e:
        print(f"❌ Failed to import coordinator server: {e}")
        deps_ok = False
    
    print("\n" + "=" * 60)
    
    if deps_ok and files_ok:
        print("🎉 ALL CHECKS PASSED - Coordinator is ready to run!")
        print("\n🚀 To start the coordinator:")
        print(f"   cd {base_path}")
        print("   python scripts/start_network_coordinator.py")
        return True
    else:
        print("❌ SOME CHECKS FAILED - Coordinator needs setup")
        print("\n🔧 To fix issues:")
        print("   1. Install missing dependencies: pip install fastapi uvicorn aiohttp pydantic cryptography")
        print("   2. Copy missing source files")
        print("   3. Run setup script: sudo ./scripts/fix_coordinator_dependencies.sh")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)