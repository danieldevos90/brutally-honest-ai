const express = require('express');
const path = require('path');
const helmet = require('helmet');
const compression = require('compression');
const rateLimit = require('express-rate-limit');

const app = express();
const PORT = process.env.PORT || 3000;

// Security and performance middleware
app.use(helmet({
  contentSecurityPolicy: false, // Disable CSP for now to avoid blocking issues
}));
app.use(compression());

// Rate limiting
const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100 // limit each IP to 100 requests per windowMs
});
app.use('/api/', limiter);

// Body parser
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// View engine setup
app.set('view engine', 'ejs');
app.set('views', path.join(__dirname, 'views'));

// Static files
app.use(express.static(path.join(__dirname, 'public')));

// Routes
app.get('/', (req, res) => {
  res.render('index', {
    title: 'BrutallyHonest.io - Actions Tell The Truth',
    description: 'Cut through the noise. We analyze what people do, not what they say. AI-powered insights for smarter hiring and authentic cultural fit.',
  });
});

// Contact form submission
app.post('/api/contact', async (req, res) => {
  const { name, email, company, phone, message, requestCallback } = req.body;
  
  // TODO: Implement email sending or CRM integration
  console.log('Contact form submission:', { name, email, company, phone, message, requestCallback });
  
  res.json({ success: true, message: 'Thank you for your interest. We\'ll be in touch soon!' });
});

// Health check for deployment
app.get('/health', (req, res) => {
  res.json({ status: 'healthy' });
});

// 404 handler
app.use((req, res) => {
  res.status(404).render('404', { title: '404 - Page Not Found' });
});

// Error handler
app.use((err, req, res, next) => {
  console.error(err.stack);
  res.status(500).json({ error: 'Something went wrong!' });
});

app.listen(PORT, () => {
  console.log(`BrutallyHonest.io landing page running on port ${PORT}`);
});

module.exports = app;

