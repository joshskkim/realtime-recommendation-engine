#!/usr/bin/env python3
# generate-mock-screenshots.py
# Place in: /scripts/generate-mock-screenshots.py

import os
from pathlib import Path

def create_svg_screenshot(title, content, filename, width=1920, height=1080):
    svg = f'''<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="grad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#1e3c72;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#2a5298;stop-opacity:1" />
    </linearGradient>
  </defs>
  <rect width="{width}" height="{height}" fill="url(#grad)"/>
  <text x="{width//2}" y="80" font-family="Arial" font-size="48" font-weight="bold" fill="white" text-anchor="middle">{title}</text>
  {content}
</svg>'''
    
    Path("docs/images").mkdir(parents=True, exist_ok=True)
    with open(f"docs/images/{filename}", "w") as f:
        f.write(svg)
    print(f"✅ Generated: docs/images/{filename}")

# Grafana Dashboard
grafana_content = '''
  <rect x="100" y="150" width="1720" height="100" rx="10" fill="rgba(255,255,255,0.1)"/>
  <text x="120" y="210" font-size="32" fill="white">📊 Metrics Overview</text>
  
  <g transform="translate(100, 300)">
    <rect width="400" height="250" rx="10" fill="rgba(16,185,129,0.2)"/>
    <text x="20" y="40" font-size="24" fill="white">Request Rate</text>
    <text x="20" y="120" font-size="64" font-weight="bold" fill="#10b981">1,250/s</text>
    <polyline points="20,200 80,180 140,190 200,150 260,160 320,140 380,145" stroke="#10b981" stroke-width="3" fill="none"/>
  </g>
  
  <g transform="translate(550, 300)">
    <rect width="400" height="250" rx="10" fill="rgba(59,130,246,0.2)"/>
    <text x="20" y="40" font-size="24" fill="white">Response Time</text>
    <text x="20" y="120" font-size="64" font-weight="bold" fill="#3b82f6">45ms</text>
    <polyline points="20,200 80,195 140,190 200,188 260,185 320,182 380,180" stroke="#3b82f6" stroke-width="3" fill="none"/>
  </g>
  
  <g transform="translate(1000, 300)">
    <rect width="400" height="250" rx="10" fill="rgba(239,68,68,0.2)"/>
    <text x="20" y="40" font-size="24" fill="white">Error Rate</text>
    <text x="20" y="120" font-size="64" font-weight="bold" fill="#10b981">0.02%</text>
    <polyline points="20,200 80,199 140,200 200,199 260,200 320,199 380,200" stroke="#10b981" stroke-width="3" fill="none"/>
  </g>
  
  <g transform="translate(1450, 300)">
    <rect width="370" height="250" rx="10" fill="rgba(139,92,246,0.2)"/>
    <text x="20" y="40" font-size="24" fill="white">CPU Usage</text>
    <text x="20" y="120" font-size="64" font-weight="bold" fill="#8b5cf6">18%</text>
    <rect x="20" y="180" width="330" height="40" rx="5" fill="rgba(139,92,246,0.3)"/>
    <rect x="20" y="180" width="60" height="40" rx="5" fill="#8b5cf6"/>
  </g>'''

