// Initialize Typed.js for the typing animation on the home page
document.addEventListener('DOMContentLoaded', function () {
    if (document.getElementById('typed-text')) {
        var typed = new Typed('#typed-text', {
            strings: ['Connect. Learn. Grow.'],
            typeSpeed: 100,
            backSpeed: 50,
            loop: false,
            cursorChar: '|'
        });
    }

    // Initialize AOS for scroll animations
    AOS.init({
        duration: 800,
        easing: 'ease-in-out',
        once: true
    });

    // Initialize Swiper.js for the top mentors carousel
    if (document.querySelector('.swiper')) {
        var swiper = new Swiper('.swiper', {
            slidesPerView: 1,
            spaceBetween: 20,
            loop: true,
            pagination: {
                el: '.swiper-pagination',
                clickable: true,
            },
            navigation: {
                nextEl: '.swiper-button-next',
                prevEl: '.swiper-button-prev',
            },
            breakpoints: {
                768: {
                    slidesPerView: 2,
                    spaceBetween: 30,
                },
                992: {
                    slidesPerView: 3,
                    spaceBetween: 40,
                },
            },
        });
    }
});