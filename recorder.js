
// This script is injected into the browser to record user actions.
// It communicates back to the Python application by calling a callback function
// provided by Selenium's `execute_async_script`.
// The Python script will set `window.isAsserting` before executing this.

const callback = arguments[0];

// Helper function to create a unique CSS selector for a given element.
function getSelector(element) {
    if (!element || !element.tagName) {
        return '';
    }
    if (element.id) {
        return `#${element.id}`;
    }
    let path = [];
    while (element.parentElement) {
        let selector = element.tagName.toLowerCase();
        const siblings = Array.from(element.parentElement.children);
        const sameTagSiblings = siblings.filter(e => e.tagName === element.tagName);
        if (sameTagSiblings.length > 1) {
            const index = sameTagSiblings.indexOf(element);
            selector += `:nth-of-type(${index + 1})`;
        }
        path.unshift(selector);
        element = element.parentElement;
        // Stop at body or a unique enough parent
        if (element.tagName.toLowerCase() === 'body') break;
    }
    return path.join(' > ');
}


// Listen for all click events on the page.
document.addEventListener('click', function(event) {
    const selector = getSelector(event.target);
    let action;

    if (window.isAsserting) {
        // DO NOT prevent default action. The user should be able to interact with the page
        // normally, while also capturing an assertion.
        
        const capturedText = event.target.innerText;
        action = {
            type: 'assert_text',
            selector: selector,
            value: capturedText
        };
        console.log(`Assertion captured: Element '${selector}' should have text '${capturedText}'`);
        // Send the recorded action back to the Python script.
        callback(action);

    } else {
        // Normal recording behavior
        action = {
            type: 'click',
            selector: selector
        };
        // Send the recorded action back to the Python script.
        callback(action);
    }
}, true); // Use 'capture' phase to ensure we get the event.

// Listen for changes in input fields, textareas, and select dropdowns.
document.addEventListener('change', function(event) {
    // We don't want to record 'change' events in assertion mode.
    if (window.isAsserting) {
        return;
    }
    const selector = getSelector(event.target);
    const action = {
        type: 'input',
        selector: selector,
        value: event.target.value
    };
    // Send the recorded action back to the Python script.
    callback(action);
}, true);

console.log('Recorder script injected. Assertion mode is:', window.isAsserting ? 'ON' : 'OFF');
