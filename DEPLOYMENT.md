# Deployment Guide: Multi-Agent AI Customer Support Assistant

This guide covers deploying the backend to Render and the frontend to GitHub Pages.

## Task 2 — Deploy Backend to Render

### Prerequisites
- A GitHub account.
- A free account on [Render](https://render.com).
- A cloud PostgreSQL database (you can use Render's free PostgreSQL or [Supabase](https://supabase.com)).

### Step-by-Step Instructions

1. **Create an account** at [render.com](https://render.com).
2. **Connect your GitHub repository** to Render from the Render dashboard.
3. **Create a New Web Service**:
   - Click "New" > "Web Service".
   - Select your connected GitHub repository.
   - **Name**: `techmart-support-ai`
   - **Environment**: `Python`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
   - Select the **Free** instance type.
4. **Set Environment Variables**:
   Under the "Environment" section, add the following variables:
   - `DATABASE_URL`: The connection string provided by Render PostgreSQL or Supabase.
   - `SECRET_KEY`: A strong, random string (e.g., generated via `openssl rand -hex 32`).
   - `GROQ_API_KEY`: Your API key from Groq.
   - `GROQ_MODEL`: `llama-3.1-8b-instant`
   - `EMBEDDING_MODEL`: `sentence-transformers/all-MiniLM-L6-v2`
   - `ALLOWED_ORIGINS`: `["https://yourusername.github.io"]` (Replace with your actual GitHub pages URL).
5. **Get Free PostgreSQL**:
   - **Render**: Click "New" > "PostgreSQL", name it, select Free tier, and copy the `Internal Database URL`.
   - **Supabase**: Create a new project, go to Database Settings > Connection String > URI, and copy it. Remember to append `?sslmode=require`.
6. **Run `build_index.py` (One-off Job)**:
   - On Render, your backend might automatically run the index builder if you implemented the auto-build fallback in `main.py` at startup.
   - Alternatively, go to the **Shell** tab of your deployed Web Service in Render and run:
     `python -m backend.rag.build_index`
7. **Verify Deployment**:
   - Once the deploy finishes, access `https://techmart-support-ai.onrender.com/health` in your browser.
   - You should see `{"status": "healthy", ...}`.

---

## Task 3 — Deploy Frontend to GitHub Pages

### Step-by-Step Instructions

1. **Update API URLs**:
   Before deploying, you must tell your frontend to talk to your live Render backend instead of `localhost`.
   - Create a new file `frontend/js/config.js`:
     ```javascript
     const API_BASE_URL = "https://techmart-support-ai.onrender.com";
     ```
   - Update `frontend/js/auth.js` and `frontend/js/chat.js` to remove the hardcoded `http://localhost:8000` and use `API_BASE_URL` instead.
     *(Note: To allow testing locally vs prod easily, you can include this file in your HTML using a `<script src="js/config.js">` tag.)*

2. **Push to GitHub**:
   - Commit your frontend changes:
     ```bash
     git add frontend/
     git commit -m "Configure frontend for production API"
     git push origin main
     ```

3. **Enable GitHub Pages**:
   - Navigate to your repository on GitHub.
   - Go to **Settings** > **Pages**.
   - Under **Build and deployment**, set the **Source** to `Deploy from a branch`.
   - Under **Branch**, select `main` (or your default branch) and select the `/frontend` (or root if you moved the files) folder. If GitHub Pages only allows `/root` or `/docs`, you might need to move your `frontend` files to the repository root or configure a GitHub Action to deploy the `frontend` folder.
   
4. **Access your App**:
   - Within a few minutes, your site will be live at:
     `https://yourusername.github.io/customer-support-ai/` (or similar depending on your repo structure).
