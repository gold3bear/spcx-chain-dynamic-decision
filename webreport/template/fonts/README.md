# Fonts

Rendering uses this CSS font stack: `"Noto Sans SC", "Microsoft YaHei", "PingFang SC", system-ui, sans-serif`.

On the Windows render machine, `Microsoft YaHei` is present, so Chinese renders without bundling.
For deterministic cross-platform output, drop `NotoSansSC-Regular.otf` (OFL, redistributable) into
this folder and uncomment the `@font-face` rule in `style.css`.
