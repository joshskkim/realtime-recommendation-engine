// docker-monitor.js
// Place in: /scripts/screenshots/docker-monitor.js

const { exec } = require('child_process');
const fs = require('fs');
const path = require('path');
const util = require('util');
const execPromise = util.promisify(exec);

class DockerMonitor {
  constructor(outputDir = './docs/media/screenshots/monitoring') {
    this.outputDir = outputDir;
    this.timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    this.ensureDirectory();
  }

  ensureDirectory() {
    if (!fs.existsSync(this.outputDir)) {
      fs.mkdirSync(this.outputDir, { recursive: true });
    }
  }

  async getRunningContainers() {
    try {
      const { stdout } = await execPromise('docker ps --format "{{.Names}}"');
      return stdout.trim().split('\n').filter(name => name);
    } catch (error) {
      console.log('⚠️  No containers running');
      return [];
    }
  }

  async captureDockerStats() {
    console.log('\n📊 Capturing Docker Statistics...');
    
    const containers = await this.getRunningContainers();
    if (containers.length === 0) {
      console.log('   No running containers to monitor');
      return;
    }

    console.log(`   Found ${containers.length} running containers`);
    
    // Capture stats
    try {
      const { stdout } = await execPromise(
        'docker stats --no-stream --format "json"'
      );
      
      const stats = stdout.trim().split('\n')
        .filter(line => line)
        .map(line => JSON.parse(line));
      
      // Generate readable report
      const report = this.generateReport(stats);
      fs.writeFileSync(
        path.join(this.outputDir, `stats-${this.timestamp}.json`),
        JSON.stringify(stats, null, 2)
      );
      fs.writeFileSync(
        path.join(this.outputDir, `report-${this.timestamp}.txt`),
        report
      );
      
      console.log('   ✅ Stats captured successfully');
      console.log('\n' + report);
      
    } catch (error) {
      console.error('   ❌ Failed to capture stats:', error.message);
    }
  }

  generateReport(stats) {
    let report = '='.repeat(60) + '\n';
    report += 'DOCKER CONTAINER PERFORMANCE REPORT\n';
    report += `Generated: ${new Date().toLocaleString()}\n`;
    report += '='.repeat(60) + '\n\n';

    stats.forEach(container => {
      report += `📦 ${container.Name}\n`;
      report += `   Status: Running\n`;
      report += `   CPU:    ${container.CPUPerc}\n`;
      report += `   Memory: ${container.MemUsage} (${container.MemPerc})\n`;
      report += `   Net I/O: ${container.NetIO}\n`;
      report += `   Disk I/O: ${container.BlockIO}\n\n`;
    });

    return report;
  }

  async captureLogs() {
    console.log('\n📝 Capturing Container Logs...');
    
    const containers = await this.getRunningContainers();
    if (containers.length === 0) {
      console.log('   No containers to capture logs from');
      return;
    }

    for (const container of containers) {
      try {
        const { stdout } = await execPromise(
          `docker logs --tail 20 --timestamps "${container}" 2>&1`
        );
        
        const logFile = path.join(this.outputDir, `logs-${container}-${this.timestamp}.txt`);
        fs.writeFileSync(logFile, stdout);
        console.log(`   ✅ Captured logs for ${container}`);
        
      } catch (error) {
        console.log(`   ⚠️  Could not capture logs for ${container}`);
      }
    }
  }

