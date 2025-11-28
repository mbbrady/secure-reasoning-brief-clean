#!/bin/bash
# One-time test to verify cron works - schedules a test run for 2 minutes from now

CURRENT_CRON=$(crontab -l 2>/dev/null)

# Get the time 2 minutes from now
MINUTE=$(date -d '+2 minutes' '+%M')
HOUR=$(date -d '+2 minutes' '+%H')

echo "Current time: $(date '+%H:%M')"
echo "Scheduling test cron run at: ${HOUR}:${MINUTE}"

# Add test cron job (will run once then we can remove it)
TEST_CRON="$MINUTE $HOUR * * * /home/mike/project/rkl-consolidated/secure-reasoning-brief/scripts/cron_pipeline_wrapper.sh # TEST-RUN-DELETE-AFTER"

# Add to existing crontab
echo "$CURRENT_CRON" | grep -v "TEST-RUN-DELETE-AFTER" > /tmp/test_crontab.txt
echo "$TEST_CRON" >> /tmp/test_crontab.txt
crontab /tmp/test_crontab.txt

echo ""
echo "✅ Test cron job scheduled!"
echo ""
echo "Current crontab:"
crontab -l | grep "rkl-phase0\|TEST-RUN"
echo ""
echo "Monitor with:"
echo "  watch -n 5 'ls -lht /home/mike/project/rkl-consolidated/secure-reasoning-brief/logs/cron/ | head -3'"
echo ""
echo "After the test completes (check logs at ${HOUR}:${MINUTE}), remove test job with:"
echo "  crontab -l | grep -v TEST-RUN-DELETE-AFTER | crontab -"
