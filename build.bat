@echo off
echo 🔧 Activando entorno virtual...
call venv\Scripts\activate

pyinstaller ^
  --onefile ^
  --console ^
  --name "ClanDashboard" ^
  --add-data "session_data.json;." ^
  --collect-all streamlit ^
  --collect-all altair ^
  --collect-all pandas ^
  --hidden-import pkg_resources.py2_warn ^
  --hidden-import pandas._libs.tslibs.timedeltas ^
  --hidden-import pandas._libs.tslibs.timestamps ^
  app.py
  
echo ✅ Listo. El ejecutable está en la carpeta /dist
pause
