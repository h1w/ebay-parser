# ebay-parser

Настроить cron

1. `sudo crontab -e`
2. `* * * * * /usr/bin/docker restart ebay-parser`
3. `* * * * * sleep 30 && /usr/bin/docker restart ebay-parser`
