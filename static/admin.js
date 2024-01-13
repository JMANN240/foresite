const inputs = document.querySelectorAll('input');


const setBackgroundToValue = (input) => {
	const hexColorRegex = new RegExp('^#[a-zA-Z0-9]{6}$', 'g');
	if (hexColorRegex.test(input.value)) {
		input.style.backgroundColor = input.value;
		input.style.color = whiteOrBlack(input.value);
	}
}

const whiteOrBlack = (hexColor) => {
	const r = parseInt(hexColor.slice(1, 3), 16);
	const g = parseInt(hexColor.slice(3, 5), 16);
	const b = parseInt(hexColor.slice(5, 7), 16);
	return (r * 0.299 + g * 0.587 + b * 0.114) > 186 ? '#000000' : '#FFFFFF';
}

inputs.forEach((input) => {
	setBackgroundToValue(input);

	input.addEventListener('input', () => {
		setBackgroundToValue(input);
	});
});