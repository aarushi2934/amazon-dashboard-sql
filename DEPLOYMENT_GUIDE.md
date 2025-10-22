# Amazon Dashboard Deployment Guide

Your dashboard is currently running locally. Here are multiple ways to deploy it so others can access it:

## Option 1: Streamlit Community Cloud (Recommended - FREE)

**Easiest and most popular option for Streamlit apps**

### Steps:
1. **Create a GitHub account** (if you don't have one): https://github.com/signup

2. **Create a new GitHub repository:**
   - Go to https://github.com/new
   - Name it: `amazon-dashboard-sql`
   - Make it **Public**
   - Click "Create repository"

3. **Push your code to GitHub:**
   ```bash
   cd /Users/aarushisharma/Desktop/amazon_dashboard_sql
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/amazon-dashboard-sql.git
   git push -u origin main
   ```

4. **Deploy to Streamlit Cloud:**
   - Go to https://share.streamlit.io/
   - Sign in with your GitHub account
   - Click "New app"
   - Select your repository: `amazon-dashboard-sql`
   - Main file path: `app.py`
   - Click "Deploy"

5. **Your dashboard will be live** at: `https://YOUR_USERNAME-amazon-dashboard-sql.streamlit.app`

**Pros:**
- ✅ Completely FREE
- ✅ Easy setup (takes 5-10 minutes)
- ✅ Auto-updates when you push to GitHub
- ✅ Built-in secrets management
- ✅ Custom domain support (with paid plan)

---

## Option 2: Hugging Face Spaces (FREE)

**Good alternative to Streamlit Cloud**

### Steps:
1. **Create account:** https://huggingface.co/join

2. **Create a new Space:**
   - Go to https://huggingface.co/new-space
   - Name: `amazon-dashboard`
   - SDK: Select **Streamlit**
   - Make it Public
   - Click "Create Space"

3. **Upload your files:**
   - Upload `app.py`
   - Upload `requirements.txt`
   - The database will be created automatically when you click the seed button

4. **Your app will be live** at: `https://huggingface.co/spaces/YOUR_USERNAME/amazon-dashboard`

**Pros:**
- ✅ FREE
- ✅ Simple file upload interface
- ✅ Good for quick prototypes
- ✅ ML-focused community

---

## Option 3: Heroku (FREE tier available)

### Steps:
1. **Install Heroku CLI:**
   ```bash
   brew install heroku/brew/heroku
   ```

2. **Create these files:**

   **Procfile:**
   ```
   web: streamlit run app.py --server.port=$PORT --server.address=0.0.0.0
   ```

   **runtime.txt:**
   ```
   python-3.11.9
   ```

3. **Deploy:**
   ```bash
   heroku login
   heroku create amazon-dashboard-sql
   git push heroku main
   ```

**Pros:**
- ✅ Professional deployment platform
- ✅ Custom domains
- ⚠️ FREE tier has limitations (app sleeps after 30 min of inactivity)

---

## Option 4: Railway (FREE tier available)

### Steps:
1. **Go to:** https://railway.app/
2. **Sign in with GitHub**
3. **Click "New Project"** → Deploy from GitHub repo
4. **Select your repository**
5. **Add environment variables if needed**
6. **Deploy**

**Pros:**
- ✅ Very simple setup
- ✅ Generous FREE tier
- ✅ Auto-deploys from GitHub

---

## Option 5: Render (FREE tier available)

### Steps:
1. **Go to:** https://render.com/
2. **Sign up** and create new Web Service
3. **Connect your GitHub repository**
4. **Configure:**
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `streamlit run app.py --server.port=$PORT --server.address=0.0.0.0`
5. **Deploy**

**Pros:**
- ✅ FREE tier available
- ✅ Auto SSL certificates
- ✅ Easy setup

---

## Option 6: Run on Your Own Server (VPS)

**If you have your own server (AWS, DigitalOcean, etc.)**

### Steps:
1. **SSH into your server:**
   ```bash
   ssh user@your-server-ip
   ```

2. **Install Python and dependencies:**
   ```bash
   sudo apt update
   sudo apt install python3.11 python3-pip
   ```

3. **Clone/upload your code:**
   ```bash
   cd /var/www
   git clone https://github.com/YOUR_USERNAME/amazon-dashboard-sql.git
   cd amazon-dashboard-sql
   ```

4. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

5. **Run with systemd or screen:**
   ```bash
   screen -S dashboard
   streamlit run app.py --server.port=8501
   # Press Ctrl+A then D to detach
   ```

6. **Set up reverse proxy with Nginx** (optional for custom domain)

**Pros:**
- ✅ Full control
- ✅ Can handle high traffic
- ⚠️ Requires server management skills

---

## Recommendation for Your Use Case:

**🎯 Best Choice: Streamlit Community Cloud**

Since you're already using Streamlit, the Streamlit Community Cloud is the easiest and best option. It's:
- Free
- Zero configuration needed
- Handles all server management
- Perfect for dashboards like yours

### Quick Start with Streamlit Cloud:
1. Create GitHub account
2. Push your code to GitHub (5 minutes)
3. Deploy on Streamlit Cloud (2 minutes)
4. Share the live URL with anyone!

---

## Important Notes:

### Before Deploying:
- The `amazon.db` file will be created when users click "Seed / Reseed DB"
- All deployments include the seed functionality
- No sensitive data is in your code, so public deployment is safe

### After Deploying:
- Share the URL with your team/stakeholders
- The dashboard will work exactly like on localhost
- Users can filter, explore, and export data
- Updates to your GitHub repo will auto-deploy

Need help with any specific deployment option? Let me know!