# CI/CD Pipeline
cicd_content = '''
  <rect x="100" y="200" width="1720" height="600" rx="15" fill="rgba(0,0,0,0.3)"/>
  
  <g transform="translate(200, 300)">
    <circle cx="50" cy="50" r="40" fill="#3b82f6"/>
    <text x="50" y="58" font-size="24" fill="white" text-anchor="middle">Code</text>
    <text x="50" y="120" font-size="18" fill="white" text-anchor="middle">GitHub</text>
  </g>
  
  <line x1="290" y1="350" x2="410" y2="350" stroke="white" stroke-width="3" marker-end="url(#arrow)"/>
  
  <g transform="translate(450, 300)">
    <circle cx="50" cy="50" r="40" fill="#10b981"/>
    <text x="50" y="58" font-size="24" fill="white" text-anchor="middle">Build</text>
    <text x="50" y="120" font-size="18" fill="white" text-anchor="middle">Docker</text>
  </g>
  
  <line x1="540" y1="350" x2="660" y2="350" stroke="white" stroke-width="3"/>
  
  <g transform="translate(700, 300)">
    <circle cx="50" cy="50" r="40" fill="#f59e0b"/>
    <text x="50" y="58" font-size="24" fill="white" text-anchor="middle">Test</text>
    <text x="50" y="120" font-size="18" fill="white" text-anchor="middle">Jest/PyTest</text>
  </g>
  
  <line x1="790" y1="350" x2="910" y2="350" stroke="white" stroke-width="3"/>
  
  <g transform="translate(950, 300)">
    <circle cx="50" cy="50" r="40" fill="#8b5cf6"/>
    <text x="50" y="58" font-size="24" fill="white" text-anchor="middle">Scan</text>
    <text x="50" y="120" font-size="18" fill="white" text-anchor="middle">Security</text>
  </g>
  
  <line x1="1040" y1="350" x2="1160" y2="350" stroke="white" stroke-width="3"/>
  
  <g transform="translate(1200, 300)">
    <circle cx="50" cy="50" r="40" fill="#ef4444"/>
    <text x="50" y="58" font-size="24" fill="white" text-anchor="middle">Deploy</text>
    <text x="50" y="120" font-size="18" fill="white" text-anchor="middle">K8s/AWS</text>
  </g>
  
  <text x="960" y="550" font-size="28" fill="white" text-anchor="middle">Automated Pipeline: Push → Production in &lt; 10 minutes</text>'''

# Swagger UI
swagger_content = '''
  <rect x="100" y="150" width="1720" height="800" rx="10" fill="rgba(255,255,255,0.95)"/>
  
  <rect x="100" y="150" width="1720" height="80" fill="#3b82f6"/>
  <text x="140" y="200" font-size="36" font-weight="bold" fill="white">Recommendation API v1.0</text>
  
  <g transform="translate(140, 280)">
    <rect width="1640" height="80" rx="5" fill="#10b981" fill-opacity="0.1" stroke="#10b981" stroke-width="2"/>
    <text x="20" y="35" font-size="20" font-weight="bold" fill="#10b981">GET</text>
    <text x="100" y="35" font-size="20" fill="#1e293b">/api/recommendations/{userId}</text>
    <text x="100" y="55" font-size="16" fill="#64748b">Get personalized recommendations for a user</text>
  </g>
  
  <g transform="translate(140, 380)">
    <rect width="1640" height="80" rx="5" fill="#3b82f6" fill-opacity="0.1" stroke="#3b82f6" stroke-width="2"/>
    <text x="20" y="35" font-size="20" font-weight="bold" fill="#3b82f6">POST</text>
    <text x="100" y="35" font-size="20" fill="#1e293b">/api/events/interaction</text>
    <text x="100" y="55" font-size="16" fill="#64748b">Record user interaction event</text>
  </g>
  
  <g transform="translate(140, 480)">
    <rect width="1640" height="80" rx="5" fill="#10b981" fill-opacity="0.1" stroke="#10b981" stroke-width="2"/>
    <text x="20" y="35" font-size="20" font-weight="bold" fill="#10b981">GET</text>
    <text x="100" y="35" font-size="20" fill="#1e293b">/api/products/trending</text>
    <text x="100" y="55" font-size="16" fill="#64748b">Get trending products</text>
  </g>
  
  <g transform="translate(140, 580)">
    <rect width="1640" height="80" rx="5" fill="#f59e0b" fill-opacity="0.1" stroke="#f59e0b" stroke-width="2"/>
    <text x="20" y="35" font-size="20" font-weight="bold" fill="#f59e0b">PUT</text>
    <text x="100" y="35" font-size="20" fill="#1e293b">/api/models/retrain</text>
    <text x="100" y="55" font-size="16" fill="#64748b">Trigger model retraining</text>
  </g>
  
  <g transform="translate(140, 680)">
    <rect width="1640" height="80" rx="5" fill="#ef4444" fill-opacity="0.1" stroke="#ef4444" stroke-width="2"/>
    <text x="20" y="35" font-size="20" font-weight="bold" fill="#ef4444">DELETE</text>
    <text x="100" y="35" font-size="20" fill="#1e293b">/api/cache/clear</text>
    <text x="100" y="55" font-size="16" fill="#64748b">Clear recommendation cache</text>
  </g>'''

