"""Test the enhancements API endpoint."""

import asyncio
import httpx


async def test_enhancements_endpoint():
    """Test that the enhancements endpoint works."""

    base_url = "http://localhost:8000"

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            # Test 1: Get all enhancements
            print("=" * 80)
            print("TEST 1: GET /api/enhancements")
            print("=" * 80)

            response = await client.get(f"{base_url}/api/enhancements")
            print(f"Status Code: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                enhancements = data.get("enhancements", [])
                progress = data.get("progress", {})
                metadata = data.get("metadata", {})

                print(f"✅ Successfully retrieved {len(enhancements)} enhancements")
                print(f"\nProject: {metadata.get('project_name')}")
                print(f"Version: {metadata.get('version')}")
                print(f"Last Updated: {metadata.get('last_updated')}")

                print(f"\nProgress:")
                print(f"  Completion Rate: {progress.get('completion_rate')}")
                print(f"  Complete: {progress.get('complete')}")
                print(f"  In Progress: {progress.get('in_progress')}")
                print(f"  Design: {progress.get('design')}")
                print(f"  Planned: {progress.get('planned')}")

                print(f"\nFirst 3 Enhancements:")
                for i, enh in enumerate(enhancements[:3]):
                    print(f"\n  {i+1}. Enhancement {enh.get('id')}: {enh.get('title')}")
                    print(f"     Status: {enh.get('status')}")
                    print(f"     Completion: {enh.get('completion_percentage')}%")
                    print(f"     Estimated Hours: {enh.get('estimated_hours')}")
                    print(f"     Actual Hours: {enh.get('actual_hours')}")
            else:
                print(f"❌ Failed: {response.text}")

            print("\n")

            # Test 2: Get specific enhancement
            print("=" * 80)
            print("TEST 2: GET /api/enhancements/012 (Enhancement 012)")
            print("=" * 80)

            response = await client.get(f"{base_url}/api/enhancements/012")
            print(f"Status Code: {response.status_code}")

            if response.status_code == 200:
                enh = response.json()
                print(f"✅ Retrieved Enhancement 012")
                print(f"\nTitle: {enh.get('title')}")
                print(f"Status: {enh.get('status')}")
                print(f"Priority: {enh.get('priority')}")
                print(f"Completion: {enh.get('completion_percentage')}%")
                print(f"Estimated Hours: {enh.get('estimated_hours')}")
                print(f"Actual Hours: {enh.get('actual_hours')}")
                print(f"Completion Date: {enh.get('completion_date')}")

                success_criteria = enh.get('success_criteria', [])
                print(f"\nSuccess Criteria ({len(success_criteria)}):")
                for criterion in success_criteria[:3]:
                    print(f"  - {criterion}")
            else:
                print(f"❌ Failed: {response.text}")

            print("\n")

            # Test 3: Get enhancements by status
            print("=" * 80)
            print("TEST 3: GET /api/enhancements/status/Complete")
            print("=" * 80)

            response = await client.get(f"{base_url}/api/enhancements/status/Complete")
            print(f"Status Code: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                enhancements = data.get("enhancements", [])
                total = data.get("total")

                print(f"✅ Retrieved {total} completed enhancements")
                for enh in enhancements:
                    print(f"  - {enh.get('id')}: {enh.get('title')}")
            else:
                print(f"❌ Failed: {response.text}")

        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_enhancements_endpoint())
