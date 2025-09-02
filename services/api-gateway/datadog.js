// Datadog APM for Node.js
const tracer = require('dd-trace').init({
  logInjection: true,
  analytics: true,
  runtimeMetrics: true,
  profiling: true
});

// StatsD client for custom metrics
const StatsD = require('node-statsd');
const dogstatsd = new StatsD({
  host: process.env.DD_AGENT_HOST || 'localhost',
  port: 8125
});

// Middleware for tracking requests
app.use((req, res, next) => {
  const start = Date.now();
  
  res.on('finish', () => {
    const duration = Date.now() - start;
    dogstatsd.histogram('api.request.duration', duration, [`endpoint:${req.path}`, `method:${req.method}`, `status:${res.statusCode}`]);
    dogstatsd.increment('api.request.count', 1, [`endpoint:${req.path}`, `method:${req.method}`]);
  });
  
  next();
});
