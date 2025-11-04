#!/usr/bin/env python3
"""
Test dual-mode enhancement data adapter.

Tests reading and writing from both YAML and database with fallback support.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.data.enhancement_adapter import EnhancementDataAdapter


async def test_dual_mode():
    """Test dual-mode adapter functionality."""
    print("=" * 80)
    print("Testing Dual-Mode Enhancement Adapter")
    print("=" * 80)
    print()

    # Create adapter
    adapter = EnhancementDataAdapter()

    print(f"Configuration:")
    print(f"  Mode: {adapter.mode}")
    print(f"  Primary Source: {adapter.primary_source}")
    print(f"  Fallback Source: {adapter.fallback_source}")
    print(f"  Write to Both: {adapter.write_to_both}")
    print(f"  Database Enabled: {adapter.db_enabled}")
    print()

    # Test 1: Get all enhancements
    print("Test 1: Get All Enhancements")
    print("-" * 80)

    try:
        enhancements = await adapter.get_all_enhancements()
        print(f"✅ Found {len(enhancements)} enhancements")

        if enhancements:
            # Show first 3
            for enh in enhancements[:3]:
                print(f"   - {enh.enhancement_number}: {enh.title} ({enh.status})")
    except Exception as e:
        print(f"❌ Error: {e}")

    print()

    # Test 2: Get enhancements by project
    print("Test 2: Get Enhancements by Project")
    print("-" * 80)

    try:
        ai_enhancements = await adapter.get_all_enhancements(project_tag="ai_orchestrator")
        print(f"✅ Found {len(ai_enhancements)} enhancements for 'ai_orchestrator'")

        if ai_enhancements:
            for enh in ai_enhancements[:3]:
                print(f"   - {enh.enhancement_number}: {enh.title}")
    except Exception as e:
        print(f"❌ Error: {e}")

    print()

    # Test 3: Get specific enhancement
    print("Test 3: Get Specific Enhancement")
    print("-" * 80)

    try:
        enhancement = await adapter.get_enhancement("012", project_tag="ai_orchestrator")

        if enhancement:
            print(f"✅ Found Enhancement 012")
            print(f"   Title: {enhancement.title}")
            print(f"   Status: {enhancement.status}")
            print(f"   Phase: {enhancement.phase}")
            print(f"   Progress: {enhancement.completion_percentage}%")
        else:
            print("❌ Enhancement 012 not found")
    except Exception as e:
        print(f"❌ Error: {e}")

    print()

    # Test 4: Test fallback (simulate primary source failure)
    print("Test 4: Test Fallback Behavior")
    print("-" * 80)

    if adapter.mode == "dual":
        print("Dual mode active - fallback should work if primary fails")

        # Temporarily disable database to test YAML fallback
        if adapter.primary_source == "database":
            original_db_enabled = adapter.db_enabled
            adapter.db_enabled = False

            try:
                enhancements = await adapter.get_all_enhancements()
                print(f"✅ Fallback to YAML successful: {len(enhancements)} enhancements")
            except Exception as e:
                print(f"❌ Fallback failed: {e}")
            finally:
                adapter.db_enabled = original_db_enabled
    else:
        print(f"Single mode ({adapter.mode}) - no fallback testing needed")

    print()
    print("=" * 80)
    print("Testing Complete")
    print("=" * 80)


async def test_mode_switching():
    """Test switching between different modes."""
    print("\n" + "=" * 80)
    print("Testing Mode Switching")
    print("=" * 80)
    print()

    modes = ["yaml", "database", "dual"]

    for mode in modes:
        print(f"Testing Mode: {mode}")
        print("-" * 80)

        try:
            # Create temporary config
            import json
            from pathlib import Path

            config_file = Path("config/data_source_config_test.json")
            config = {
                "enhancement_tracking": {
                    "mode": mode,
                    "primary_source": "database" if mode == "dual" else mode,
                    "fallback_source": "yaml",
                    "write_to_both": True,
                    "yaml_file": "PROJECT_ENHANCEMENT_TRACKER_DB.yaml",
                    "mongodb_enabled": True
                }
            }

            config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)

            # Create adapter with test config
            adapter = EnhancementDataAdapter(str(config_file))

            # Try to get enhancements
            enhancements = await adapter.get_all_enhancements()
            print(f"✅ {mode} mode: Found {len(enhancements)} enhancements")

            # Clean up
            config_file.unlink()

        except Exception as e:
            print(f"❌ {mode} mode failed: {e}")

        print()


def main():
    """Run all tests."""
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "Dual-Mode Adapter Test Suite" + " " * 30 + "║")
    print("╚" + "=" * 78 + "╝")
    print()

    # Run async tests
    asyncio.run(test_dual_mode())
    asyncio.run(test_mode_switching())

    print("\n✨ All tests completed!\n")


if __name__ == "__main__":
    main()
