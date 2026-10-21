// Mimic the onetrust style insert

window.addEventListener("load", (_) => {
    
    let style = document.querySelector("#onetrust-style");
    
    if (!style) {
        style = document.createElement("style");
        style.id = "onetrust-style";
        document.head.insertAdjacentElement("beforeend", style);
    }
    
    //style.innerHTML = "*, html, body { background-color: #000 !important; color: #fff !important; }"
})

// Fix the removed style tag

let __gStyles;

// Subscribe to the document$ to know that there was a site reload
// Restore the removed style from the global variable
window.document$.subscribe(function() {
    if (!__gStyles) return;
    if (document.head.querySelector("#onetrust-style")) return;
    document.head.insertAdjacentElement("beforeend", __gStyles);
})

// Subscribe to the location$ to know that the location change was invoked
// On first location change get the style (it's not removed yet) and assign it to the global variable
window.location$.subscribe(function() {
    let style = document.head.querySelector("#onetrust-style");
    if (!style) return;
    if (__gStyles) return;
    __gStyles = style;
})

// Page feedback — send ratings + optional text to Google Analytics 4
window.document$.subscribe(function() {
    var feedback = document.forms.feedback;
    if (!feedback) return;
    feedback.hidden = false;
    feedback.addEventListener("submit", function(ev) {
        ev.preventDefault();
        var page = document.location.pathname;
        var data = ev.submitter.getAttribute("data-md-value");

        // Send initial rating event to GA4
        if (typeof gtag === "function") {
            gtag("event", "feedback", {
                page_path: page,
                rating: data
            });
        }

        // Disable rating buttons
        feedback.firstElementChild.disabled = true;

        // Hide any default thank-you notes
        var notes = feedback.querySelectorAll(".md-feedback__note [data-md-value]");
        for (var i = 0; i < notes.length; i++) notes[i].hidden = true;

        // Show text feedback form
        var existing = feedback.querySelector(".feedback-text-form");
        if (existing) existing.remove();

        var textForm = document.createElement("div");
        textForm.className = "feedback-text-form";
        textForm.innerHTML =
            '<p class="feedback-text-prompt">Want to tell us more? <span class="feedback-optional">(optional)</span></p>' +
            '<textarea class="feedback-textarea" maxlength="500" rows="3" placeholder="What can we improve on this page?"></textarea>' +
            '<div class="feedback-text-actions">' +
                '<button type="button" class="feedback-submit md-button md-button--primary">Submit</button>' +
                '<button type="button" class="feedback-skip">Skip</button>' +
            '</div>';
        feedback.appendChild(textForm);

        var textarea = textForm.querySelector(".feedback-textarea");
        var submitBtn = textForm.querySelector(".feedback-submit");
        var skipBtn = textForm.querySelector(".feedback-skip");

        function showThanks() {
            textForm.innerHTML = '<p class="feedback-thanks">Thanks for your feedback!</p>';
        }

        submitBtn.addEventListener("click", function() {
            var text = textarea.value.trim();
            if (text && typeof gtag === "function") {
                gtag("event", "feedback_text", {
                    page_path: page,
                    rating: data,
                    comment: text.substring(0, 500)
                });
            }
            showThanks();
        });

        skipBtn.addEventListener("click", showThanks);
    });
})