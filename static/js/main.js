// Mobile navigation toggle
document.addEventListener('DOMContentLoaded', function () {
  const menuBtn = document.getElementById('mobile-menu-btn');
  const mobileMenu = document.getElementById('mobile-menu');
  if (menuBtn && mobileMenu) {
    menuBtn.addEventListener('click', function () {
      mobileMenu.classList.toggle('open');
    });
  }

  initCarousels();
  initBookingCalculator();
  initUserMenu();
  initCardNavigation();
});

// Avatar dropdown menu (desktop) - toggle open/closed, close on outside click
function initUserMenu() {
  const btn = document.getElementById('user-menu-btn');
  const menu = document.getElementById('user-menu');
  if (!btn || !menu) return;

  btn.addEventListener('click', function (e) {
    e.stopPropagation();
    menu.classList.toggle('hidden');
  });

  document.addEventListener('click', function (e) {
    if (!menu.classList.contains('hidden') && !menu.contains(e.target) && e.target !== btn) {
      menu.classList.add('hidden');
    }
  });
}

// Makes an entire vehicle card clickable (navigates to its detail page), while still
// letting carousel arrows/dots and any explicit buttons/links inside the card work
// normally without triggering the card-level navigation.
function initCardNavigation() {
  const cards = document.querySelectorAll('[data-card-href]');
  cards.forEach(function (card) {
    card.style.cursor = 'pointer';
    card.addEventListener('click', function (e) {
      if (e.target.closest('[data-no-navigate]')) return;
      window.location.href = card.dataset.cardHref;
    });
  });
}

// Image carousel with next/prev arrows, used on homepage cards and category/detail pages
function initCarousels() {
  const carousels = document.querySelectorAll('[data-carousel]');
  carousels.forEach(function (carousel) {
    const track = carousel.querySelector('.carousel-track');
    const slides = carousel.querySelectorAll('.carousel-slide');
    const dotsWrap = carousel.querySelector('.carousel-dots');
    const prevBtn = carousel.querySelector('.carousel-prev');
    const nextBtn = carousel.querySelector('.carousel-next');
    let index = 0;

    if (!track || slides.length === 0) return;

    function goTo(i) {
      index = (i + slides.length) % slides.length;
      track.style.transform = 'translateX(-' + (index * 100) + '%)';
      if (dotsWrap) {
        dotsWrap.querySelectorAll('.carousel-dot').forEach(function (dot, di) {
          dot.classList.toggle('active', di === index);
        });
      }
    }

    if (prevBtn) prevBtn.addEventListener('click', function (e) {
      e.preventDefault();
      goTo(index - 1);
    });
    if (nextBtn) nextBtn.addEventListener('click', function (e) {
      e.preventDefault();
      goTo(index + 1);
    });

    if (dotsWrap) {
      dotsWrap.querySelectorAll('.carousel-dot').forEach(function (dot, di) {
        dot.addEventListener('click', function () { goTo(di); });
      });
    }

    goTo(0);
  });
}

// Booking price calculator: price/day * days, adjusted by destination extra charge
function initBookingCalculator() {
  const form = document.getElementById('booking-form');
  if (!form) return;

  const pricePerDay = parseFloat(form.dataset.pricePerDay || '0');
  const driverCost = parseFloat(form.dataset.driverCost || '0');
  const startInput = document.getElementById('id_start_date');
  const endInput = document.getElementById('id_end_date');
  const driverRadios = document.querySelectorAll('input[name="with_driver"]');
  const summaryBox = document.getElementById('price-summary');

  const daysOut = document.getElementById('summary-days');
  const rateOut = document.getElementById('summary-rate');
  const totalOut = document.getElementById('summary-total');
  const advanceOut = document.getElementById('summary-advance');
  const ADVANCE_RATE = 0.05;

  // Prevent picking any date before today
  const todayStr = new Date().toISOString().split('T')[0];
  if (startInput) startInput.min = todayStr;
  if (endInput) endInput.min = todayStr;

  function getWithDriver() {
    const checked = document.querySelector('input[name="with_driver"]:checked');
    return checked && checked.value === '1';
  }

  function recalc() {
    if (!startInput.value || !endInput.value) {
      if (summaryBox) summaryBox.classList.add('hidden');
      return;
    }
    const start = new Date(startInput.value);
    const end = new Date(endInput.value);
    const days = Math.round((end - start) / (1000 * 60 * 60 * 24));

    if (days <= 0) {
      if (summaryBox) summaryBox.classList.add('hidden');
      return;
    }

    const withDriver = getWithDriver();
    const effectiveDailyRate = pricePerDay + (withDriver ? driverCost : 0);
    const total = effectiveDailyRate * days;
    const advance = total * ADVANCE_RATE;

    if (summaryBox) {
      summaryBox.classList.remove('hidden');
      daysOut.textContent = days;
      rateOut.textContent = 'NPR ' + effectiveDailyRate.toLocaleString() + (withDriver ? ' (incl. driver)' : ' (self-drive)');
      totalOut.textContent = 'NPR ' + total.toLocaleString();
      advanceOut.textContent = 'NPR ' + advance.toLocaleString(undefined, {maximumFractionDigits: 2});
    }
  }

  [startInput, endInput].forEach(function (el) {
    if (el) el.addEventListener('change', recalc);
  });
  driverRadios.forEach(function (radio) {
    radio.addEventListener('change', recalc);
  });

  if (startInput && endInput) {
    startInput.addEventListener('change', function () {
      endInput.min = startInput.value > todayStr ? startInput.value : todayStr;
    });
  }

  recalc();
}