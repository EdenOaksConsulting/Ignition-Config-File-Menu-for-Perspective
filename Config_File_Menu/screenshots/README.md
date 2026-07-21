# Screenshots

Captures for the GitHub README and the Exchange listing.

The PNGs live here (~75–165 KB each). The GIF is 2.4 MB — acceptable once, but **re-cuts
should not be committed on top of it**, or every revision stays in clone history forever.
If it needs reshooting, upload the replacement to a GitHub issue or discussion and hotlink
that URL from the README instead.

## Current set

| File | Shows | Used in |
|------|-------|---------|
| `config-file-menu-hero.png` | Designer property editor with `contentSource` open in the string editor, beside the live session rendering that exact menu | Root README, above the fold; Exchange image #1 |
| `config-file-menu-expanded.png` | Menu four levels deep, icons at every level, selected item highlighted, full breadcrumb trail | Root README |
| `config-file-menu-settings.png` | **Settings → Tag → Menu** mid-generation with YAML output populated | Root README |
| `config-file-menu-themes.png` | The same Reports page in light and dark | Root README |
| `config-file-menu-overview.gif` | Dock motion — hamburger, expand, navigate, pin, push/cover, click-outside close | Root README (see size note) |

The hero is the exception to "capture in a live session": popping the `contentSource`
multiline editor open shows ~25 readable lines of YAML *and* the `configFileMenu` property
tree behind it, so one image answers both "what does the config look like" and "where does
it live". Everything else is a live Perspective session — the Settings tab especially, since
tag browsing can fail in Designer preview.

## Deliberately not captured

Do not "fix" these by adding them; they were dropped on purpose.

- **Standalone breadcrumb shot** — the trail is already visible in the hero, expanded, and
  settings captures. A dedicated one adds nothing.
- **Collapsed / responsive still** — the GIF shows the dock collapsing in motion, which is
  what the claim actually needs. A frozen narrow viewport reads as a broken layout.
- **Separate Designer session-props shot** — folded into the hero.
- **Diagnostics Dashboard** — bundled but adapted from
  [Exchange #98](https://inductiveautomation.com/exchange/98/overview). Leading with it
  would advertise someone else's work. If ever added, place it last and label it as bundled.

## Composing the hero

The YAML must match what the menu shows, item for item, so a viewer can trace
`label: Areas` to the "Areas" row and `icon: material/account_tree` to the icon beside it.
The current hero does this down to the selected leaf: the config ends on
`- label: Overview` under `Line 01`, and that is the highlighted row in the menu and the
last breadcrumb segment. A 60-line config beside a 5-item menu teaches nothing.

Keep the Designer window cropped so the title bar stays out of frame — that is where the
gateway and project names appear.

## Capture method

**Stills — Chrome DevTools, not the Snipping Tool.** `F12` → `Ctrl+Shift+P` → "Capture
screenshot". You get the exact viewport with no OS chrome, window borders, or cursor, and
identical dimensions across every shot. Set the viewport first with `Ctrl+Shift+M`:
1440×900 for desktop captures, 390×844 for the collapsed one. Set DPR to 2 for crisp text.

**Animation — ScreenToGif** (free, open source). Target ~960px wide, 10–15 fps, under 4 MB;
drop duplicate frames before exporting. One 12–20s clip covering hamburger open → expand a
nested section → navigate (breadcrumb updates) → pin → push/cover toggle → click-outside
close. That motion is the one thing stills cannot convey. GIF, not MP4 — GitHub markdown
embeds GIF inline but cannot embed MP4.

## Before publishing

Check every frame for leaks: gateway hostname, project name in the Designer title bar, tag
provider names, trial-license banner, IP address in the URL bar. Use `localhost`. The
Designer capture (#7) is the likeliest to expose an internal hostname.

Shoot light theme as the primary; it reads better against GitHub's default rendering.
