const champAnimation = document.querySelector('.champ-animation');

setInterval(() => {
    const colors = ['#bb86fc', '#03dac6', '#ff0266', '#ffd700', '#3700b3'];
    const randomColor = colors[Math.floor(Math.random() * colors.length)];
    champAnimation.style.color = randomColor;
}, 1000);
