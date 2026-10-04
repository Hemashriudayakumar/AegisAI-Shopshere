// ShopSphere Global Scripts

function showToast(message, type = 'primary') {
  const toastContainer = document.getElementById('toast-container');
  if (!toastContainer) return;

  const toastEl = document.createElement('div');
  toastEl.className = `toast align-items-center text-bg-${type} border-0 show mb-2 shadow`;
  toastEl.setAttribute('role', 'alert');
  toastEl.innerHTML = `
    <div class="d-flex">
      <div class="toast-body">${message}</div>
      <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
    </div>
  `;
  toastContainer.appendChild(toastEl);
  setTimeout(() => {
    toastEl.classList.remove('show');
    setTimeout(() => toastEl.remove(), 300);
  }, 3500);
}

// 1-Click Demo User Switcher
async function switchDemoUser(customerId) {
  try {
    const res = await fetch('/api/auth/demo-switch', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ customer_id: customerId })
    });
    const data = await res.json();
    if (data.success) {
      showToast(data.message, 'success');
      setTimeout(() => window.location.reload(), 600);
    } else {
      showToast(data.message, 'danger');
    }
  } catch (err) {
    showToast('Failed to switch demo customer.', 'danger');
  }
}

// Quick Add to Cart
async function quickAddToCart(productId, quantity = 1) {
  try {
    const res = await fetch('/api/cart/add', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ product_id: productId, quantity: quantity })
    });
    const data = await res.json();
    if (data.success) {
      showToast(data.message, 'success');
      updateCartBadge(data.cart.total_items);
    } else {
      showToast(data.message, 'warning');
    }
  } catch (err) {
    showToast('Error adding product to cart.', 'danger');
  }
}

function updateCartBadge(count) {
  const badge = document.getElementById('navbar-cart-badge');
  if (badge) {
    badge.textContent = count;
    badge.classList.remove('d-none');
  }
}

// Track Recently Viewed Products
function recordRecentlyViewed(product) {
  if (!product || !product.product_id) return;
  try {
    let recent = JSON.parse(localStorage.getItem('shopsphere_recent') || '[]');
    recent = recent.filter(p => p.product_id !== product.product_id);
    recent.unshift({
      product_id: product.product_id,
      product_name: product.product_name,
      final_price: product.final_price,
      image: product.image,
      rating: product.rating
    });
    recent = recent.slice(0, 6);
    localStorage.setItem('shopsphere_recent', JSON.stringify(recent));
  } catch (e) {
    console.error(e);
  }
}

function renderRecentlyViewed(containerId) {
  const container = document.getElementById(containerId);
  if (!container) return;
  try {
    const recent = JSON.parse(localStorage.getItem('shopsphere_recent') || '[]');
    if (recent.length === 0) {
      container.innerHTML = '<p class="text-muted small">No recently viewed products yet.</p>';
      return;
    }
    container.innerHTML = recent.map(p => `
      <div class="col-6 col-md-4 col-lg-2 mb-3">
        <a href="/products/${p.product_id}" class="text-decoration-none">
          <div class="card h-100 border-0 shadow-sm p-2 text-center">
            <img src="${p.image}" class="img-fluid rounded mb-2" style="height: 110px; object-fit: cover;" alt="${p.product_name}">
            <div class="small fw-semibold text-truncate text-dark">${p.product_name}</div>
            <div class="text-primary fw-bold small">₹${p.final_price.toLocaleString('en-IN')}</div>
          </div>
        </a>
      </div>
    `).join('');
  } catch (e) {
    console.error(e);
  }
}

document.addEventListener('DOMContentLoaded', () => {
  // Global search form handler
  const searchForm = document.getElementById('global-search-form');
  const searchInput = document.getElementById('global-search-input');
  if (searchForm && searchInput) {
    searchForm.addEventListener('submit', (e) => {
      e.preventDefault();
      const q = searchInput.value.trim();
      if (q) {
        window.location.href = `/products?q=${encodeURIComponent(q)}`;
      }
    });
  }
});

