// feature-demo.js
// Place in: /scripts/screenshots/feature-demo.js

const puppeteer = require('puppeteer');
const path = require('path');
const fs = require('fs');

class FeatureDemo {
  constructor(baseUrl = 'http://localhost:3000', outputDir = './docs/media/screenshots/features') {
    this.baseUrl = baseUrl;
    this.outputDir = outputDir;
    this.browser = null;
    this.page = null;
    this.ensureDirectory();
  }

  ensureDirectory() {
    if (!fs.existsSync(this.outputDir)) {
      fs.mkdirSync(this.outputDir, { recursive: true });
    }
  }

  async init() {
    this.browser = await puppeteer.launch({
      headless: false, // Set to true for CI/CD
      defaultViewport: {
        width: 1920,
        height: 1080
      },
      args: ['--no-sandbox', '--disable-setuid-sandbox']
    });
    this.page = await this.browser.newPage();
    
    // Set up console logging
    this.page.on('console', msg => console.log('Browser:', msg.text()));
  }

  async cleanup() {
    if (this.browser) {
      await this.browser.close();
    }
  }

  async screenshot(name, fullPage = false) {
    const timestamp = new Date().toISOString().split('T')[0];
    const filename = `${name}-${timestamp}.png`;
    const filepath = path.join(this.outputDir, filename);
    
    await this.page.screenshot({
      path: filepath,
      fullPage: fullPage
    });
    
    console.log(`📸 Screenshot saved: ${filename}`);
    return filepath;
  }

  async wait(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  // Feature: Landing Page
  async captureLandingPage() {
    console.log('\n🏠 Capturing Landing Page...');
    await this.page.goto(this.baseUrl, { waitUntil: 'networkidle2' });
    await this.wait(1000);
    await this.screenshot('01-landing-page');
  }

  // Feature: User Authentication
  async captureAuthentication() {
    console.log('\n🔐 Capturing Authentication Flow...');
    
    // Login page
    await this.page.goto(`${this.baseUrl}/login`, { waitUntil: 'networkidle2' });
    await this.screenshot('02-login-page');
    
    // Fill login form
    await this.page.type('#email', 'demo@example.com');
    await this.page.type('#password', 'password123');
    await this.screenshot('03-login-filled');
    
    // Submit and capture dashboard
    await Promise.all([
      this.page.waitForNavigation(),
      this.page.click('#login-button')
    ]);
    await this.wait(1000);
    await this.screenshot('04-dashboard');
  }

  // Feature: Main Functionality
  async captureMainFeature() {
    console.log('\n⭐ Capturing Main Feature...');
    
    // Navigate to main feature
    await this.page.goto(`${this.baseUrl}/feature`, { waitUntil: 'networkidle2' });
    await this.screenshot('05-feature-page');
    
    // Interact with feature
    if (await this.page.$('#start-button')) {
      await this.page.click('#start-button');
      await this.wait(2000);
      await this.screenshot('06-feature-in-progress');
    }
    
    // Capture results
    await this.wait(2000);
    await this.screenshot('07-feature-results');
  }

  // Feature: API Interaction
  async captureAPIDemo() {
    console.log('\n🔌 Capturing API Interaction...');
    
    await this.page.goto(`${this.baseUrl}/api-demo`, { waitUntil: 'networkidle2' });
    
    // Open network tab simulation
    await this.page.evaluate(() => {
      console.log('Making API request...');
    });
    
    // Trigger API call
    if (await this.page.$('#api-test')) {
      await this.page.click('#api-test');
      await this.page.waitForSelector('.api-response', { timeout: 5000 });
      await this.screenshot('08-api-response');
    }
  }

  // Feature: Error Handling
  async captureErrorHandling() {
    console.log('\n⚠️ Capturing Error Handling...');
    
    // Trigger an error scenario
    await this.page.goto(`${this.baseUrl}/test-error`, { waitUntil: 'networkidle2' });
    await this.screenshot('09-error-page');
    
    // Capture form validation
    await this.page.goto(`${this.baseUrl}/form`, { waitUntil: 'networkidle2' });
    if (await this.page.$('#submit-button')) {
      await this.page.click('#submit-button');
      await this.wait(500);
      await this.screenshot('10-validation-errors');
    }
  }

  // Feature: Mobile Responsive
  async captureMobileView() {
    console.log('\n📱 Capturing Mobile View...');
    
    // Set mobile viewport
    await this.page.setViewport({
      width: 375,
      height: 812,
      isMobile: true
    });
    
    await this.page.goto(this.baseUrl, { waitUntil: 'networkidle2' });
    await this.screenshot('11-mobile-view');
    
    // Reset viewport
    await this.page.setViewport({
      width: 1920,
      height: 1080
    });
  }

  // Create animated GIF from screenshots
  async createGIF() {
    console.log('\n🎬 Creating animated demo...');
    
    const gifScript = `
#!/bin/bash
# Place in: /scripts/screenshots/create-gif.sh

# Requires ImageMagick
convert -delay 150 -loop 0 ${this.outputDir}/*.png ${this.outputDir}/feature-demo.gif
echo "✅ GIF created: feature-demo.gif"
    `;
    
    fs.writeFileSync(
      path.join(path.dirname(this.outputDir), 'create-gif.sh'),
      gifScript
    );
    
    console.log('📝 GIF creation script saved to create-gif.sh');
    console.log('   Run: bash scripts/screenshots/create-gif.sh');
  }

  async runFullDemo() {
    console.log('\n🚀 Starting Feature Demo Capture\n');
    console.log('================================\n');
    
    try {
      await this.init();
      
      // Capture all features
      await this.captureLandingPage();
      await this.captureAuthentication();
      await this.captureMainFeature();
      await this.captureAPIDemo();
      await this.captureErrorHandling();
      await this.captureMobileView();
      
      // Create GIF script
      await this.createGIF();
      
      console.log('\n✨ Demo capture complete!');
      console.log(`📁 Screenshots saved to: ${this.outputDir}\n`);
      
    } catch (error) {
      console.error('❌ Demo capture failed:', error);
    } finally {
      await this.cleanup();
    }
  }
}

// Usage
async function main() {
  const demo = new FeatureDemo(
    process.env.APP_URL || 'http://localhost:3000',
    './docs/media/screenshots/features'
  );
  
  await demo.runFullDemo();
}

// Run if executed directly
if (require.main === module) {
  main().catch(console.error);
}

module.exports = FeatureDemo;