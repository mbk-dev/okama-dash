// Tab on an open ticker-search combobox accepts the top (best-match) option.
//
// okama-dash issue #25. The searchable dmc.Select / dmc.MultiSelect pickers (Mantine
// comboboxes) select the highlighted option on Enter but ignore Tab, so a typed prefix
// is discarded when the user tabs out and they have to reach for Enter or the mouse.
// dash-mantine-components 2.7 exposes no "select on Tab" option, so a single
// document-level keydown listener handles every combobox at once: on Tab, if the focused
// element's listbox is open with at least one match, it clicks the top option (exactly as
// choosing it with the mouse — Mantine binds onClick to each option) and lets the default
// Tab move focus on. Living in assets/ means Dash serves it on every page, so it applies to
// every selector (Portfolio, EF, Compare, Benchmark, Macro) with no per-page wiring.

(function () {
    "use strict";

    // The top option of the open listbox for a Mantine combobox search input, or null
    // when this isn't such an input, the dropdown is closed/hidden, or there are no
    // matches (the "nothing found" note is not a [role=option]).
    function topOption(input) {
        if (!input || typeof input.getAttribute !== "function") return null;
        // A Mantine combobox input points at its listbox via aria-controls.
        var ddId = input.getAttribute("aria-controls");
        if (!ddId) return null;
        var dd = document.getElementById(ddId);
        if (!dd || dd.getClientRects().length === 0) return null; // closed / hidden
        var opt = dd.querySelector('[role="option"]');
        if (!opt) return null;
        // Scope to Mantine only: dcc.Dropdown (React-Select) and other widgets also use
        // aria-controls + role=option, but their options are not "mantine-…-option".
        var cls = opt.className || "";
        if (cls.indexOf("mantine-") === -1 || cls.indexOf("option") === -1) return null;
        return opt;
    }

    document.addEventListener(
        "keydown",
        function (e) {
            if (e.key !== "Tab" || e.shiftKey) return; // plain Tab only
            var input = e.target;
            var opt = topOption(input);
            if (!opt) return; // closed / no match / not a Mantine combobox -> normal Tab
            // Choose it exactly as a mouse click would; Mantine's onMouseDown keeps focus
            // on the input, onClick submits the option.
            opt.dispatchEvent(new MouseEvent("mousedown", { bubbles: true, cancelable: true }));
            opt.dispatchEvent(new MouseEvent("mouseup", { bubbles: true, cancelable: true }));
            opt.click();
            // Multi-ticker pickers (MultiSelect) keep the cursor in the search box so the
            // user can type the next ticker without re-focusing: cancel the focus move and
            // the dropdown stays open with the search cleared. A single Select holds one
            // value, so let the default Tab move focus on (e.g. ticker -> weight).
            if ((input.className || "").indexOf("MultiSelect") !== -1) {
                e.preventDefault();
                input.focus(); // keep the caret here even if the click briefly blurred it
            }
        },
        true // capture, so a combobox's own onKeyDown can't swallow the event first
    );
})();
