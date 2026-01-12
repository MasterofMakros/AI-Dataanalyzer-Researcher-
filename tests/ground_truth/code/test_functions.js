// JavaScript Test File 1: Functions
// Expected: Extract function definitions

function calculateTax(income, rate) {
    return income * rate;
}

const formatCurrency = (amount) => {
    return new Intl.NumberFormat('de-DE', {
        style: 'currency',
        currency: 'EUR'
    }).format(amount);
};

async function fetchData(url) {
    const response = await fetch(url);
    return response.json();
}

console.log(formatCurrency(1234.56));
