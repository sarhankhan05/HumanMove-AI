@echo off
echo Starting Hadoop...
call start-all.cmd

echo.
echo Waiting a moment for NameNode and DataNodes to warm up...
timeout /t 10 /nobreak

echo.
echo Creating input directory in HDFS...
hdfs dfs -mkdir -p /chess/input

echo.
echo Uploading generated PGN chunks to HDFS. This may take a bit depending on total size...
hdfs dfs -put -f "file-path"\*.pgn /chess/input/

echo.
echo Listing HDFS contents to verify:
hdfs dfs -ls /chess/input/

echo.
echo Upload complete!
