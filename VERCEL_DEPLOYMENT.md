# Deploying Your Telegram Bot to Vercel

This guide will walk you through deploying your Telegram character bot to Vercel.

## Prerequisites

1. A [Vercel](https://vercel.com) account
2. Your Telegram bot token from BotFather
3. Your Mistral AI API key
4. A PostgreSQL database (you can use [Neon](https://neon.tech), [Supabase](https://supabase.com), or any other PostgreSQL provider)

## Deployment Steps

### 1. Fork or Clone this Repository to GitHub

Make sure your code is on GitHub as Vercel will need to access it from there.

### 2. Connect Your GitHub Repository to Vercel

1. Log in to your Vercel account
2. Click "Add New..." → "Project"
3. Select your GitHub repository
4. Configure the project:
   - Framework Preset: Other
   - Root Directory: ./

### 3. Configure Environment Variables

Add the following environment variables to your Vercel project:

- `TELEGRAM_BOT_TOKEN`: Your Telegram bot token
- `MISTRAL_API_KEY`: Your Mistral AI API key
- `DATABASE_URL`: Your PostgreSQL connection string
- `SESSION_SECRET`: A random string for Flask session security

### 4. Deploy

1. Click "Deploy"
2. Wait for the deployment to complete
3. Vercel will provide you with a deployment URL (e.g., `your-project.vercel.app`)

### 5. Set Up Webhook for Your Telegram Bot

After deployment, you'll need to set up the webhook to connect your Telegram bot to your Vercel deployment:

1. Visit `https://your-project.vercel.app/api/set_webhook?url=https://your-project.vercel.app/api/webhook`
2. You should see a success message confirming that the webhook was set

### 6. Test Your Bot

Send a message to your Telegram bot to test if it responds properly.

## Troubleshooting

If your bot doesn't respond:

1. Check Vercel logs for any errors
2. Verify that all environment variables are set correctly
3. Make sure the webhook is set up properly
4. Ensure your PostgreSQL database is accessible from Vercel

## Notes on Serverless Deployment

Vercel uses a serverless architecture, which means:

- Your application doesn't run continuously, it spins up on demand
- There's a cold start time when the app hasn't been used recently
- It works best for webhook-based interactions rather than long-polling

For heavy usage, you might want to consider a different hosting solution like Koyeb or Railway that offers continuous runtime.
