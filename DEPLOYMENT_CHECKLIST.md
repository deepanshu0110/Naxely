---
name: Pre-Launch Deployment Checklist
about: Verify all deployment steps before going live
title: 'Pre-Launch Deployment Checklist'
labels: ['deployment']
---

## Pre-Launch Deployment Checklist

### Environment Variables
- [ ] All 8 env vars set on Render.com
- [ ] All 4 env vars set on Vercel

### Database & Auth
- [ ] Database migrations run on production Supabase
- [ ] Run 000_create_auth_trigger.sql in Supabase SQL editor before any users sign up
- [ ] Auth trigger (`000_create_auth_trigger.sql`) confirmed active

### Storage
- [ ] Storage buckets created + policies set

### Auth & OAuth
- [ ] Google OAuth redirect URI set to production URL

### Payments
- [ ] Dodo Payments webhook pointing to production URL

### Domains & SSL
- [ ] Custom domain `databrief.io` connected to Vercel
- [ ] Custom domain `api.databrief.io` connected to Render
- [ ] SSL certificates active on both domains

### Monitoring
- [ ] Uptime Robot monitors active
- [ ] Sentry project created + DSN set

### Email
- [ ] Resend domain verified + email templates created

### CI/CD
- [ ] CI/CD pipelines tested with a dummy commit

### Health & Smoke Tests
- [ ] /health endpoint returning 200
- [ ] End-to-end test: signup → upload → generate → download PDF
- [ ] Payment test: upgrade to Pro → verify tier changes → cancel
