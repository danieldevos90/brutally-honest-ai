# BrutallyHonest.io Landing Page

A modern, conversion-optimized landing page for BrutallyHonest.io - AI-powered verification system that validates if what people say matches what they actually do.

## 🎯 Features

- **Modern OpenAI-Inspired Design**: Clean, minimal aesthetic with professional appearance
- **Tokenized Theme System**: CSS variables for consistent branding and easy customization
- **SEO Optimized**: Complete meta tags, Schema.org markup, sitemap, and robots.txt
- **Conversion Focused**: Strategic CTAs, contact form, and call-back request functionality
- **Fully Responsive**: Mobile-first design that works on all devices
- **Performance Optimized**: Fast loading with compression and security headers
- **Vercel Ready**: One-click deployment to Vercel

## 🚀 Quick Start

### Local Development

1. **Install Dependencies**
```bash
cd landing-page
npm install
```

2. **Run Development Server**
```bash
npm run dev
```

3. **Access the Site**
Open your browser to `http://localhost:3000`

### Production Build

```bash
npm start
```

## 📦 Project Structure

```
landing-page/
├── public/               # Static assets
│   ├── theme.css        # Tokenized design system
│   ├── styles.css       # Landing page specific styles
│   ├── script.js        # Client-side JavaScript
│   ├── favicon.svg      # Site favicon
│   ├── robots.txt       # SEO: Search engine instructions
│   └── sitemap.xml      # SEO: Site structure
├── views/               # EJS templates
│   ├── index.ejs        # Main landing page
│   └── 404.ejs          # 404 error page
├── server.js            # Node.js/Express server
├── package.json         # Dependencies
├── vercel.json          # Vercel deployment config
└── README.md           # This file
```

## 🎨 Design System

The landing page uses a tokenized design system with CSS variables for easy customization:

### Color Tokens
- Primary: `--color-primary` (#10a37f)
- Accent: `--color-accent` (#ff6b6b)
- Text colors: `--color-text-primary`, `--color-text-secondary`, `--color-text-tertiary`
- Background colors: `--color-bg-primary`, `--color-bg-secondary`, `--color-bg-tertiary`

### Typography Tokens
- Font sizes: `--text-xs` to `--text-6xl`
- Font families: `--font-primary`, `--font-mono`

### Spacing Tokens
- Space scale: `--space-1` (4px) to `--space-24` (96px)

### Component Tokens
- Border radius: `--radius-sm` to `--radius-full`
- Shadows: `--shadow-sm` to `--shadow-xl`
- Transitions: `--transition-fast`, `--transition-base`, `--transition-slow`

## 🔧 Customization

### Updating Colors

Edit `/public/theme.css`:

```css
:root {
  --color-primary: #10a37f;  /* Change primary color */
  --color-accent: #ff6b6b;   /* Change accent color */
}
```

### Adding New Sections

1. Add HTML to `/views/index.ejs`
2. Add styles to `/public/styles.css`
3. Add interactions to `/public/script.js`

### Modifying Contact Form

The contact form submits to `/api/contact`. To integrate with your email service or CRM:

Edit `/server.js`:

```javascript
app.post('/api/contact', async (req, res) => {
  // Add your email service integration here
  // e.g., SendGrid, Mailgun, HubSpot, etc.
});
```

## 🚀 Deployment to Vercel

### Option 1: Vercel CLI (Recommended)

1. **Install Vercel CLI**
```bash
npm install -g vercel
```

2. **Deploy**
```bash
cd landing-page
vercel
```

3. **Follow Prompts**
- Set up and deploy: Yes
- Which scope: Select your account
- Link to existing project: No
- Project name: brutallyhonest-landing (or your preference)
- Directory: `./`
- Override settings: No

4. **Production Deployment**
```bash
vercel --prod
```

### Option 2: Vercel Dashboard

1. Go to [vercel.com](https://vercel.com)
2. Click "Add New" → "Project"
3. Import your Git repository
4. Set root directory to `landing-page`
5. Click "Deploy"

### Custom Domain Setup

1. Go to your Vercel project settings
2. Navigate to "Domains"
3. Add `brutallyhonest.io`
4. Update your DNS records as instructed
5. Wait for SSL certificate to be issued (automatic)

## 📊 SEO Features

- **Meta Tags**: Complete Open Graph and Twitter Card tags
- **Schema.org Markup**: Organization and WebApplication schemas
- **Sitemap**: Auto-generated sitemap.xml
- **Robots.txt**: Search engine crawling instructions
- **Semantic HTML**: Proper heading hierarchy and ARIA labels
- **Performance**: Fast loading with compression and caching

## 🔒 Security Features

- **Helmet.js**: Security headers middleware
- **Rate Limiting**: API endpoint protection
- **CSP**: Content Security Policy headers
- **HTTPS**: Enforced on Vercel
- **XSS Protection**: Cross-site scripting prevention

## 📈 Analytics Integration

To add analytics (Google Analytics, Plausible, etc.), add the tracking code to `/views/index.ejs` before the closing `</head>` tag:

```html
<!-- Google Analytics -->
<script async src="https://www.googletagmanager.com/gtag/js?id=GA_MEASUREMENT_ID"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'GA_MEASUREMENT_ID');
</script>
```

## 🎯 Conversion Optimization

The landing page includes:

- **Above-the-fold CTA**: Primary call-to-action visible immediately
- **Clear Value Proposition**: "Is what you say also what you do?"
- **Social Proof Sections**: Features, use cases, testimonials (ready to add)
- **Multiple CTAs**: Strategically placed throughout the page
- **Contact Form**: With callback request option
- **Fast Loading**: Optimized for quick page loads
- **Mobile Optimized**: Touch-friendly buttons and forms

## 📝 Content Updates

### Updating Hero Section
Edit `/views/index.ejs`, section with class `.hero`

### Adding Testimonials
Add a new section after `.use-cases` in `/views/index.ejs`:

```html
<section class="section testimonials">
  <!-- Add testimonial cards here -->
</section>
```

### Updating Footer Links
Edit footer section in `/views/index.ejs`

## 🐛 Troubleshooting

### Port Already in Use
```bash
# Kill process on port 3000
lsof -ti:3000 | xargs kill -9
```

### CSS Not Loading
- Clear browser cache
- Check `/public/` directory exists
- Verify Express static middleware is configured

### Form Not Submitting
- Check browser console for errors
- Verify `/api/contact` endpoint is working
- Test with browser dev tools network tab

## 📞 Support

For questions or issues:
- Email: hello@brutallyhonest.io
- Website: https://brutallyhonest.io

## 📄 License

Copyright © 2024 BrutallyHonest.io. All rights reserved.

