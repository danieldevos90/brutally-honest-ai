const express = require('express');
const path = require('path');
const helmet = require('helmet');
const compression = require('compression');
const rateLimit = require('express-rate-limit');
const { Resend } = require('resend');

const app = express();
const PORT = process.env.PORT || 3000;

// Initialize Resend
const resend = new Resend(process.env.RESEND_API_KEY);

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
  try {
    const { name, email, company, phone, message, requestCallback } = req.body;
    
    // Validate required fields
    if (!name || !email || !message) {
      return res.status(400).json({ 
        success: false, 
        error: 'Name, email, and message are required.' 
      });
    }
    
    // Send email via Resend
    const emailContent = `
New Contact Form Submission - Brutally Honest

Name: ${name}
Email: ${email}
Company: ${company || 'Not provided'}
Phone: ${phone || 'Not provided'}
Callback Requested: ${requestCallback ? 'Yes' : 'No'}

Message:
${message}
    `.trim();
    
    const { data, error } = await resend.emails.send({
      from: 'Brutally Honest <no-reply@brutallyhonest.io>',
      to: ['hello@brutallyhonest.io'],
      subject: `New Contact: ${name} ${company ? `from ${company}` : ''}`,
      text: emailContent,
      html: emailContent.replace(/\n/g, '<br>'),
    });
    
    if (error) {
      console.error('Resend error:', error);
      return res.status(500).json({ 
        success: false, 
        error: 'Failed to send message. Please try again.' 
      });
    }
    
    console.log('Email sent successfully:', data);
    res.json({ 
      success: true, 
      message: 'Thank you for your interest. We\'ll be in touch soon!' 
    });
    
  } catch (error) {
    console.error('Contact form error:', error);
    res.status(500).json({ 
      success: false, 
      error: 'Something went wrong. Please try again later.' 
    });
  }
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

