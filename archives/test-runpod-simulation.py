#!/usr/bin/env python3
"""
Simple test script to demonstrate RunPod log integration
This simulates what RunPod should do when processing a request
"""

import requests
import time
import json

BACKEND_URL = "http://18.140.62.254"

def send_log(job_id: str, message: str):
    """Send a log message to the backend"""
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/crawler/log",
            json={
                "job_id": job_id,
                "message": message
            },
            timeout=5
        )
        if response.status_code == 200:
            print(f"✅ Log sent: {message[:50]}...")
            return True
        else:
            print(f"❌ Failed to send log: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error sending log: {e}")
        return False

def simulate_runpod_processing(job_id: str, keyword: str, num_domains: int):
    """Simulate RunPod processing with real-time logs"""
    
    print(f"\n{'='*60}")
    print(f"Simulating RunPod Processing")
    print(f"Job ID: {job_id}")
    print(f"Keyword: {keyword}")
    print(f"Domains: {num_domains}")
    print(f"{'='*60}\n")
    
    # Initial logs
    send_log(job_id, "[INFO] Initializing domain generation on RunPod...")
    time.sleep(0.5)
    
    send_log(job_id, f"[INFO] Keyword: {keyword}")
    time.sleep(0.3)
    
    send_log(job_id, f"[INFO] Target domains: {num_domains}")
    time.sleep(0.5)
    
    # Simulate domain generation
    domains = []
    for i in range(num_domains):
        domain = f"example-{i+1}.com"
        domains.append(domain)
        
        progress = int((i + 1) / num_domains * 100)
        send_log(job_id, f"[INFO] Progress: {progress}% - Generated: {domain}")
        time.sleep(0.8)
    
    # Completion logs
    send_log(job_id, f"[SUCCESS] Domain generation completed!")
    time.sleep(0.3)
    
    send_log(job_id, f"[INFO] Total domains generated: {len(domains)}")
    time.sleep(0.5)
    
    # Send summary (this is what the frontend expects)
    summary = {
        "status": "success",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "time_elapsed": "Simulated",
        "domains_generated": {"success": len(domains), "total": len(domains)},
        "screenshot": {"success": 0, "failed": 0, "skipped": 0, "total": 0},
        "domains_inserted": len(domains),
        "keywords": [keyword]
    }
    
    send_log(job_id, f"[SUMMARY] {json.dumps(summary)}")
    
    print(f"\n{'='*60}")
    print(f"✅ Simulation completed!")
    print(f"Generated domains: {domains}")
    print(f"{'='*60}\n")
    
    return domains

def main():
    print("\n🧪 RunPod Log Integration Test\n")
    
    # Get job_id from user
    print("To test this:")
    print("1. Open Domain Generator UI in your browser")
    print("2. Click 'Generate' to start a job")
    print("3. Copy the job_id from browser console or network tab")
    print("4. Paste it here\n")
    
    job_id = input("Enter job_id (or press Enter to skip): ").strip()
    
    if not job_id:
        print("\n⚠️  No job_id provided. Exiting.")
        print("\nAlternatively, you can call this function directly:")
        print("  simulate_runpod_processing('your-job-id', 'test keyword', 5)")
        return
    
    # Simulate processing
    keyword = input("Enter keyword (default: 'test keyword'): ").strip() or "test keyword"
    num_domains = input("Enter number of domains (default: 5): ").strip()
    num_domains = int(num_domains) if num_domains.isdigit() else 5
    
    simulate_runpod_processing(job_id, keyword, num_domains)

if __name__ == "__main__":
    main()
