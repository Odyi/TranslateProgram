document.addEventListener('DOMContentLoaded', () => {
    const orderForm = document.getElementById('order-form');

    orderForm.addEventListener('submit', async (e) => {
        e.preventDefault(); // Hindre at skjemaet sender data på vanlig måte

        const description = document.getElementById('description').value;

        // Send bestillingen til serveren
        const response = await fetch('/order', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ description }),
        });

        const result = await response.json();

        if (response.ok) {
            // Omdiriger til takkesiden
            window.location.href = "/thank_you";
        } else {
            alert('Noe gikk galt: ' + result.message);
        }
    });
});