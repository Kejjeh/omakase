"""Filtering, the empty state, and surviving a failed chart library.

Three defects found by driving the released dashboards in a real browser:

* A blocked Chart.js CDN made `new Chart(...)` throw inside applyFilters(),
  which aborted the call before updateTable() ran. The stat cards rendered
  and the restaurant table stayed empty - a dependency outage dressed up as
  an empty filter.
* Price bounds were read with `|| 0` / `|| 9999`, so a Max Price of 0 meant
  "no maximum" and widened the results instead of emptying them; and a row
  with no price was compared as if it cost $0, so it passed every maximum.
* Filters that matched nothing left a bare table under a full header row,
  with nothing to say the filters were responsible.

These run the shipped JavaScript under node against a stub of the handful of
DOM calls it makes. See jsharness.py for why.
"""

import json

import pytest
from jsharness import DASHBOARDS, extract, run_node, source


def run_apply_filters(cuisine: str, rows: list[dict], values: dict) -> list[str]:
    """Return the names surviving applyFilters() with `values` in the boxes."""
    src = source(cuisine)
    script = f"""
const ALL_DATA = {json.dumps(rows)};
let filtered = [];
const VALUES = {json.dumps(values)};
const document = {{ getElementById: (id) => ({{ value: VALUES[id] ?? '' }}) }};
function updateStats() {{}}
function updateTable() {{}}
function updateChart() {{}}
{extract(src, "function priceBound(")}
{extract(src, "function applyFilters()")}
applyFilters();
console.log(JSON.stringify(filtered.map(r => r.name)));
"""
    return run_node(script)


def run_update_table(cuisine: str, rows: list[dict], header_count: int = 12) -> dict:
    """Return {'html': tbody innerHTML} after updateTable() runs over `rows`."""
    src = source(cuisine)
    script = f"""
const filtered = {json.dumps(rows)};
let sortCol = 'composite_rating';
let sortAsc = false;
const out = {{}};
const tbody = {{ set innerHTML(v) {{ out.html = String(v); }} }};
const document = {{
  querySelector: (sel) => sel === '#data-table tbody' ? tbody : null,
  querySelectorAll: (sel) => ({{ length: {header_count} }}),
}};
{extract(src, "function escAttr(")}
{extract(src, "function exclusionTags(")}
{extract(src, "function updateTable()")}
updateTable();
console.log(JSON.stringify(out));
"""
    return run_node(script)


def run_update_chart(cuisine: str, *, chart_defined: bool, draw_throws: bool) -> dict:
    """Return what updateChart() does to the chart container."""
    src = source(cuisine)
    script = f"""
const out = {{ threw: false, html: null }};
const box = {{ dataset: {{}}, set innerHTML(v) {{ out.html = String(v); }} }};
const document = {{ querySelector: (sel) => sel === '.chart-container' ? box : null }};
const console_error = () => {{}};
const console = {{ error: console_error }};
{'const Chart = class {};' if chart_defined else ''}
function drawChart() {{ {'throw new Error("render failed");' if draw_throws else 'out.drew = true;'} }}
{extract(src, "function chartUnavailable(")}
{extract(src, "function updateChart()")}
try {{ updateChart(); }} catch (e) {{ out.threw = String(e); }}
process.stdout.write(JSON.stringify(out));
"""
    return run_node(script)


def priced(name, price, rating=4.2, n_sources=2):
    return {
        "name": name,
        "min_price": price,
        "composite_rating": rating,
        "value_score": 10.0,
        "n_sources": n_sources,
        "rating_percentile": 50,
    }


def unpriced(name, rating=4.2, n_sources=2):
    # ROKI and Tokyo Bar in the omakase data: a real restaurant whose price we
    # never captured. `price_str` reads "Unlisted"; min_price is null.
    row = priced(name, None, rating, n_sources)
    return row


# --- price bounds ------------------------------------------------------------


@pytest.mark.parametrize("cuisine", DASHBOARDS)
def test_blank_price_boxes_bound_nothing(cuisine):
    names = run_apply_filters(
        cuisine, [priced("Cheap", 20), priced("Dear", 400), unpriced("Unlisted")], {}
    )
    assert names == ["Cheap", "Dear", "Unlisted"]


@pytest.mark.parametrize("cuisine", DASHBOARDS)
def test_max_price_of_zero_means_zero_not_unlimited(cuisine):
    """The reported defect: typing 0 widened the results instead of emptying them."""
    names = run_apply_filters(
        cuisine,
        [priced("Cheap", 20), priced("Dear", 400)],
        {"f-price-max": "0"},
    )
    assert names == []


@pytest.mark.parametrize("cuisine", DASHBOARDS)
def test_unknown_price_does_not_pass_a_maximum(cuisine):
    """An unknown price is not a free one."""
    names = run_apply_filters(
        cuisine,
        [priced("Known Cheap", 20), unpriced("Price Unlisted")],
        {"f-price-max": "50"},
    )
    assert names == ["Known Cheap"]


