pyinstaller --onefile --distpath dist/ src/lbal_run_summarizer.py \
  --noconsole \
  --icon "icon.ico" \
  --add-data "img:img" \
  --add-data "icon.ico:." \
  --add-data "fonts:fonts" \
  --add-data "symbol_data.json:."