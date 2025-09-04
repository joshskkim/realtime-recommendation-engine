// generate-demo-screenshots.js  
// Place in: /scripts/screenshots/generate-demo-screenshots.js

const fs = require('fs');
const path = require('path');

class DemoScreenshotGenerator {
  constructor() {
    this.outputDir = './docs/media/screenshots';
    this.timestamp = new Date().toISOString().split('T')[0];
    this.setupDirectories();
  }

  setupDirectories() {
    ['monitoring', 'features', 'performance'].forEach(dir => {
      const fullPath = path.join(this.outputDir, dir);
      if (!fs.existsSync(fullPath)) {
        fs.mkdirSync(fullPath, { recursive: true });
      }
    });
  }

  generateSVGScreenshot(title, content, filename, type = 'monitoring') {
    const svg = `
<svg width="1920" height="1080" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#1e3c72;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#2a5298;stop-opacity:1" />
    </linearGradient>
  </defs>
  
  <rect width="1920" height="1080" fill="url(#bg)"/>
  
  <!-- Header -->
  <text x="960" y="100" font-family="Arial, sans-serif" font-size="48" 
        font-weight="bold" fill="white" text-anchor="middle">
    ${title}
  </text>
  
  <!-- Content -->
  <rect x="160" y="180" width="1600" height="800" rx="20" 
        fill="rgba(255,255,255,0.1)" stroke="rgba(255,255,255,0.2)" stroke-width="2"/>
  
  ${content}
  
  <!-- Timestamp -->
  <text x="960" y="1030" font-family="Arial, sans-serif" font-size="24" 
        fill="rgba(255,255,255,0.6)" text-anchor="middle">
    Generated: ${new Date().toLocaleString()}
  </text>
</svg>`;

    const filepath = path.join(this.outputDir, type, filename);
    fs.writeFileSync(filepath, svg);
    console.log(`   ✅ Generated: ${filename}`);
    return filepath;
  }

  generateMonitoringScreenshots() {
    console.log('\n📊 Generating Monitoring Screenshots...');

    // Docker Stats
    const statsContent = `
      <text x="200" y="300" font-family="monospace" font-size="24" fill="white">
        CONTAINER ID   NAME            CPU %    MEM USAGE / LIMIT
        a3f4c8b2d1    recommendation   12.5%    512MB / 2GB
        b7e9f3c5a8    postgres-db      3.2%     256MB / 1GB  
        c2d8a7f6e9    redis-cache      1.8%     128MB / 512MB
        d5b3c9f1a7    nginx-proxy      0.5%     64MB / 256MB
      </text>
      <rect x="200" y="400" width="400" height="200" rx="10" fill="rgba(16,185,129,0.2)"/>
      <text x="220" y="450" font-size="20" fill="#10b981">✓ All Systems Operational</text>`;
    
    this.generateSVGScreenshot('Docker Container Monitoring', statsContent, 
                              `docker-stats-${this.timestamp}.svg`);

    // Performance Metrics
    const perfContent = `
      <g transform="translate(300, 300)">
        <rect width="300" height="180" rx="10" fill="rgba(59,130,246,0.2)"/>
        <text x="20" y="40" font-size="24" fill="white">CPU Usage</text>
        <text x="20" y="80" font-size="36" font-weight="bold" fill="#3b82f6">18.5%</text>
      </g>
      <g transform="translate(650, 300)">
        <rect width="300" height="180" rx="10" fill="rgba(139,92,246,0.2)"/>
        <text x="20" y="40" font-size="24" fill="white">Memory</text>
        <text x="20" y="80" font-size="36" font-weight="bold" fill="#8b5cf6">2.1 GB</text>
      </g>
      <g transform="translate(1000, 300)">
        <rect width="300" height="180" rx="10" fill="rgba(16,185,129,0.2)"/>
        <text x="20" y="40" font-size="24" fill="white">Requests/sec</text>
        <text x="20" y="80" font-size="36" font-weight="bold" fill="#10b981">1,250</text>
      </g>`;

    this.generateSVGScreenshot('Performance Metrics Dashboard', perfContent,
                              `performance-dashboard-${this.timestamp}.svg`, 'performance');
  }

