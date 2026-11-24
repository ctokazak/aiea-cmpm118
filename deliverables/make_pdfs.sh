#!/bin/sh
# Build the PDF deliverables: write-ups and diary (pandoc + headless Chrome), slides (Keynote).
# Usage: cd deliverables && ./make_pdfs.sh
set -e
cd "$(dirname "$0")"
CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
TMP=$(mktemp -d)

pdf() {
  pandoc "$1" -s --embed-resources --resource-path=.:../task6_other_logics --css pdf_style.css \
    --metadata title-meta="$(basename "$2" .pdf)" -o "$TMP/page.html"
  "$CHROME" --headless=new --disable-gpu --no-pdf-header-footer --print-to-pdf="$PWD/$2" "file://$TMP/page.html" 2>/dev/null
  echo "wrote $2"
}

for t in 2 3 4 5 6; do pdf "task${t}_writeup.md" "task${t}_writeup.pdf"; done
pdf research_diary.md research_diary.pdf
pdf ../task6_other_logics/TUTORIAL.md task6_datalog_tutorial.pdf

for deck in task5_logic_lm_slides task6_datalog_slides; do
  osascript keynote_to_pdf.applescript "$PWD/$deck.pptx" "$PWD/$deck.pdf"
  echo "wrote $deck.pdf"
done
rm -rf "$TMP"