# A/B Testing
ab_content = '''
  <rect x="100" y="200" width="800" height="600" rx="10" fill="rgba(255,255,255,0.1)"/>
  <text x="500" y="250" font-size="32" fill="white" text-anchor="middle">A/B Test Results</text>
  
  <g transform="translate(150, 300)">
    <rect width="350" height="400" rx="10" fill="rgba(59,130,246,0.2)"/>
    <text x="175" y="40" font-size="28" fill="white" text-anchor="middle">Variant A (Control)</text>
    <text x="30" y="100" font-size="20" fill="white">Conversion Rate:</text>
    <text x="30" y="140" font-size="36" font-weight="bold" fill="#3b82f6">12.3%</text>
    <text x="30" y="200" font-size="20" fill="white">Avg. Order Value:</text>
    <text x="30" y="240" font-size="36" font-weight="bold" fill="#3b82f6">$67.50</text>
    <text x="30" y="300" font-size="20" fill="white">Sample Size:</text>
    <text x="30" y="340" font-size="36" font-weight="bold" fill="#3b82f6">10,000</text>
  </g>
  
  <g transform="translate(550, 300)">
    <rect width="350" height="400" rx="10" fill="rgba(16,185,129,0.2)"/>
    <text x="175" y="40" font-size="28" fill="white" text-anchor="middle">Variant B (ML Model)</text>
    <text x="30" y="100" font-size="20" fill="white">Conversion Rate:</text>
    <text x="30" y="140" font-size="36" font-weight="bold" fill="#10b981">18.7% ↑</text>
    <text x="30" y="200" font-size="20" fill="white">Avg. Order Value:</text>
    <text x="30" y="240" font-size="36" font-weight="bold" fill="#10b981">$82.30 ↑</text>
    <text x="30" y="300" font-size="20" fill="white">Sample Size:</text>
    <text x="30" y="340" font-size="36" font-weight="bold" fill="#10b981">10,000</text>
  </g>
  
  <g transform="translate(1000, 350)">
    <rect width="720" height="350" rx="10" fill="rgba(139,92,246,0.1)"/>
    <text x="360" y="40" font-size="28" fill="white" text-anchor="middle">Statistical Significance</text>
    <text x="30" y="100" font-size="24" fill="white">p-value: &lt; 0.001</text>
    <text x="30" y="150" font-size="24" fill="white">Confidence: 99.9%</text>
    <text x="30" y="200" font-size="24" fill="white">Lift: +52%</text>
    <text x="30" y="250" font-size="24" fill="#10b981" font-weight="bold">✓ Statistically Significant</text>
    <text x="30" y="300" font-size="20" fill="#94a3b8">Recommendation: Deploy Variant B</text>
  </g>'''

# Generate all screenshots
create_svg_screenshot("Grafana Monitoring Dashboard", grafana_content, "grafana-dashboard.svg")
create_svg_screenshot("CI/CD Pipeline", cicd_content, "cicd-pipeline.svg")
create_svg_screenshot("Swagger API Documentation", swagger_content, "swagger-ui.svg")
create_svg_screenshot("A/B Testing Dashboard", ab_content, "ab-testing.svg")

print("\n✅ All mock screenshots generated in docs/images/")