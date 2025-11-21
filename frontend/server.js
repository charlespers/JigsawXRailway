import express from 'express';
import path from 'path';
import { fileURLToPath } from 'url';
import { existsSync } from 'fs';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const PORT = process.env.PORT || 3000;
const DIST_DIR = path.join(__dirname, 'dist');

// Verify dist directory exists
if (!existsSync(DIST_DIR)) {
  console.error(`ERROR: dist directory not found at ${DIST_DIR}`);
  console.error('Make sure npm run build completed successfully');
  process.exit(1);
}

console.log(`Starting server...`);
console.log(`PORT: ${PORT}`);
console.log(`DIST_DIR: ${DIST_DIR}`);
console.log(`Dist directory exists: ${existsSync(DIST_DIR)}`);

// Serve static files from the dist directory
app.use(express.static(DIST_DIR));

// Handle client-side routing - serve index.html for all routes
app.get('*', (req, res) => {
  const indexPath = path.join(DIST_DIR, 'index.html');
  if (!existsSync(indexPath)) {
    console.error(`ERROR: index.html not found at ${indexPath}`);
    return res.status(500).send('index.html not found');
  }
  res.sendFile(indexPath);
});

// Start server listening on 0.0.0.0 (all interfaces) and PORT
try {
  const server = app.listen(PORT, '0.0.0.0', () => {
    console.log(`✓ Server running on http://0.0.0.0:${PORT}`);
    console.log(`✓ Serving static files from ${DIST_DIR}`);
    console.log(`✓ Ready to accept connections`);
  });

  // Handle server errors
  server.on('error', (err) => {
    console.error('Server error:', err);
    if (err.code === 'EADDRINUSE') {
      console.error(`Port ${PORT} is already in use`);
    }
    process.exit(1);
  });

  // Handle process errors
  process.on('uncaughtException', (err) => {
    console.error('Uncaught exception:', err);
    process.exit(1);
  });

  process.on('unhandledRejection', (reason, promise) => {
    console.error('Unhandled rejection at:', promise, 'reason:', reason);
    process.exit(1);
  });
} catch (error) {
  console.error('Failed to start server:', error);
  process.exit(1);
}

process.on('SIGTERM', () => {
  console.log('SIGTERM received, shutting down gracefully');
  process.exit(0);
});

