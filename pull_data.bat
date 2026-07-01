@echo off
cd /d "D:\Khushi\my trade"
echo [%date% %time%] Starting Git pull... >> sync_log.txt
git pull origin main >> sync_log.txt 2>&1
echo [%date% %time%] Git pull completed. >> sync_log.txt
exit



