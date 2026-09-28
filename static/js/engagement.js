function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === (name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

function showToast(message) {
  let toast = document.getElementById('engagementToast');
  if (!toast) {
    toast = document.createElement('div');
    toast.id = 'engagementToast';
    toast.className = 'fixed bottom-6 left-1/2 z-50 -translate-x-1/2 rounded-xl border border-white/10 bg-nv-800 px-4 py-2.5 text-sm font-semibold text-nv-100 shadow-[0_8px_30px_rgba(0,0,0,0.5)] opacity-0 pointer-events-none transition-opacity duration-300';
    toast.setAttribute('role', 'status');
    document.body.appendChild(toast);
  }
  toast.textContent = message;
  toast.classList.remove('opacity-0');
  clearTimeout(showToast.timer);
  showToast.timer = setTimeout(() => toast.classList.add('opacity-0'), 2500);
}

function handleLoginRequired(data) {
  if (data && data.login_required) {
    const next = encodeURIComponent(window.location.pathname + window.location.search);
    window.location = '/accounts/login/?next=' + next;
    return true;
  }
  return false;
}

/* ---------- Rating stars ---------- */
document.querySelectorAll('.js-rating').forEach((widget) => {
  const stars = Array.from(widget.querySelectorAll('.rating-star'));
  const textEl = widget.querySelector('.rating-text');
  const productId = widget.dataset.product;
  const avg = parseFloat(widget.dataset.avg || '0');
  const count = parseInt(widget.dataset.count || '0', 10);
  let userRating = parseInt(widget.dataset.user || '0', 10) || 0;

  function paint(level) {
    stars.forEach((s, i) => s.classList.toggle('text-gold-400', i < level));
    textEl.textContent = userRating
      ? `You: ${userRating}/5`
      : avg > 0
        ? `${avg.toFixed(1)} (${count || 0})`
        : count > 0 ? `${count} rating${count > 1 ? 's' : ''}` : '';
  }

  stars.forEach((s, i) => {
    s.addEventListener('mouseenter', () => stars.forEach((x, j) => x.classList.toggle('text-gold-400', j <= i)));
    s.addEventListener('mouseleave', () => paint(userRating || Math.round(avg)));
    s.addEventListener('click', () => {
      const value = i + 1;
      fetch(`/product/${productId}/rate/`, {
        method: 'POST',
        headers: {
          'X-CSRFToken': getCookie('csrftoken'),
          'X-Requested-With': 'XMLHttpRequest',
        },
        body: new URLSearchParams({ value }),
      })
        .then((r) => r.json().catch(() => ({ ok: false })))
        .then((data) => {
          if (handleLoginRequired(data)) return;
          if (!data.ok) {
            showToast(data.error || 'Could not save rating.');
            return;
          }
          userRating = data.user_rating;
          paint(userRating);
          showToast(`Thanks! You rated this ${userRating}/5.`);
        });
    });
  });

  paint(userRating || Math.round(avg));
});

/* ---------- Wishlist toggle ---------- */
let wishlistServerCount = 0;
const wishlistBadgeInit = document.querySelector('[data-wishlist-count]');
if (wishlistBadgeInit && wishlistBadgeInit.textContent.trim() !== '') {
  wishlistServerCount = parseInt(wishlistBadgeInit.textContent.trim(), 10) || 0;
}
let wishlistDelta = 0;

function refreshWishlistBadge() {
  const badge = document.querySelector('[data-wishlist-count]');
  if (!badge) return;
  const count = wishlistServerCount + wishlistDelta;
  if (count > 0) {
    badge.textContent = count;
    badge.classList.remove('hidden');
  } else {
    badge.classList.add('hidden');
  }
}

document.querySelectorAll('.js-wishlist').forEach((btn) => {
  const productId = btn.dataset.product;
  const label = btn.querySelector('.wishlist-label');

  function paint() {
    const saved = btn.dataset.saved === '1';
    const colorClass = saved ? 'text-red-400' : 'text-nv-500';
    btn.classList.remove('text-red-400', 'text-red-500', 'text-nv-500', 'text-nv-400');
    btn.classList.add(colorClass);
    if (label) label.textContent = saved ? 'Saved' : 'Save';
  }

  paint();
  btn.addEventListener('click', () => {
    fetch(`/product/${productId}/wishlist/`, {
      method: 'POST',
      headers: {
        'X-CSRFToken': getCookie('csrftoken'),
        'X-Requested-With': 'XMLHttpRequest',
      },
    })
      .then((r) => r.json().catch(() => ({ ok: false })))
      .then((data) => {
        if (handleLoginRequired(data)) return;
        if (!data.ok) return;
        btn.dataset.saved = data.saved ? '1' : '0';
        paint();
        wishlistDelta += data.saved ? 1 : -1;
        showToast(data.saved ? 'Saved to wishlist.' : 'Removed from wishlist.');
        refreshWishlistBadge();
      });
  });
});

/* ---------- Share ---------- */
document.querySelectorAll('.js-share').forEach((btn) => {
  btn.addEventListener('click', async () => {
    const url = new URL(btn.dataset.url, window.location.origin).href;
    if (navigator.share) {
      try {
        await navigator.share({ title: document.title, url });
      } catch (err) {
        // user cancelled
      }
    } else {
      try {
        await navigator.clipboard.writeText(url);
        showToast('Link copied!');
      } catch (err) {
        showToast(url);
      }
    }
  });
});