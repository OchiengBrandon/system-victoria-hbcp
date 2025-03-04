// auth.js

$(document).ready(function() {
    // Example: Show password toggle functionality
    $('#togglePassword').on('click', function() {
        const passwordField = $('#password');
        const type = passwordField.attr('type') === 'password' ? 'text' : 'password';
        passwordField.attr('type', type);
        $(this).text(type === 'password' ? 'Show Password' : 'Hide Password');
    });

    // Example: Form submission feedback
    $('form').on('submit', function() {
        // Show a loading spinner or disable the button
        const submitButton = $(this).find('button[type="submit"]');
        submitButton.prop('disabled', true).text('Submitting...');
    });
});