window.stripe = Stripe(document.getElementById('public_key').value);

// When the form is submitted...
var submitBtn = document.querySelector('#submit');
submitBtn.addEventListener('click', function (evt) {
  var quantity = parseInt(document.getElementById('quantity').value);
  var currency = document.getElementById('currency').value;
  var frequency = document.getElementById('frequency').value;
  var csrf = document.getElementById('csrf').value;

  // Create the checkout session.
  fetch('/create-checkout-session', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      user_csrf: csrf,
      quantity: quantity,
      currency: currency,
      frequency: frequency
    }),
  }).then(function (result) {
    return result.json();
  }).then(function (data) {
    // Redirect to Checkout. with the ID of the
    // CheckoutSession created on the server.
    stripe.redirectToCheckout({
      sessionId: data.sessionId,
    })
    .then(function(result) {
      // If redirection fails, display an error to the customer.
      if (result.error) {
        var displayError = document.getElementById('error-message');
        displayError.textContent = result.error.message;
      }
    });
  });
});