@pytest.mark.parametrize("cuisine", DASHBOARDS)
def test_unknown_price_does_not_pass_a_minimum(cuisine):
    names = run_apply_filters(
        cuisine,
        [priced("Known Dear", 300), unpriced("Price Unlisted")],
        {"f-price-min": "100"},
    )
    assert names == ["Known Dear"]


@pytest.mark.parametrize("cuisine", DASHBOARDS)
def test_a_minimum_of_zero_is_still_a_bound(cuisine):
    """0 is a number the user typed, not an empty box."""
    names = run_apply_filters(
        cuisine,
        [priced("Known", 20), unpriced("Unlisted")],
        {"f-price-min": "0"},
    )
    assert names == ["Known"]


@pytest.mark.parametrize("cuisine", DASHBOARDS)
def test_price_range_keeps_only_what_is_inside_it(cuisine):
    names = run_apply_filters(
        cuisine,
        [priced("Under", 20), priced("Inside", 80), priced("Over", 400)],
        {"f-price-min": "50", "f-price-max": "100"},
    )
    assert names == ["Inside"]


# --- the empty state ---------------------------------------------------------


@pytest.mark.parametrize("cuisine", DASHBOARDS)
def test_no_matches_says_so(cuisine):
    out = run_update_table(cuisine, [])
    assert "No restaurants match these filters" in out["html"]


@pytest.mark.parametrize("cuisine", DASHBOARDS)
def test_empty_message_spans_the_whole_table(cuisine):
    out = run_update_table(cuisine, [], header_count=13)
    assert 'colspan="13"' in out["html"]


@pytest.mark.parametrize("cuisine", DASHBOARDS)
def test_rows_still_render_when_there_are_some(cuisine):
    out = run_update_table(cuisine, [priced("Sushi Somewhere", 90)])
    assert "Sushi Somewhere" in out["html"]
    assert "No restaurants match" not in out["html"]


# --- a chart that will not load ----------------------------------------------


@pytest.mark.parametrize("cuisine", DASHBOARDS)
def test_missing_chart_library_does_not_throw(cuisine):
    """Chart.js comes from a CDN; it does not always arrive."""
    out = run_update_chart(cuisine, chart_defined=False, draw_throws=False)
    assert out["threw"] is False
    assert "Chart.js" in out["html"]
    assert "listed below" in out["html"]


@pytest.mark.parametrize("cuisine", DASHBOARDS)
def test_a_failing_chart_render_does_not_throw(cuisine):
    out = run_update_chart(cuisine, chart_defined=True, draw_throws=True)
    assert out["threw"] is False
    assert "unavailable" in out["html"]


@pytest.mark.parametrize("cuisine", DASHBOARDS)
def test_a_working_chart_is_left_alone(cuisine):
    out = run_update_chart(cuisine, chart_defined=True, draw_throws=False)
    assert out["threw"] is False
    assert out["html"] is None
    assert out["drew"] is True


@pytest.mark.parametrize("cuisine", DASHBOARDS)
def test_the_table_is_rendered_before_the_chart(cuisine):
    """The ordering that keeps a chart failure from emptying the report."""
    src = source(cuisine)
    script = f"""
const ALL_DATA = {json.dumps([priced("Still Listed", 60)])};
let filtered = [];
const order = [];
const document = {{ getElementById: () => ({{ value: '' }}) }};
function updateStats() {{ order.push('stats'); }}
function updateTable() {{ order.push('table'); }}
function updateChart() {{ order.push('chart'); throw new Error('Chart is not defined'); }}
{extract(src, "function priceBound(")}
{extract(src, "function applyFilters()")}
try {{ applyFilters(); }} catch (e) {{ order.push('threw'); }}
console.log(JSON.stringify({{ order, rows: filtered.map(r => r.name) }}));
"""
    out = run_node(script)
    assert out["order"].index("table") < out["order"].index("chart")
    assert out["rows"] == ["Still Listed"]


# --- wiring that only a browser can really exercise --------------------------


@pytest.mark.parametrize("cuisine", DASHBOARDS)
def test_column_headers_are_keyboard_operable(cuisine):
    """Sorting was mouse-only: no header could take focus, so a keyboard user
    was stuck with one ordering. Browser evidence is in the handoff; this guards
    the wiring against deletion."""
    src = source(cuisine)
    block = extract(src, "document.querySelectorAll('#data-table th').forEach")
    assert "th.tabIndex = 0" in block
    assert "keydown" in block
    assert "aria-sort" in block
    assert "'Enter'" in block and "' '" in block


@pytest.mark.parametrize("cuisine", DASHBOARDS)
def test_filter_controls_can_shrink_below_their_content(cuisine):
    """A <select> is as wide as its longest <option>, which pushed the whole
    page into horizontal scroll on a phone."""
    src = source(cuisine)
    assert "min-width: 0;" in extract(src, ".filter-group {")
