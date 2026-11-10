# A new look for Code-Theory

An editorial GitHub README with off-white paper, deep ink, lime, lavender and peach. No featured repositories or project showcases on the front page: the focus is Daksh, his interests and live contribution activity.

## Publish it

Copy `README.md`, `.github/workflows/update-cards.yml`, `scripts/render_readme_cards.py`, `data/contributions.json` and all files in `cards/` to the root of your **Code-Theory/Code-Theory** profile repository. Commit to your default branch.

Open GitHub **Actions → Refresh profile SVG cards → Run workflow** once. It fetches your *real* contribution calendar, rerenders the monthly chart and yearly heatmap, and commits the updated JSON and cards. After that, the Action runs daily.

If the workflow cannot push, in your repo go to **Settings → Actions → General → Workflow permissions** and select **Read and write permissions**. A built-in GitHub Actions token is used by default. A `STATS_TOKEN` secret is optional, not required in standard setups. Never put tokens in SVGs or JSON.

**Important:** The currently committed `data/contributions.json` is deliberately empty. It does not fake stats. `data/demo.json` is synthetic preview data and is never read by the scheduled workflow.

## Test the design locally

```bash
python -m pip install 'fonttools[woff]>=4.55,<6'
# Ubuntu / Debian:
sudo apt-get install fonts-inter fonts-liberation

python scripts/render_readme_cards.py
STATIC=1 python scripts/render_readme_cards.py --data data/demo.json --out preview/cards
```

`STATIC=1` generates the final animation frame so you can capture screenshots. Rendering SVGs directly (with all animations) uses the default command. The preview SVGs are kept separate from the cards GitHub serves.

### Customization

Edit the palette, headline, three social tiles, and interests card at the beginning of `scripts/render_readme_cards.py`. The social tile destinations live in `README.md`, because links only work when wrapping the `<img>` in an `<a>` tag. There is no portfolio URL, and none is required.

For a portrait, set `PORTRAIT_FILE=/path/to/portrait.png` when rendering. The portrait becomes a **base64 embedded data image** inside the hero, not an external request. Without it, the hero shows the custom systems illustration.

The script uses `pyftsubset` to subset locally installed Inter and Liberation Mono fonts into **embedded base64 WOFF** data URIs. It does not publish or distribute font files separately. SVG animation uses inline CSS keyframes and a decorative SMIL element. Animations are disabled visually with `prefers-reduced-motion`; SVG cards contain no JavaScript, remote CSS, or remote images.

## Files

- `scripts/render_readme_cards.py` — the single Python generator and GitHub GraphQL fetcher
- `data/contributions.json` — live contribution calendar, refreshed daily
- `data/demo.json` — clearly labeled fake data, for local previews only
- `cards/` — seven embeddable animated SVGs
- `README.md` — responsive, linked profile layout using image tags
- `.github/workflows/update-cards.yml` — daily fetch, render, commit
