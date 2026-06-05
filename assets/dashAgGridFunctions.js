// Custom functions for dash-ag-grid valueFormatter function strings.
// The dash-ag-grid function-string parser does not support inline guards like
// `typeof params.value === 'number'` — such expressions are silently rejected
// and the raw value is rendered. Real JS lives here instead (documented pattern:
// https://dash.plotly.com/dash-ag-grid/custom-functions-value-formatters).
var dagfuncs = (window.dashAgGridFunctions = window.dashAgGridFunctions || {});

// Percent with 2 decimals (d3 '.2%' equivalent): 0.0834 -> "8.34%".
// Non-numeric cells (dates, text) pass through unchanged.
dagfuncs.formatPercentGuarded = function (value) {
    if (typeof value !== "number" || isNaN(value)) {
        return value;
    }
    return (value * 100).toFixed(2) + "%";
};

// Fixed decimal with 2 digits (d3 '.2f' equivalent): 0.1234 -> "0.12".
dagfuncs.formatDecimalGuarded = function (value) {
    if (typeof value !== "number" || isNaN(value)) {
        return value;
    }
    return value.toFixed(2);
};

// Grouped integer (d3 ',.0f' equivalent): 13456.78 -> "13,457".
dagfuncs.formatGroupedIntGuarded = function (value) {
    if (typeof value !== "number" || isNaN(value)) {
        return value;
    }
    return Intl.NumberFormat("en-US", {maximumFractionDigits: 0}).format(value);
};
