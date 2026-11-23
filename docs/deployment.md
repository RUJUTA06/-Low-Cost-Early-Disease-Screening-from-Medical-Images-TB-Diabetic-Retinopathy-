# Protected Supabase + Render deployment

This deployment uses Supabase PostgreSQL for pseudonymous case metadata and Render for one Docker web service serving both the React UI and FastAPI API. Uploaded images stay in request memory and are discarded. The app is gated by one shared HTTP Basic credential; anyone with that credential can see and manage all case metadata in the project. This is a small private research demo, not multi-user clinical software.

## Before you deploy

- Do not upload real patient data or identifiable medical images. This project has no clinical validation, no authentication per person, no role separation, and no regulated-data compliance review.
- Choose free plans only if their current limits and service-sleep behavior meet your needs. Do not add a payment method or select a paid resource unless you have reviewed its price.
- The app contains no datasets, trained checkpoints, or validated performance results. Both workflows abstain until configured. Keep `TB_CHECKPOINT` and `DR_CHECKPOINT` unset.
- Use a unique shared access password of at least 20 characters. Store it only in Render's secret environment settings; don't commit it or paste it into chat.

## Supabase database

1. Create a Supabase project in your account and choose a region close to Singapore (the Render blueprint's default region).
2. Save the database password in a password manager.
3. In the Supabase project, select **Connect**, then choose the **Session pooler** connection string. Copy it exactly; don't construct the pooler hostname yourself.
4. Ensure the connection uses TLS (`sslmode=require`). Change the SQLAlchemy URL driver prefix to `postgresql+psycopg://` if the copied URI starts with `postgresql://` or `postgres://`.
5. Keep the database password and URI private. Do not use the Supabase service-role key in this project. The API creates the tables on first startup.

## Render deployment

1. Connect the GitHub repository `RUJUTA06/-Low-Cost-Early-Disease-Screening-from-Medical-Images-TB-Diabetic-Retinopathy-` to Render.
2. Create a **Blueprint** from the repository and select `render.yaml`. Review that the service is on the Free plan before applying it.
3. When prompted, set `DATABASE_URL` to the Supabase session-pooler URL; set `ACCESS_USERNAME` to a non-identifying operator name; set `ACCESS_PASSWORD` to your unique 20+ character secret.
4. Apply the Blueprint and wait for the Docker build and health check at `/api/health` to pass.
5. Open the generated `onrender.com` service URL. Sign in with the shared access username/password. The service sleeps on some free plans and the first request after sleep may take time.
6. Check `https://<your-service>.onrender.com/api/health` for service status. This health endpoint is public for Render health checks; all other `/api/*` routes require the shared credential.

## Operations

- Rotate the shared password in Render if access needs to be revoked.
- Supabase contains the cases, review notes, audit metadata, and evaluation records. Apply a retention/deletion policy before using the service with any sensitive data.
- Render auto-deploys commits pushed to the connected branch. Changes to the protected access settings are saved as Render secrets, never in Git.
- Avoid creating multiple independent copies of production data. Backup/restore and deletion workflows should be reviewed before any meaningful use.
- Free plan availability, sleeping, quotas, and provider terms may change; confirm current details in the provider dashboards before creating resources.
