
// This script is injected into the browser to record user actions.
// It communicates back to the Python application by calling a callback function
// provided by Selenium's `execute_async_script`.

const callback = arguments[0];

// Helper function to create a unique CSS selector for a given element.
function getSelector(element) {
    if (!element || !element.tagName) {
        return '';
    }

    // Start with the tag name
    let selector = element.tagName.toLowerCase();

    // Add ID if it exists
    if (element.id) {
        selector += '#' + element.id;
        // ID is unique, so we can stop here
        return selector;
    }

    // Add classes if they exist
    if (element.className) {
        const classes = element.className.trim().split(/\s+/).join('.');
        if (classes) {
            selector += '.' + classes;
        }
    }

    // To make it more robust, you could traverse up the DOM,
    // but for now, this is a good starting point.
    return selector;
}

// Listen for all click events on the page.
document.addEventListener('click', function(event) {
    const selector = getSelector(event.target);
    const action = {
        type: 'click',
        selector: selector
    };
    // Send the recorded action back to the Python script.
    callback(action);
}, true); // Use 'capture' phase to ensure we get the event.

// Listen for changes in input fields, textareas, and select dropdowns.
document.addEventListener('change', function(event) {
    const selector = getSelector(event.target);
    const action = {
        type: 'input',
        selector: selector,
        value: event.target.value
    };
    // Send the recorded action back to the Python script.
    callback(action);
}, true);

console.log('Recorder script injected and listening for actions.');
