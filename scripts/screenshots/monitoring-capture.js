// monitoring-capture.js
// Place in: /scripts/screenshots/monitoring-capture.js

const { exec } = require('child_process');
const fs = require('fs');
const path = require('path');
const util = require('util');
const execPromise = util.promisify(exec);

class MonitoringCapture {
  constructor(outputDir = './docs/media/screenshots/monitoring') {
    this.outputDir = outputDir;
    this.ensureDirectory();
  }

  ensureDirectory() {
    if (!fs.existsSync(this.outputDir)) {
      fs.mkdirSync(this.outputDir, { recursive: true });
    }
  }

  async captureDockerStats(duration = 5) {
    console.log('📊 Capturing Docker stats...');
    const timestamp = new Date().toISOString().split('T')[0];
    const filename = `docker-stats-${timestamp}.txt`;
    
    try {
      // Capture docker stats for specified duration
      const { stdout } = await execPromise(
        `docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}"`
      );
      
      // Save raw stats
      fs.writeFileSync(
        path.join(this.outputDir, filename),
        stdout
      );
      
      // Generate HTML visualization
      const html = this.generateStatsHTML(stdout);
      fs.writeFileSync(
        path.join(this.outputDir, `docker-stats-${timestamp}.html`),
        html
      );
      
      console.log(`✅ Docker stats saved to ${filename}`);
      return stdout;
    } catch (error) {
      console.error('❌ Failed to capture Docker stats:', error.message);
    }
  }

  generateStatsHTML(stats) {
    return `
<!DOCTYPE html>
<html>
<head>
  <title>Docker Container Metrics</title>
  <style>
    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      padding: 20px;
      color: white;
    }
    .container {
      max-width: 1200px;
      margin: 0 auto;
    }
    h1 {
      text-align: center;
      margin-bottom: 30px;
      font-size: 2.5em;
      text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    .stats-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
      gap: 20px;
    }
    .stat-card {
      background: rgba(255, 255, 255, 0.1);
      backdrop-filter: blur(10px);
      border-radius: 15px;
      padding: 20px;
      border: 1px solid rgba(255, 255, 255, 0.2);
    }
    .stat-title {
      font-size: 1.2em;
      margin-bottom: 10px;
      opacity: 0.9;
    }
    .stat-value {
      font-size: 2em;
      font-weight: bold;
    }
    .timestamp {
      text-align: center;
      margin-top: 30px;
      opacity: 0.7;
    }
  </style>
</head>
<body>
  <div class="container">
    <h1>🚀 Container Performance Metrics</h1>
    <pre style="background: rgba(0,0,0,0.3); padding: 20px; border-radius: 10px; overflow-x: auto;">
${stats}
    </pre>
    <div class="timestamp">Generated: ${new Date().toLocaleString()}</div>
  </div>
</body>
</html>`;
  }

  async captureDockerLogs(containerName, lines = 50) {
    console.log(`📝 Capturing logs for ${containerName}...`);
    const timestamp = new Date().toISOString().split('T')[0];
    const filename = `logs-${containerName}-${timestamp}.txt`;
    
    try {
      const { stdout } = await execPromise(
        `docker logs --tail ${lines} --timestamps ${containerName}`
      );
      
      fs.writeFileSync(
        path.join(this.outputDir, filename),
        stdout
      );
      
      console.log(`✅ Logs saved to ${filename}`);
      return stdout;
    } catch (error) {
      console.error(`❌ Failed to capture logs for ${containerName}:`, error.message);
    }
  }

  async captureResourceUsage() {
    console.log('💻 Capturing system resource usage...');
    const metrics = {};
    
    try {
      // CPU info
      const { stdout: cpuInfo } = await execPromise(
        "docker stats --no-stream --format 'json' | jq -s 'map({name: .Name, cpu: .CPUPerc, memory: .MemPerc})'"
      ).catch(() => ({ stdout: '[]' }));
      
      metrics.containers = JSON.parse(cpuInfo || '[]');
      
      // Disk usage
      const { stdout: diskUsage } = await execPromise(
        "df -h | grep -E '^/dev/'"
      ).catch(() => ({ stdout: '' }));
      
      metrics.disk = diskUsage;
      
      // Save metrics
      fs.writeFileSync(
        path.join(this.outputDir, `metrics-${Date.now()}.json`),
        JSON.stringify(metrics, null, 2)
      );
      
      console.log('✅ Resource metrics captured');
      return metrics;
    } catch (error) {
      console.error('❌ Failed to capture resource usage:', error.message);
    }
  }

  async generateHealthCheck() {
    console.log('🏥 Running health checks...');
    const health = {
      timestamp: new Date().toISOString(),
      services: []
    };
    
    try {
      // Check container health
      const { stdout } = await execPromise(
        "docker ps --format 'json'"
      ).catch(() => ({ stdout: '[]' }));
      
      const containers = stdout.trim().split('\n')
        .filter(line => line)
        .map(line => {
          try {
            return JSON.parse(line);
          } catch {
            return null;
          }
        })
        .filter(Boolean);
      
      for (const container of containers) {
        health.services.push({
          name: container.Names,
          status: container.Status,
          state: container.State,
          ports: container.Ports
        });
      }
      
      // Save health report
      fs.writeFileSync(
        path.join(this.outputDir, `health-${Date.now()}.json`),
        JSON.stringify(health, null, 2)
      );
      
      console.log('✅ Health check complete');
      return health;
    } catch (error) {
      console.error('❌ Health check failed:', error.message);
    }
  }

  async captureAll(containers = []) {
    console.log('\n🎬 Starting monitoring capture session...\n');
    
    // Capture Docker stats
    await this.captureDockerStats();
    
    // Capture logs for specified containers
    for (const container of containers) {
      await this.captureDockerLogs(container);
    }
    
    // Capture resource usage
    await this.captureResourceUsage();
    
    // Generate health check
    await this.generateHealthCheck();
    
    console.log('\n✨ Monitoring capture complete!\n');
    console.log(`📁 Files saved to: ${this.outputDir}`);
  }
}

// Usage
async function main() {
  const capture = new MonitoringCapture();
  
  // Specify your container names here
  const containers = [
    'web-app',
    'api-server',
    'database',
    'redis-cache'
  ];
  
  await capture.captureAll(containers);
}

// Run if executed directly
if (require.main === module) {
  main().catch(console.error);
}

module.exports = MonitoringCapture;