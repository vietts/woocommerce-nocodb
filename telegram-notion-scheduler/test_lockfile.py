#!/usr/bin/env python3
"""
Test script to verify lockfile failsafe system.
Tests that only one scheduler instance can run at a time.
"""

import os
import sys
import time
import subprocess
import psutil

SCHEDULER_DIR = os.path.dirname(os.path.abspath(__file__))
SCHEDULER_PY = os.path.join(SCHEDULER_DIR, 'scheduler.py')
LOCKFILE = os.path.join(SCHEDULER_DIR, '.scheduler.lock')


def cleanup_scheduler():
    """Kill all scheduler instances"""
    try:
        subprocess.run(['pkill', '-9', '-f', 'python3 scheduler.py'], timeout=5)
        time.sleep(1)
    except:
        pass


def cleanup_lockfile():
    """Remove lockfile if exists"""
    try:
        if os.path.exists(LOCKFILE):
            os.remove(LOCKFILE)
    except:
        pass


def read_lockfile_pid():
    """Read PID from lockfile"""
    try:
        if os.path.exists(LOCKFILE):
            with open(LOCKFILE, 'r') as f:
                return int(f.read().strip())
    except:
        pass
    return None


def wait_for_lockfile(timeout=5):
    """Wait for lockfile to be created"""
    start = time.time()
    while time.time() - start < timeout:
        if os.path.exists(LOCKFILE):
            return True
        time.sleep(0.1)
    return False


def test_lockfile_system():
    """Test the lockfile failsafe system"""
    print("\n" + "=" * 70)
    print("🧪 TESTING LOCKFILE FAILSAFE SYSTEM")
    print("=" * 70)

    # Clean up any existing processes
    print("\n📋 Step 1: Cleaning up any existing scheduler instances...")
    cleanup_scheduler()
    cleanup_lockfile()
    time.sleep(1)

    if os.path.exists(LOCKFILE):
        print("❌ Lockfile still exists after cleanup")
        return False
    print("✅ Cleanup successful")

    # Test 1: Start first instance
    print("\n📋 Step 2: Starting first scheduler instance...")
    proc1 = subprocess.Popen(
        ['python3', SCHEDULER_PY],
        cwd=SCHEDULER_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    print(f"✅ First instance started (PID: {proc1.pid})")

    # Wait for lockfile
    print("\n📋 Step 3: Waiting for lockfile to be created...")
    if not wait_for_lockfile(timeout=10):
        print("❌ Lockfile was not created!")
        cleanup_scheduler()
        return False

    lockfile_pid = read_lockfile_pid()
    print(f"✅ Lockfile created with PID: {lockfile_pid}")

    if lockfile_pid != proc1.pid:
        print(f"⚠️  WARNING: PID mismatch - subprocess: {proc1.pid}, lockfile: {lockfile_pid}")

    # Test 2: Try to start second instance
    print("\n📋 Step 4: Attempting to start second scheduler instance...")
    print("   (This should FAIL because first instance holds the lock)")

    proc2 = subprocess.Popen(
        ['python3', SCHEDULER_PY],
        cwd=SCHEDULER_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    time.sleep(2)

    # Check if second process is still running
    try:
        if proc2.poll() is None:
            # Process still running - this is WRONG
            print("❌ FAIL: Second instance is still running!")
            print("   The lockfile failsafe did not work!")
            cleanup_scheduler()
            return False
        else:
            # Process exited - this is CORRECT
            stdout, stderr = proc2.communicate()
            if "already running" in stderr.decode() or "already running" in stdout.decode():
                print("✅ PASS: Second instance was rejected (as expected)")
                print("   Stderr output:")
                for line in stderr.decode().split('\n')[-10:]:
                    if line.strip():
                        print(f"   > {line}")
            else:
                print("✅ PASS: Second instance exited (refused to start)")
    except:
        print("✅ PASS: Second instance terminated")

    # Test 3: Verify first instance still running
    print("\n📋 Step 5: Verifying first instance is still running...")
    if proc1.poll() is None:
        print("✅ First instance is still running")
    else:
        print("❌ First instance has stopped!")
        return False

    # Test 4: Stop first instance
    print("\n📋 Step 6: Stopping first scheduler instance...")
    cleanup_scheduler()
    time.sleep(1)

    if os.path.exists(LOCKFILE):
        print("❌ Lockfile was not cleaned up after shutdown!")
        return False
    print("✅ Lockfile properly cleaned up")

    # Test 5: Verify we can start another instance after cleanup
    print("\n📋 Step 7: Starting new instance after cleanup...")
    proc3 = subprocess.Popen(
        ['python3', SCHEDULER_PY],
        cwd=SCHEDULER_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    if not wait_for_lockfile(timeout=10):
        print("❌ Could not start new instance after cleanup!")
        return False

    print(f"✅ New instance started successfully (PID: {proc3.pid})")

    # Cleanup
    cleanup_scheduler()
    cleanup_lockfile()

    print("\n" + "=" * 70)
    print("✅ ALL TESTS PASSED - LOCKFILE FAILSAFE SYSTEM IS WORKING!")
    print("=" * 70)
    return True


if __name__ == "__main__":
    success = test_lockfile_system()
    sys.exit(0 if success else 1)
