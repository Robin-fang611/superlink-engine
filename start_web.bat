@echo off
echo Starting SuperLink Web Console...
echo Access at http://localhost:8501 or http://[Your-IP]:8501
streamlit run app.py --server.address 0.0.0.0 --server.port 8501
pause
