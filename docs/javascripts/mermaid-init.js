// Initialize Mermaid diagrams
document$.subscribe(function() {
    if (typeof mermaid !== 'undefined') {
        mermaid.initialize({
            startOnLoad: true,
            theme: 'default',
            securityLevel: 'loose',
            fontFamily: 'Roboto, sans-serif'
        });
        
        // Re-render Mermaid diagrams on page navigation
        mermaid.contentLoaded();
    }
});
