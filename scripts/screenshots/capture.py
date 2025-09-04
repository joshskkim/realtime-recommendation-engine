#!/usr/bin/env python3
# capture.py
# Place in: /scripts/screenshots/capture.py

import subprocess
import json
import time
import os
from datetime import datetime
from pathlib import Path
import sys

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    print("⚠️  Selenium not installed. Feature screenshots will be skipped.")
    print("   Install with: pip install selenium")

class ProjectCapture:
    def __init__(self, base_url="http://localhost:3000"):
        self.base_url = base_url
        self.timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        self.output_dir = Path("docs/media/screenshots")
        self.setup_directories()
        
    def setup_directories(self):
        """Create output directories"""
        dirs = ["monitoring", "features", "performance"]
        for d in dirs:
            (self.output_dir / d).mkdir(parents=True, exist_ok=True)
    
    def run_command(self, cmd):
        """Execute shell command and return output"""
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            return result.stdout
        except Exception as e:
            print(f"❌ Command failed: {e}")
            return None
    
    def capture_docker_metrics(self):
        """Capture Docker container metrics"""
        print("\n📊 Capturing Docker Metrics...")
        
        # Container stats
        stats = self.run_command(
            'docker stats --no-stream --format "json"'
        )
        if stats:
            stats_file = self.output_dir / f"monitoring/stats-{self.timestamp}.json"
            stats_file.write_text(stats)
            print(f"  ✓ Stats saved to {stats_file.name}")
        
        # Container list with status
        containers = self.run_command(
            'docker ps -a --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"'
        )
        if containers:
            status_file = self.output_dir / f"monitoring/status-{self.timestamp}.txt"
            status_file.write_text(containers)
            print(f"  ✓ Status saved to {status_