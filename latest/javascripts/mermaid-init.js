// Initialize Mermaid diagrams
//
// `startOnLoad` is off and rendering is driven explicitly through `run()` with
// a `:not([data-processed])` selector, so a diagram is only ever rendered once.
// With `startOnLoad: true` plus a manual `contentLoaded()` call, a second pass
// can re-read an already-rendered container — whose text is now the SVG's
// labels rather than diagram source — and replace the diagram with Mermaid's
// "Syntax error in text" graphic.
document$.subscribe(function() {
    if (typeof mermaid === 'undefined') return;

    mermaid.initialize({
        startOnLoad: false,
        theme: 'default',
        securityLevel: 'loose',
        fontFamily: 'Roboto, sans-serif'
    });

    var pending = document.querySelectorAll('.mermaid:not([data-processed])');
    if (!pending.length) return;

    mermaid.run({ nodes: pending }).catch(function(error) {
        console.error('Mermaid render failed:', error);
    });
});
