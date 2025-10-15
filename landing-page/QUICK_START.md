# 🚀 Quick Start Guide - BrutallyHonest.io Landing Page

Get your landing page running in under 5 minutes!

## ⚡ Super Quick Start

```bash
cd landing-page
npm install
npm start
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

## 📋 What You Get

✅ **Professional Landing Page** with OpenAI-inspired design  
✅ **Conversion Optimized** with strategic CTAs and contact form  
✅ **SEO Ready** with meta tags, Schema.org markup, and sitemap  
✅ **Fully Responsive** mobile-first design  
✅ **Vercel Ready** one-click deployment  
✅ **Tokenized Theme** easy to customize with CSS variables  

## 🎯 Key Sections

1. **Hero Section** - Powerful headline with dual CTAs
2. **Features** - 6 core features with icons
3. **Use Cases** - 6 business applications
4. **How It Works** - 3-step process
5. **CTA Section** - Conversion-focused call to action
6. **Contact Form** - With callback request option

## 🎨 Customization Basics

### Change Colors

Edit `public/theme.css`:

```css
:root {
  --color-primary: #10a37f;  /* Main brand color */
  --color-accent: #ff6b6b;   /* Accent color */
}
```

### Update Content

Edit `views/index.ejs` - all content is clearly structured with comments.

### Modify Contact Form Behavior

Edit `server.js` - `/api/contact` endpoint (line ~51)

## 🚀 Deploy to Vercel (3 Steps)

### Option 1: One-Click Deploy

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/yourusername/brutallyhonest-landing)

### Option 2: CLI Deploy

```bash
npm install -g vercel
cd landing-page
vercel --prod
```

### Option 3: Dashboard Deploy

1. Push to GitHub
2. Go to [vercel.com](https://vercel.com)
3. Import repository
4. Deploy!

## 🌐 Custom Domain Setup

After deploying to Vercel:

1. **Add Domain**
   - Project Settings → Domains
   - Add `brutallyhonest.io`

2. **Update DNS** (at your domain registrar)
   ```
   Type: A
   Name: @
   Value: 76.76.21.21
   ```

3. **Wait for SSL**
   - Automatic HTTPS
   - Active in 5-10 minutes

## 📊 Add Analytics

### Google Analytics

Add to `views/index.ejs` (before `</head>`):

```html
<script async src="https://www.googletagmanager.com/gtag/js?id=GA_MEASUREMENT_ID"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'GA_MEASUREMENT_ID');
</script>
```

### Plausible (Privacy-Friendly)

```html
<script defer data-domain="brutallyhonest.io" src="https://plausible.io/js/script.js"></script>
```

## 📧 Email Integration

To receive contact form submissions via email:

### Using SendGrid

1. Get API key from [sendgrid.com](https://sendgrid.com)
2. Install package:
   ```bash
   npm install @sendgrid/mail
   ```
3. Update `server.js`:
   ```javascript
   const sgMail = require('@sendgrid/mail');
   sgMail.setApiKey(process.env.SENDGRID_API_KEY);
   
   app.post('/api/contact', async (req, res) => {
     const msg = {
       to: 'hello@brutallyhonest.io',
       from: 'noreply@brutallyhonest.io',
       subject: 'New Contact Form Submission',
       text: `Name: ${req.body.name}\nEmail: ${req.body.email}...`,
     };
     await sgMail.send(msg);
     res.json({ success: true });
   });
   ```

## 🔧 Common Tasks

### Run in Development Mode
```bash
npm run dev  # Auto-restarts on file changes
```

### Test Production Build
```bash
NODE_ENV=production npm start
```

### Check for Security Issues
```bash
npm audit
npm audit fix
```

## 📱 Mobile Testing

Test responsiveness:
- Chrome DevTools (F12 → Toggle Device Toolbar)
- [responsively.app](https://responsively.app) (free tool)
- Real devices

## ✅ Pre-Launch Checklist

Before going live:

- [ ] Update all content in `views/index.ejs`
- [ ] Add your logo to `public/favicon.svg`
- [ ] Configure contact form email
- [ ] Test all links and CTAs
- [ ] Verify mobile responsiveness
- [ ] Set up analytics
- [ ] Test form submission
- [ ] Check page load speed
- [ ] Verify SEO tags
- [ ] SSL certificate active
- [ ] Custom domain configured

## 🎯 Performance Targets

Your site should achieve:
- ✅ **Load Time**: < 2 seconds
- ✅ **PageSpeed Score**: > 90
- ✅ **Mobile Friendly**: Yes
- ✅ **SEO Score**: > 95

Test at:
- [PageSpeed Insights](https://pagespeed.web.dev)
- [GTmetrix](https://gtmetrix.com)

## 📞 Need Help?

- 📖 Full README: `README.md`
- 🚀 Deployment Guide: `DEPLOYMENT.md`
- 💬 Email: hello@brutallyhonest.io

## 🎉 You're Ready!

Your landing page is production-ready with:
- Modern, professional design
- Full SEO optimization
- Conversion-focused layout
- Mobile responsiveness
- Security best practices
- One-click deployment

**Now deploy it and start converting visitors!** 🚀

