@echo off
echo Starting multi-arena training...
echo.

set EVALUATIONS=200
set IT_PER_EVAL=400
set DISPLAY_MODE=2

echo.
echo ========================================
echo Training on Arena 0 (Empty)...
echo ========================================
python tetracomposibot.py config_multiarena_training 0 False %DISPLAY_MODE% %EVALUATIONS%
if %ERRORLEVEL% NEQ 0 (
    echo Error in Arena 0 training
    pause
    exit /b 1
)

echo.
echo ========================================
echo Training on Arena 1 (Classic)...
echo ========================================
python tetracomposibot.py config_multiarena_training 1 False %DISPLAY_MODE% %EVALUATIONS%
if %ERRORLEVEL% NEQ 0 (
    echo Error in Arena 1 training
    pause
    exit /b 1
)

echo.
echo ========================================
echo Training on Arena 2 (Lines)...
echo ========================================
python tetracomposibot.py config_multiarena_training 2 False %DISPLAY_MODE% %EVALUATIONS%
if %ERRORLEVEL% NEQ 0 (
    echo Error in Arena 2 training
    pause
    exit /b 1
)

echo.
echo ========================================
echo Training on Arena 3 (Vertical Limit)...
echo ========================================
python tetracomposibot.py config_multiarena_training 3 False %DISPLAY_MODE% %EVALUATIONS%
if %ERRORLEVEL% NEQ 0 (
    echo Error in Arena 3 training
    pause
    exit /b 1
)

echo.
echo ========================================
echo Training on Arena 4 (Maze)...
echo ========================================
python tetracomposibot.py config_multiarena_training 4 False %DISPLAY_MODE% %EVALUATIONS%
if %ERRORLEVEL% NEQ 0 (
    echo Error in Arena 4 training
    pause
    exit /b 1
)

echo.
echo ========================================
echo Training complete!
echo.
echo Results:
echo 1. Best genome: multiarena_best_genome.txt
echo 2. Training stats: multiarena_training_results.json
echo 3. CSV data: multiarena_training_stats.csv
echo.
echo To use the trained robot in Paint Wars:
echo 1. Copy multiarena_best_genome.txt to your project folder
echo 2. Use MultiArenaChampion class from robot_multiarena_trainer_v2.py
echo ========================================
pause