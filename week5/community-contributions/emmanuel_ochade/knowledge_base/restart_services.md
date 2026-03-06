# Restarting Services

## API service

To restart the main API (e.g. after a config change or memory issue):

**Linux / systemd:**
- `sudo systemctl restart api-service`
- `sudo systemctl status api-service`

**Docker:**
- `docker compose restart api`
- `docker compose ps`

**Kubernetes:**
- `kubectl rollout restart deployment/api -n production`
- `kubectl rollout status deployment/api -n production`

## Worker / queue

The background worker processes jobs from the queue. Restart only during low-traffic windows.

**systemd:** `sudo systemctl restart worker-service`

**Docker:** `docker compose restart worker`

Allow 1-2 minutes for in-flight jobs to drain. Check the queue depth in the dashboard before restarting.

## Database

Do not restart the database without coordination. If required: announce in ops, get approval, put the app in maintenance mode, restart the DB, run health checks, then bring the app back.
