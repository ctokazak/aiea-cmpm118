on run argv
  set inF to POSIX file (item 1 of argv)
  set outF to POSIX file (item 2 of argv)
  tell application "Keynote"
    set d to open inF
    export d to outF as PDF
    close d saving no
  end tell
end run
