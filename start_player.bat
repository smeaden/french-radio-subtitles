@echo off
echo Starting subtitle player server...
echo Open your browser to: http://localhost:8000/test_player.html
python -m http.server 8000
