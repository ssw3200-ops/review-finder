@echo off
chcp 65001 >nul
REM 한 번만 실행: 매일 10:00, 16:00 국내 수집 예약 (Windows 작업 스케줄러)
set RUN=%~dp0run_local.bat
schtasks /create /f /sc daily /st 10:00 /tn "review-finder 국내수집 10시" /tr "\"%RUN%\""
schtasks /create /f /sc daily /st 16:00 /tn "review-finder 국내수집 16시" /tr "\"%RUN%\""
echo 등록 완료. 확인: 작업 스케줄러 ^> 작업 스케줄러 라이브러리
pause
