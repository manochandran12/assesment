import requests
import sys
import json
from datetime import datetime
import time

class URLShortenerTester:
    def __init__(self, base_url="https://url-minifier.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.created_short_codes = []  # Track created codes for cleanup/testing

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        if endpoint.startswith('/api'):
            url = f"{self.base_url}{endpoint}"
        elif endpoint.startswith('/'):
            url = f"{self.base_url}{endpoint}"
        else:
            url = f"{self.api_url}/{endpoint}"
            
        if headers is None:
            headers = {'Content-Type': 'application/json'}

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, allow_redirects=False)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    print(f"   Response: {json.dumps(response_data, indent=2)[:200]}...")
                    return True, response_data
                except:
                    print(f"   Response: {response.text[:200]}...")
                    return True, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                print(f"   Response: {response.text[:200]}...")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_health_check(self):
        """Test health check endpoint"""
        return self.run_test("Health Check", "GET", "health", 200)

    def test_single_url_shorten(self, url, custom_code=None):
        """Test single URL shortening"""
        data = {"url": url}
        if custom_code:
            data["custom_code"] = custom_code
            
        success, response = self.run_test(
            f"Single URL Shorten {'with custom code' if custom_code else ''}",
            "POST", "shorten", 200, data
        )
        
        if success and 'short_code' in response:
            self.created_short_codes.append(response['short_code'])
            return response['short_code'], response
        return None, {}

    def test_bulk_url_shorten(self, urls):
        """Test bulk URL shortening"""
        data = {"urls": urls}
        success, response = self.run_test(
            "Bulk URL Shorten", "POST", "shorten-bulk", 200, data
        )
        
        if success and 'results' in response:
            for result in response['results']:
                if 'short_code' in result:
                    self.created_short_codes.append(result['short_code'])
        
        return success, response

    def test_get_urls(self, limit=10):
        """Test getting recent URLs"""
        return self.run_test(
            f"Get Recent URLs (limit={limit})", "GET", f"urls?limit={limit}", 200
        )

    def test_redirect(self, short_code):
        """Test redirect functionality - NEW /api/r/{short_code} endpoint"""
        return self.run_test(
            f"Redirect for code: {short_code}", "GET", f"/api/r/{short_code}", 302
        )

    def test_invalid_scenarios(self):
        """Test various invalid scenarios"""
        print("\n🧪 Testing Invalid Scenarios...")
        
        # Invalid URL
        self.run_test("Invalid URL", "POST", "shorten", 422, {"url": "not-a-url"})
        
        # Empty URL
        self.run_test("Empty URL", "POST", "shorten", 422, {"url": ""})
        
        # Invalid custom code (too short)
        self.run_test("Custom code too short", "POST", "shorten", 422, 
                     {"url": "https://google.com", "custom_code": "ab"})
        
        # Invalid custom code (too long)
        self.run_test("Custom code too long", "POST", "shorten", 422,
                     {"url": "https://google.com", "custom_code": "a" * 25})
        
        # Invalid custom code (special characters)
        self.run_test("Custom code with invalid chars", "POST", "shorten", 422,
                     {"url": "https://google.com", "custom_code": "test@123"})
        
        # Non-existent short code redirect
        self.run_test("Non-existent redirect", "GET", "/nonexistent123", 404)
        
        # Empty bulk URLs
        self.run_test("Empty bulk URLs", "POST", "shorten-bulk", 422, {"urls": []})
        
        # Too many bulk URLs (over 50)
        many_urls = ["https://example.com"] * 51
        self.run_test("Too many bulk URLs", "POST", "shorten-bulk", 422, {"urls": many_urls})

def main():
    print("🚀 Starting URL Shortener Backend Tests")
    print("=" * 50)
    
    tester = URLShortenerTester()
    
    # Test 1: Health Check
    print("\n📋 Phase 1: Health Check")
    tester.test_health_check()
    
    # Test 2: Single URL Shortening
    print("\n📋 Phase 2: Single URL Shortening")
    
    # Test with google.com
    short_code1, response1 = tester.test_single_url_shorten("https://google.com")
    
    # Test with custom code
    custom_code = f"test{int(time.time())}"  # Make it unique
    short_code2, response2 = tester.test_single_url_shorten("https://github.com", custom_code)
    
    # Test URL without protocol (should auto-add https://)
    short_code3, response3 = tester.test_single_url_shorten("example.com")
    
    # Test 3: Bulk URL Shortening
    print("\n📋 Phase 3: Bulk URL Shortening")
    bulk_urls = [
        "https://stackoverflow.com",
        "https://reddit.com", 
        "https://youtube.com",
        "twitter.com",  # Test without protocol
        "https://linkedin.com"
    ]
    tester.test_bulk_url_shorten(bulk_urls)
    
    # Test 4: Get Recent URLs
    print("\n📋 Phase 4: Get Recent URLs")
    tester.test_get_urls(10)
    tester.test_get_urls(5)
    
    # Test 5: Redirect Functionality (Critical!)
    print("\n📋 Phase 5: Redirect Functionality")
    if short_code1:
        tester.test_redirect(short_code1)
    if short_code2:
        tester.test_redirect(short_code2)
    if short_code3:
        tester.test_redirect(short_code3)
    
    # Test 6: Invalid Scenarios
    print("\n📋 Phase 6: Invalid Scenarios")
    tester.test_invalid_scenarios()
    
    # Test 7: Custom Code Conflicts
    print("\n📋 Phase 7: Custom Code Conflicts")
    if custom_code:
        # Try to use the same custom code again
        tester.run_test("Duplicate custom code", "POST", "shorten", 400,
                       {"url": "https://google.com", "custom_code": custom_code})
    
    # Final Results
    print("\n" + "=" * 50)
    print(f"📊 FINAL RESULTS")
    print(f"Tests Run: {tester.tests_run}")
    print(f"Tests Passed: {tester.tests_passed}")
    print(f"Tests Failed: {tester.tests_run - tester.tests_passed}")
    print(f"Success Rate: {(tester.tests_passed/tester.tests_run)*100:.1f}%")
    
    if tester.created_short_codes:
        print(f"\n📝 Created Short Codes for Further Testing:")
        for code in tester.created_short_codes[:5]:  # Show first 5
            print(f"   - {tester.base_url}/{code}")
    
    # Return exit code
    if tester.tests_passed == tester.tests_run:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠️  {tester.tests_run - tester.tests_passed} tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())