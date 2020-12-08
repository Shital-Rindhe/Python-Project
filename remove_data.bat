@echo off
echo Clearing Data
set execution_path=D:\common\execution\
set db_id=%1
echo %execution_path%%db_id%
RD /S /Q "%execution_path%%db_id%"
echo removed directory %execution_path%%db_id%

echo %ERRORLEVEL%
exit %ERRORLEVEL%