  generateFeatureScreenshots() {
    console.log('\n🎨 Generating Feature Screenshots...');

    // Landing Page
    const landingContent = `
      <text x="960" y="400" font-size="72" font-weight="bold" fill="white" text-anchor="middle">
        Real-Time Recommendation Engine
      </text>
      <text x="960" y="480" font-size="32" fill="rgba(255,255,255,0.8)" text-anchor="middle">
        Powered by Apache Kafka & Machine Learning
      </text>
      <rect x="760" y="550" width="400" height="80" rx="40" fill="#3b82f6"/>
      <text x="960" y="605" font-size="28" fill="white" text-anchor="middle">Get Started</text>`;

    this.generateSVGScreenshot('Landing Page', landingContent,
                              `01-landing-page-${this.timestamp}.svg`, 'features');

    // Dashboard
    const dashboardContent = `
      <g transform="translate(200, 250)">
        <rect width="700" height="300" rx="10" fill="rgba(255,255,255,0.05)"/>
        <text x="20" y="40" font-size="28" fill="white">Recent Recommendations</text>
        <line x1="20" y1="60" x2="680" y2="60" stroke="rgba(255,255,255,0.2)"/>
        <text x="20" y="100" font-size="20" fill="rgba(255,255,255,0.9)">• Product A - Score: 0.95</text>
        <text x="20" y="140" font-size="20" fill="rgba(255,255,255,0.9)">• Product B - Score: 0.92</text>
        <text x="20" y="180" font-size="20" fill="rgba(255,255,255,0.9)">• Product C - Score: 0.89</text>
      </g>
      <g transform="translate(950, 250)">
        <rect width="700" height="300" rx="10" fill="rgba(255,255,255,0.05)"/>
        <text x="20" y="40" font-size="28" fill="white">System Status</text>
        <line x1="20" y1="60" x2="680" y2="60" stroke="rgba(255,255,255,0.2)"/>
        <circle cx="40" cy="100" r="8" fill="#10b981"/>
        <text x="60" y="108" font-size="20" fill="rgba(255,255,255,0.9)">Kafka Streams: Active</text>
        <circle cx="40" cy="140" r="8" fill="#10b981"/>
        <text x="60" y="148" font-size="20" fill="rgba(255,255,255,0.9)">ML Model: Deployed</text>
      </g>`;

    this.generateSVGScreenshot('Dashboard View', dashboardContent,
                              `02-dashboard-${this.timestamp}.svg`, 'features');

    // API Response
    const apiContent = `
      <rect x="200" y="250" width="1520" height="600" rx="10" fill="rgba(0,0,0,0.3)"/>
      <text x="220" y="290" font-family="monospace" font-size="20" fill="#10b981">
        GET /api/recommendations/user/12345
      </text>
      <text x="220" y="340" font-family="monospace" font-size="18" fill="white">
        {
      </text>
      <text x="260" y="380" font-family="monospace" font-size="18" fill="white">
        "status": "success",
      </text>
      <text x="260" y="420" font-family="monospace" font-size="18" fill="white">
        "recommendations": [
      </text>
      <text x="300" y="460" font-family="monospace" font-size="18" fill="white">
        { "id": "prod_123", "score": 0.95, "category": "electronics" },
      </text>
      <text x="300" y="500" font-family="monospace" font-size="18" fill="white">
        { "id": "prod_456", "score": 0.92, "category": "books" }
      </text>
      <text x="260" y="540" font-family="monospace" font-size="18" fill="white">
        ],
      </text>
      <text x="260" y="580" font-family="monospace" font-size="18" fill="white">
        "timestamp": "${new Date().toISOString()}"
      </text>
      <text x="220" y="620" font-family="monospace" font-size="18" fill="white">
        }
      </text>`;

    this.generateSVGScreenshot('API Response Example', apiContent,
                              `03-api-response-${this.timestamp}.svg`, 'features');
  }

  generateREADME() {
    console.log('\n📝 Generating README content...');
    
    const readme = `
# 📸 Project Screenshots

## System Monitoring
![Docker Stats](docs/media/screenshots/monitoring/docker-stats-${this.timestamp}.svg)
*Real-time container monitoring showing CPU, memory, and network usage*

## Performance Dashboard
![Performance](docs/media/screenshots/performance/performance-dashboard-${this.timestamp}.svg)
*Key performance metrics including throughput and response times*

## Application Features

### Landing Page
![Landing](docs/media/screenshots/features/01-landing-page-${this.timestamp}.svg)
*Clean, modern landing page with clear call-to-action*

### Dashboard
![Dashboard](docs/media/screenshots/features/02-dashboard-${this.timestamp}.svg)
*Real-time recommendation dashboard with system status*

### API Response
![API](docs/media/screenshots/features/03-api-response-${this.timestamp}.svg)
*Example API response showing recommendation data structure*

---
Generated: ${new Date().toLocaleString()}
`;

    fs.writeFileSync(path.join(this.outputDir, 'README-screenshots.md'), readme);
    console.log('   ✅ README content generated');
  }

  run() {
    console.log('\n' + '='.repeat(60));
    console.log(' DEMO SCREENSHOT GENERATOR');
    console.log('='.repeat(60));
    
    this.generateMonitoringScreenshots();
    this.generateFeatureScreenshots();
    this.generateREADME();
    
    console.log('\n' + '='.repeat(60));
    console.log('✨ Demo screenshots generated successfully!');
    console.log(`📁 Output directory: ${path.resolve(this.outputDir)}`);
    console.log('\nNext steps:');
    console.log('1. Review generated SVG files');
    console.log('2. Convert to PNG if needed: npm install sharp');
    console.log('3. Add to your main README.md');
    console.log('='.repeat(60) + '\n');
  }
}

// Run if executed directly
if (require.main === module) {
  const generator = new DemoScreenshotGenerator();
  generator.run();
}

module.exports = DemoScreenshotGenerator;