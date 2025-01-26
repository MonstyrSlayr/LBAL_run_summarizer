if [[ "${ matrix.os }" == "macos-latest" ]]; then
  pyinstaller --onefile --noconsole --icon "icon.icns" \
    --distpath dist/ src/lbal_run_summarizer.py \
    --add-data "img:img" \
    --add-data "fonts:fonts" \
    --add-data "symbol_data.json:."
else
  pyinstaller --onefile --noconsole --icon "icon.ico" \
    --distpath dist/ src/lbal_run_summarizer.py \
    --add-data "img:img" \
    --add-data "fonts:fonts" \
    --add-data "symbol_data.json:."
fi