// Auto-rescale the Y axis to the visible X window when the range slider zooms.
//
// Plotly's range slider only changes the X range; the Y axis stays at the range
// computed for the full series, so a zoomed window occupies a sliver of the
// vertical space (okama-dash issue #26). Plotly has no native "autorange Y to the
// visible X slice" config, so we attach a global `plotly_relayout` listener to
// every graph: on an X-range change we recompute the Y range over the points
// inside the window and relayout. Living in assets/ means Dash serves it on every
// page, so the fix is shared across all charts (macro, Compare/Benchmark, Portfolio,
// EF) with no per-page callback wiring.

(function () {
    "use strict";

    var Y_PAD_FRACTION = 0.05; // breathing room above/below the visible extremes

    // x values arrive as numbers (linear axes) or ISO date strings (date axes);
    // normalize both to a comparable number.
    function toNumber(v) {
        return typeof v === "number" ? v : new Date(v).getTime();
    }

    // Plotly >= 6 stores numeric trace data as a typed-array *spec* object
    // ({dtype, bdata, _inputArray}) rather than a plain Array, so tr.x / tr.y are
    // not always directly indexable (the spec object has no .length and obj[i] is
    // undefined). Normalize to something indexable: a plain Array, a typed array,
    // or the decoded `_inputArray`; return null for anything we can't read so the
    // caller skips the trace instead of misreading every point as out-of-window.
    function asArray(v) {
        if (v == null) return null;
        if (Array.isArray(v) || ArrayBuffer.isView(v)) return v;
        if (v._inputArray) return v._inputArray; // plotly typed-array spec
        return null;
    }

    // Min/max Y over every visible point whose X falls inside [lo, hi] on the
    // primary Y axis ('y'). Secondary axes (y2, …) keep their own autorange.
    function computeYRange(gd, x0, x1) {
        var lo = toNumber(x0);
        var hi = toNumber(x1);
        if (lo > hi) {
            var tmp = lo;
            lo = hi;
            hi = tmp;
        }
        var ymin = Infinity;
        var ymax = -Infinity;
        var sawBar = false;
        var data = gd.data || [];
        for (var i = 0; i < data.length; i++) {
            var tr = data[i];
            if (tr.visible === "legendonly" || tr.visible === false) continue;
            if (tr.yaxis && tr.yaxis !== "y") continue;
            var xs = asArray(tr.x);
            var ys = asArray(tr.y);
            if (!xs || !ys) continue;
            var n = Math.min(xs.length, ys.length);
            var contributed = false;
            for (var j = 0; j < n; j++) {
                var xv = toNumber(xs[j]);
                if (xv < lo || xv > hi) continue;
                var yv = ys[j];
                if (yv === null || yv === undefined || isNaN(yv)) continue;
                if (yv < ymin) ymin = yv;
                if (yv > ymax) ymax = yv;
                contributed = true;
            }
            if (contributed && tr.type === "bar") sawBar = true;
        }
        if (ymin === Infinity) return null; // no visible points in the window
        if (sawBar) {
            // Bars are read against a 0 baseline; never float them off it.
            if (ymin > 0) ymin = 0;
            if (ymax < 0) ymax = 0;
        }
        return [ymin, ymax];
    }

    function onRelayout(gd, ev) {
        if (gd._yRescaleBusy) return; // ignore the event our own relayout fires

        // X reset (double-click / "autoscale") -> hand the Y axis back to Plotly.
        if (ev["xaxis.autorange"] || ev["autosize"]) {
            gd._yRescaleBusy = true;
            window.Plotly.relayout(gd, { "yaxis.autorange": true }).then(function () {
                gd._yRescaleBusy = false;
            });
            return;
        }

        // Box-zoom (drag a rectangle) sets the Y range explicitly in the same
        // event; that's a deliberate Y selection, so leave it alone. The range
        // slider, by contrast, only ever changes X — which is what we react to.
        if ("yaxis.range[0]" in ev || ev["yaxis.range"]) return;

        var x0;
        var x1;
        if ("xaxis.range[0]" in ev) {
            x0 = ev["xaxis.range[0]"];
            x1 = ev["xaxis.range[1]"];
        } else if (ev["xaxis.range"]) {
            x0 = ev["xaxis.range"][0];
            x1 = ev["xaxis.range"][1];
        } else {
            return; // pure Y-axis or unrelated event -> nothing to do (no recursion)
        }

        var range = computeYRange(gd, x0, x1);
        if (!range) return;
        var span = range[1] - range[0];
        var pad = span * Y_PAD_FRACTION || Math.abs(range[1]) * Y_PAD_FRACTION || 1;
        gd._yRescaleBusy = true;
        window.Plotly.relayout(gd, { "yaxis.range": [range[0] - pad, range[1] + pad] }).then(
            function () {
                gd._yRescaleBusy = false;
            }
        );
    }

    // Plotly events are emitted on the graph div, not via DOM bubbling, so each
    // graph needs its own listener. New graphs appear as the user navigates pages
    // or submits forms; a MutationObserver wires up any we haven't seen yet.
    function attach(gd) {
        if (gd._yRescaleAttached || typeof gd.on !== "function") return;
        gd._yRescaleAttached = true;
        gd.on("plotly_relayout", function (ev) {
            onRelayout(gd, ev);
        });
    }

    function scan() {
        var graphs = document.querySelectorAll(".js-plotly-plot");
        for (var i = 0; i < graphs.length; i++) attach(graphs[i]);
    }

    function start() {
        scan();
        var observer = new MutationObserver(scan);
        observer.observe(document.body, { childList: true, subtree: true });
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", start);
    } else {
        start();
    }
})();
