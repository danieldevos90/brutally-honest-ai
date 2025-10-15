# Deployment Guide for BrutallyHonest.io Landing Page

## 🚀 Deploying to Vercel (Recommended)

Vercel is the recommended platform for deploying this Node.js landing page. It provides:
- Automatic HTTPS
- Global CDN
- Zero configuration
- Automatic deployments from Git
- Custom domain support

### Prerequisites

1. GitHub account with your code repository
2. Vercel account (free at [vercel.com](https://vercel.com))

### Step-by-Step Deployment

#### Method 1: Vercel Dashboard (Easiest)

1. **Push Code to GitHub**
   ```bash
   cd landing-page
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/yourusername/brutallyhonest-landing.git
   git push -u origin main
   ```

2. **Connect to Vercel**
   - Go to [vercel.com/dashboard](https://vercel.com/dashboard)
   - Click "Add New" → "Project"
   - Click "Import" next to your GitHub repository
   - Select the repository

3. **Configure Project**
   - Framework Preset: `Other`
   - Root Directory: `./` or `landing-page` (if in subdirectory)
   - Build Command: (leave empty)
   - Output Directory: (leave empty)
   - Install Command: `npm install`

4. **Deploy**
   - Click "Deploy"
   - Wait for build to complete (usually 1-2 minutes)
   - Your site is now live at `https://your-project.vercel.app`

#### Method 2: Vercel CLI (Advanced)

1. **Install Vercel CLI**
   ```bash
   npm install -g vercel
   ```

2. **Login to Vercel**
   ```bash
   vercel login
   ```

3. **Deploy to Preview**
   ```bash
   cd landing-page
   vercel
   ```

4. **Deploy to Production**
   ```bash
   vercel --prod
   ```

### Custom Domain Setup

1. **Add Domain in Vercel Dashboard**
   - Go to Project Settings → Domains
   - Click "Add"
   - Enter `brutallyhonest.io`
   - Click "Add"

2. **Configure DNS Records**
   
   **For Root Domain (brutallyhonest.io):**
   ```
   Type: A
   Name: @
   Value: 76.76.21.21
   TTL: 3600
   ```

   **For WWW Subdomain:**
   ```
   Type: CNAME
   Name: www
   Value: cname.vercel-dns.com
   TTL: 3600
   ```

   **Alternative (CNAME for root):**
   ```
   Type: CNAME
   Name: @
   Value: cname.vercel-dns.com
   TTL: 3600
   ```

3. **Wait for DNS Propagation**
   - Usually takes 5-30 minutes
   - Check status at [dnschecker.org](https://dnschecker.org)

4. **SSL Certificate**
   - Automatically issued by Vercel
   - No configuration needed
   - Active within a few minutes

### Environment Variables

If you need to add environment variables (for email services, etc.):

1. Go to Project Settings → Environment Variables
2. Add each variable:
   - `SENDGRID_API_KEY`
   - `MAILGUN_API_KEY`
   - etc.
3. Redeploy for changes to take effect

## 🌐 Alternative Deployment Options

### Deploy to Netlify

1. **Install Netlify CLI**
   ```bash
   npm install -g netlify-cli
   ```

2. **Create netlify.toml**
   ```toml
   [build]
     command = "npm install"
     publish = "public"
     functions = "netlify/functions"

   [[redirects]]
     from = "/*"
     to = "/index.html"
     status = 200
   ```

3. **Deploy**
   ```bash
   netlify deploy --prod
   ```

### Deploy to Railway

1. Go to [railway.app](https://railway.app)
2. Click "New Project" → "Deploy from GitHub repo"
3. Select your repository
4. Railway auto-detects Node.js and deploys
5. Add custom domain in project settings

### Deploy to Heroku

1. **Install Heroku CLI**
   ```bash
   npm install -g heroku
   ```

2. **Create Procfile**
   ```
   web: node server.js
   ```

3. **Deploy**
   ```bash
   heroku login
   heroku create brutallyhonest-landing
   git push heroku main
   heroku open
   ```

### Deploy to DigitalOcean App Platform

1. Go to [cloud.digitalocean.com/apps](https://cloud.digitalocean.com/apps)
2. Click "Create App"
3. Connect your GitHub repository
4. Configure:
   - Type: Web Service
   - Build Command: `npm install`
   - Run Command: `npm start`
5. Click "Next" and "Deploy"

## 🔧 Post-Deployment Checklist

- [ ] Test all pages and links
- [ ] Verify contact form works
- [ ] Check mobile responsiveness
- [ ] Test page load speed (Google PageSpeed Insights)
- [ ] Verify SSL certificate is active
- [ ] Test SEO with [search.google.com/test/mobile-friendly](https://search.google.com/test/mobile-friendly)
- [ ] Submit sitemap to Google Search Console
- [ ] Set up analytics (Google Analytics, Plausible, etc.)
- [ ] Test cross-browser compatibility
- [ ] Verify all CTAs work correctly
- [ ] Check email notifications (if configured)

## 📊 Monitoring & Analytics

### Google Search Console

1. Go to [search.google.com/search-console](https://search.google.com/search-console)
2. Add property for `brutallyhonest.io`
3. Verify ownership (DNS or HTML tag method)
4. Submit sitemap: `https://brutallyhonest.io/sitemap.xml`

### Google Analytics

Add to `/views/index.ejs` before `</head>`:

```html
<script async src="https://www.googletagmanager.com/gtag/js?id=G-XXXXXXXXXX"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'G-XXXXXXXXXX');
</script>
```

### Uptime Monitoring

Recommended services:
- [UptimeRobot](https://uptimerobot.com) (Free)
- [Pingdom](https://pingdom.com)
- [StatusCake](https://statuscake.com)

## 🐛 Troubleshooting Deployment

### Build Fails

**Error: Module not found**
```bash
# Clear node_modules and reinstall
rm -rf node_modules package-lock.json
npm install
```

**Error: Port already in use**
- Vercel automatically assigns ports, no need to configure

### DNS Issues

**Site not loading after DNS update**
- Wait 24-48 hours for full propagation
- Clear your local DNS cache:
  ```bash
  # macOS
  sudo dscacheutil -flushcache; sudo killall -HUP mDNSResponder
  
  # Windows
  ipconfig /flushdns
  
  # Linux
  sudo systemd-resolve --flush-caches
  ```

### SSL Certificate Issues

**Certificate not issued**
- Ensure DNS is properly configured
- Wait 24 hours for full propagation
- Contact Vercel support if issues persist

## 📞 Support

If you encounter issues:

1. Check [Vercel Documentation](https://vercel.com/docs)
2. Visit [Vercel Community](https://github.com/vercel/vercel/discussions)
3. Contact support: hello@brutallyhonest.io

## 🔄 Continuous Deployment

With Vercel connected to GitHub:

1. Make changes to your code
2. Commit and push to GitHub
   ```bash
   git add .
   git commit -m "Update landing page"
   git push origin main
   ```
3. Vercel automatically deploys changes
4. Preview deployments for pull requests
5. Production deployment on merge to main

## 🎯 Performance Optimization

After deployment, optimize:

1. **Compress Images**: Use [TinyPNG](https://tinypng.com)
2. **Enable Caching**: Already configured in `vercel.json`
3. **Minify Assets**: Automatically handled by Vercel
4. **Monitor Speed**: Use [PageSpeed Insights](https://pagespeed.web.dev)
5. **CDN**: Automatically enabled by Vercel

Target metrics:
- First Contentful Paint: < 1.8s
- Time to Interactive: < 3.8s
- Cumulative Layout Shift: < 0.1
- Largest Contentful Paint: < 2.5s

---

**Need help?** Contact hello@brutallyhonest.io

