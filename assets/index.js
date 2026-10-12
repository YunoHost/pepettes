window.stripe = Stripe(document.getElementById('public_key').value);

// Proof of Work Captcha
async function solvePoWChallenge(token, challenge_pow, nb_worker, start) {
return new Promise((resolve, reject) => {
    let urls = [];
    let workers = [];
    const terminate = () => {
	for (let worker of workers) worker.terminate();
	for (let url of urls) URL.revokeObjectURL(url);
    };
    for (let i = 0; i < nb_worker; i++) {
	// FIXME put this code in a file ?
	const blob = new Blob([
	  `const sha256 = async (text) => {
		const msgUint8 = new TextEncoder().encode(text);
		const hashBuffer = await crypto.subtle.digest("SHA-256", msgUint8);
		return new Uint8Array(hashBuffer).toHex();
	    };
	    addEventListener("message", async (event) => {
		const {token, challenge_pow, nb_worker, i, start} = event.data;
		for(var k=i + start; k<10 ** 10; k += nb_worker) {
		    computedHash = await sha256(token + k);
		    if (challenge_pow == computedHash) {
			postMessage(k);
			break;
		    }
		}
	    });`
	], { type: "application/javascript", });
	const url = URL.createObjectURL(blob);
	const worker = new Worker(url);
	urls.push(url);
	workers.push(worker);
	worker.onmessage = (e) => {
	    terminate();
	    resolve(e.data);
	};
	worker.postMessage({token, challenge_pow, nb_worker, i, start});
    }
});
}

async function solveAllPoWChallenges(btn, token, challenge_pows) {
if (!challenge_pows)
    return [];
challenge_pows = challenge_pows.split("|");
let answers = [];
let answer = 0;
for (let challenge_pow of challenge_pows) {
    answer = await solvePoWChallenge(token, challenge_pow, 5, answer)
    answers.push(answer);
    btn.style.background = "linear-gradient(to right, #5394f2, #5394f2 "+ (answers.length * 5) +"%, #0d6efd "+ (answers.length * 5) +"%, #0d6efd)";
}
return answers;
}



// When the form is submitted...
var submitBtn = document.querySelector('#submit');
submitBtn.addEventListener('click', function (evt) {
  var quantity = parseInt(document.getElementById('quantity').value);
  var currency = document.getElementById('currency').value;
  var frequency = document.getElementById('frequency').value;
  fetch('/challenge', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
        body: JSON.stringify({
          quantity: quantity,
          currency: currency,
          frequency: frequency,
        }),
  }).then(function (challenge_result) {
    return challenge_result.json();
  }).then(function (challenge_data) {
    submitBtn.classList.add("loading");
    submitBtn.style.background = "linear-gradient(to right, #5394f2, #5394f2 2%, #0d6efd 2%, #0d6efd)";
    powPromise = solveAllPoWChallenges(submitBtn, challenge_data['token'], challenge_data['pow']);

    powPromise.then(function (powAnswers) {
      // Create the checkout session.
      fetch('/create-checkout-session', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          token: challenge_data['token'],
          proof_of_work: powAnswers.join('|'),
          quantity: quantity,
          currency: currency,
          frequency: frequency,
        }),
      }).then(function (result) {
        submitBtn.classList.add("remove");
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
  });
});