  async generateDashboard() {
    console.log('\n📈 Generating Monitoring Dashboard...');
    
    const containers = await this.getRunningContainers();
    const containerCards = containers.map(name => `
      <div class="container-card">
        <h3>${name}</h3>
        <div class="status">🟢 Running</div>
      </div>
    `).join('');

    const html = `
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Docker Monitoring - ${this.timestamp}</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
      background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
      color: white;
      padding: 2rem;
      min-height: 100vh;
    }
    .header {
      text-align: center;
      margin-bottom: 3rem;
    }
    h1 {
      font-size: 3rem;
      margin-bottom: 1rem;
      text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    .timestamp {
      opacity: 0.8;
      font-size: 1.1rem;
    }
    .stats-summary {
      max-width: 1200px;
      margin: 0 auto 3rem;
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
      gap: 2rem;
    }
    .stat-card {
      background: rgba(255,255,255,0.1);
      backdrop-filter: blur(10px);
      border-radius: 15px;
      padding: 2rem;
      text-align: center;
      border: 1px solid rgba(255,255,255,0.2);
    }
    .stat-value {
      font-size: 3rem;
      font-weight: bold;
      margin: 1rem 0;
    }
    .stat-label {
      opacity: 0.9;
      text-transform: uppercase;
      letter-spacing: 1px;
      font-size: 0.9rem;
    }
    .containers-grid {
      max-width: 1200px;
      margin: 0 auto;
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
      gap: 1.5rem;
    }
    .container-card {
      background: rgba(255,255,255,0.1);
      backdrop-filter: blur(10px);
      border-radius: 10px;
      padding: 1.5rem;
      border: 1px solid rgba(255,255,255,0.2);
    }
    .container-card h3 {
      margin-bottom: 1rem;
      font-size: 1.3rem;
    }
    .status {
      font-size: 1.1rem;
    }
    .no-containers {
      text-align: center;
      padding: 4rem;
      background: rgba(255,255,255,0.1);
      border-radius: 15px;
      max-width: 600px;
      margin: 0 auto;
    }
  </style>
</head>
<body>
  <div class="header">
    <h1>🐳 Docker Monitoring Dashboard</h1>
    <div class="timestamp">Last Updated: ${new Date().toLocaleString()}</div>
  </div>
  
  <div class="stats-summary">
    <div class="stat-card">
      <div class="stat-label">Total Containers</div>
      <div class="stat-value">${containers.length}</div>
    </div>
    <div class="stat-card">
      <div class="stat-label">Status</div>
      <div class="stat-value">✅</div>
    </div>
    <div class="stat-card">
      <div class="stat-label">Docker Version</div>
      <div class="stat-value">Active</div>
    </div>
  </div>

  ${containers.length > 0 ? `
    <div class="containers-grid">
      ${containerCards}
    </div>
  ` : `
    <div class="no-containers">
      <h2>No Running Containers</h2>
      <p style="margin-top: 1rem; opacity: 0.8;">
        Start your containers with: docker-compose up -d
      </p>
    </div>
  `}
</body>
</html>`;

    const dashboardFile = path.join(this.outputDir, `dashboard-${this.timestamp}.html`);
    fs.writeFileSync(dashboardFile, html);
    console.log(`   ✅ Dashboard saved to ${dashboardFile}`);
    
    return dashboardFile;
  }

  async checkDockerHealth() {
    console.log('\n🏥 Docker Health Check...');
    
    try {
      // Docker version
      const { stdout: version } = await execPromise('docker --version');
      console.log(`   Docker: ${version.trim()}`);
      
      // Docker compose version
      const { stdout: composeVersion } = await execPromise('docker compose version 2>/dev/null || docker-compose --version');
      console.log(`   Compose: ${composeVersion.trim()}`);
      
      // System info
      const { stdout: info } = await execPromise('docker system df');
      console.log('\n   Storage Usage:');
      console.log(info.split('\n').slice(0, 4).map(l => '   ' + l).join('\n'));
      
      return true;
    } catch (error) {
      console.error('   ❌ Docker health check failed:', error.message);
      return false;
    }
  }

  async run() {
    console.log('\n' + '='.repeat(60));
    console.log(' DOCKER MONITORING CAPTURE');
    console.log('='.repeat(60));
    
    // Check Docker
    const dockerHealthy = await this.checkDockerHealth();
    if (!dockerHealthy) {
      console.log('\n⚠️  Please ensure Docker is running');
      return;
    }
    
    // Run captures
    await this.captureDockerStats();
    await this.captureLogs();
    const dashboard = await this.generateDashboard();
    
    console.log('\n' + '='.repeat(60));
    console.log('✨ Monitoring capture complete!');
    console.log(`📁 Output: ${this.outputDir}`);
    console.log(`📊 Dashboard: file://${path.resolve(dashboard)}`);
    console.log('='.repeat(60) + '\n');
  }
}

// Run if executed directly
if (require.main === module) {
  const monitor = new DockerMonitor();
  monitor.run().catch(console.error);
}

module.exports = DockerMonitor;