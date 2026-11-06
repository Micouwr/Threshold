#!/usr/bin/env python3
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""
Build script for Threshold - Creates standalone executable with PyInstaller
"""

import os
import platform
import subprocess
import sys
from pathlib import Path

def build_executable():
    ROOT_DIR = Path(__file__).parent.resolve()
    MAIN_SCRIPT = ROOT_DIR / "gui" / "tkinter_app.py"
    system = platform.system()

    # Base PyInstaller command (cross-platform compatible)
    pyinstaller_cmd = [
        sys.executable, "-m", "PyInstaller",
        str(MAIN_SCRIPT),
        "--name", "Threshold",
        "--onedir",
        "--windowed",
        "--clean",
        "--noconfirm",
        "--paths", str(ROOT_DIR),
        "--paths", str(ROOT_DIR / "utils"),
        "--hidden-import", "database",
        "--hidden-import", "tailor",
        # Imported dynamically by the GUI (utils/ is added to sys.path at runtime)
        "--hidden-import", "job_parser",
        "--hidden-import", "config.settings",
        "--hidden-import", "jinja2",
        "--hidden-import", "PIL",
        "--hidden-import", "tkinter",
        "--add-data", f"{ROOT_DIR / 'config'}{os.pathsep}config",
        "--add-data", f"{ROOT_DIR / 'prompts'}{os.pathsep}prompts",
        "--add-data", f"{ROOT_DIR / 'assets'}{os.pathsep}assets",
    ]

    # App icon, per platform (PyInstaller takes .icns on macOS, .ico on Windows)
    if system == "Darwin":
        icon_file = ROOT_DIR / "assets" / "CareerForge_AI.icns"
    elif system == "Windows":
        icon_file = ROOT_DIR / "assets" / "CareerForge_AI.ico"
    else:
        icon_file = None
    if icon_file is not None:
        pyinstaller_cmd.extend(["--icon", str(icon_file)])

    # Add splash screen only on non-macOS platforms
    if system != "Darwin":
        splash_path = ROOT_DIR / "assets" / "splash.png"
        if splash_path.exists():
            pyinstaller_cmd.extend(["--splash", str(splash_path)])
        else:
            print(f"  Splash screen not found at {splash_path}")

    print(" Verifying build environment...")
    print("=" * 60)

    # Verify Python version
    print(f" Python {sys.version.split()[0]}")

    # Verify PyInstaller
    try:
        import PyInstaller
        print(f" PyInstaller {PyInstaller.__version__}")
    except ImportError:
        print(" PyInstaller not found. Install with: pip install pyinstaller")
        return False

    # Verify Pillow
    try:
        import PIL
        print(f" Pillow {PIL.__version__} (for icon conversion)")
    except ImportError:
        print(" Pillow not found. Install with: pip install Pillow")
        return False

    # Verify main script
    if MAIN_SCRIPT.exists():
        print(f" Main GUI script found: {MAIN_SCRIPT}")
    else:
        print(f" Main script not found: {MAIN_SCRIPT}")
        return False

    # Verify .env file
    env_file = ROOT_DIR / ".env"
    if env_file.exists():
        print(" .env configuration file found (Will NOT be bundled)")
        print("   (This is correct - users must provide their own API keys)")
    else:
        print(f"  Warning: .env file not found at {env_file}")
        print("   (Users will need to create this themselves)")

    # Verify icon files
    icon_dir = ROOT_DIR / "assets"
    ico = icon_dir / "CareerForge_AI.ico"
    if ico.exists():
        print(f"    - Windows icon: {ico} ({ico.stat().st_size:,} bytes)")
    icns = icon_dir / "CareerForge_AI.icns"
    if icns.exists():
        print(f"    - macOS icon: {icns} ({icns.stat().st_size:,} bytes)")

    print("-" * 60)

    # Run PyInstaller
    print("\n  Running PyInstaller...")
    print("=" * 60)
    print(f"   Running: {' '.join(pyinstaller_cmd)}\n")

    try:
        subprocess.run(pyinstaller_cmd, check=True, capture_output=False)
        print("\n" + "=" * 60)
        print(" Build completed successfully!")
        print("=" * 60)

        print("\n Distribution Instructions")
        print("=" * 60)
        print(" The executable is located in the './dist' folder.")
        print("  CRITICAL: Users must place their own '.env' file containing API keys")
        print("            in the same directory as the executable.")
        if system == "Darwin":
            print(" App bundle: ./dist/Threshold.app")
        elif system == "Windows":
            print(" Executable: ./dist/Threshold/Threshold.exe")
        else:
            print(" Executable: ./dist/Threshold/Threshold")

        return True

    except subprocess.CalledProcessError as e:
        print("\n Build failed!")
        print(f"Error code: {e.returncode}")
        return False
    except KeyboardInterrupt:
        print("\n\n  Build interrupted by user")
        return False
    except Exception as e:
        print(f"\n Build failed with unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = build_executable()
    sys.exit(0 if success else 1)
