# PhotoPrism Automation with Cron

This document provides examples for automating PhotoPrism tasks using cron jobs, focusing particularly on BRAINS neural network analysis and maintenance tasks.

## BRAINS Automation

BRAINS provides advanced neural network analysis for your photos. To automate these processes, you can set up cron jobs that run at optimal times.

### Daily Analysis of New Photos

This cron job runs the BRAINS analysis workflow every day at 3:00 AM when system usage is typically low:

```bash
0 3 * * * cd /path/to/photoprism && ./scripts/brains-workflow.sh --mode analyze --cron >> /var/log/photoprism/brains-cron.log 2>&1
```

### Weekly Model Updates

Keep your BRAINS models up-to-date with this weekly update job that runs every Sunday at 4:00 AM:

```bash
0 4 * * 0 cd /path/to/photoprism && ./scripts/brains-workflow.sh --mode update --cron >> /var/log/photoprism/brains-cron.log 2>&1
```

### Monthly Collection Curation

This job automatically organizes your photos into AI-curated collections based on BRAINS analysis results:

```bash
0 5 1 * * cd /path/to/photoprism && ./scripts/brains-workflow.sh --mode curate --cron >> /var/log/photoprism/brains-cron.log 2>&1
```

### Complete BRAINS Workflow

For a comprehensive approach, this job runs the full BRAINS workflow (update models, analyze photos, curate collections) once a week:

```bash
0 2 * * 6 cd /path/to/photoprism && ./scripts/brains-workflow.sh --mode full --cron >> /var/log/photoprism/brains-cron.log 2>&1
```

## General PhotoPrism Maintenance

### Index New Photos

Automatically index your photos daily:

```bash
0 1 * * * cd /path/to/photoprism && ./photoprism index >> /var/log/photoprism/index-cron.log 2>&1
```

### Clean Up Orphaned Files

Run the cleanup command weekly to optimize storage:

```bash
0 2 * * 0 cd /path/to/photoprism && ./photoprism cleanup >> /var/log/photoprism/cleanup-cron.log 2>&1
```

### Backup Settings

Create regular backups of your settings and database:

```bash
0 0 * * 0 cd /path/to/photoprism && ./photoprism backup >> /var/log/photoprism/backup-cron.log 2>&1
```

## System Resource Considerations

The included `--cron` flag in the BRAINS workflow script ensures that analysis only runs when:

1. System load is below a specified threshold (default: 3.0)
2. The time is within the "quiet hours" window (default: 1:00 AM - 5:00 AM)

This prevents the CPU-intensive BRAINS analysis from affecting system performance during peak usage times.

## Setting Up Cron Jobs

To add these jobs to your crontab:

1. Open your crontab file:

   ```bash
   crontab -e
   ```

2. Add the desired job entries from the examples above

3. Save and exit the editor

4. Verify that your cron jobs are properly set:

   ```bash
   crontab -l
   ```

Remember to adjust the paths to match your PhotoPrism installation directory.
