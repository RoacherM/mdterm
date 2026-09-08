# Search log

A shell pipeline full of `|`, wider than any pane:

```
grep -rn "presetBusy|selectPreset|stagedPreset|makeDefaultPreset|removePreset|startSession" \
  plugins/app/src plugins/app/tests | grep -v src/client/presets.ts
→ no matches
```
