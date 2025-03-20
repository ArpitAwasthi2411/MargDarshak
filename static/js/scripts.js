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

    // Initialize Swiper.js for carousels
    if (document.querySelector('.swiper')) {
        document.querySelectorAll('.swiper').forEach(function (swiperContainer) {
            var swiper = new Swiper(swiperContainer, {
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
        });
    }

    // Toggle edit profile form visibility
    const toggleButtons = document.querySelectorAll('.toggle-edit-form');
    toggleButtons.forEach(button => {
        button.addEventListener('click', function () {
            const form = this.nextElementSibling;
            form.classList.toggle('active');
            this.textContent = form.classList.contains('active') ? 'Cancel' : 'Edit Profile';
        });
    });
});