# AMB site renderer

Pages are rendered from data; nothing is hand-edited per edition.

**Flagship:** write `data/fx/<YYYY-MM-DD>.json` (schema `amb-fx-site/1`; copy the latest file as the template), then run `python3 tools/render.py`.
Required per Nigeria currency (USD, GBP, EUR): `parallel_buy_low/high`, `parallel_sell_low/high`, `official_selling_rate`, `official_rate_date`, `official_basis` (`CBN selling rate (NFEM)` or `Derived: CBN NFEM x ECB reference cross`), `premium_pct`; for derived rates also `official_inputs` (text) and `cbn_check` `{rate,date,pct}`. Also `markets` (name -> `symbol`, `asof`, `rates` USD/GBP/EUR), `edition_type`, optional `label_suffix`, `correction_note`, `markets_note`.

**Early Look:** write `data/fx/early-<YYYY-MM-DD>.json` (schema `amb-fx-early/1`): same Nigeria fields (parallel fields may be omitted per currency if not sourced) and `markets`. It is shown above the Flagship until that day's Flagship is published.

The renderer FAILS (nothing is written for the failing step; do not publish) if: premium does not recompute from the ranges and the CBN selling rate, a range is wider than max(N20, 1.5% of midpoint), buy midpoint exceeds sell midpoint, a derived rate is >0.3% from the CBN's own row, a market is incomplete, or any parallel-provider name appears in a data file or rendered output.

It regenerates: `data/fx/latest.json`, `data/fx/series.csv`, `data/fx/index.json`, and the `<!--AMB:...-->` regions of `index.html`, `fx.html`, `archive.html`, `data.html`.

## Money & Rates page
Source of truth: `data/money-rates.json` (schema `amb-money-rates/1`): per country `policy`, `inflation`, `bills` (basis `discount`|`interest`|`yield`, auction date, `tenors` with `rate` and `prev`), `deposits` (dated rows). Set `as_of` to the refresh date. Run `python3 tools/render_money.py` to regenerate the board, bars, takeaway, country sections and freshness table in `money-rates.html`. The homepage and Money & Rates calculators read the same JSON in the browser. The renderer fails on: dates after `as_of`, a missing 91/182/364-day tenor, rates outside 0–60%, a bill move above 3 points without corroboration, or any provider name. A country whose official data cannot be confirmed is set to `"bills": null` and the page shows "Re-verifying" instead of numbers.
