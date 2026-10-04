// ShopSphere Cart Management Scripts

async function loadCart() {
  const container = document.getElementById('cart-items-container');
  const summarySubtotal = document.getElementById('summary-subtotal');
  const summaryTotal = document.getElementById('summary-total');
  const emptyCartState = document.getElementById('empty-cart-state');
  const cartContentArea = document.getElementById('cart-content-area');

  if (!container) return;

  try {
    const res = await fetch('/api/cart');
    const data = await res.json();
    if (!data.success || !data.cart || data.cart.items.length === 0) {
      if (emptyCartState) emptyCartState.classList.remove('d-none');
      if (cartContentArea) cartContentArea.classList.add('d-none');
      updateCartBadge(0);
      return;
    }

    if (emptyCartState) emptyCartState.classList.add('d-none');
    if (cartContentArea) cartContentArea.classList.remove('d-none');

    const cart = data.cart;
    updateCartBadge(cart.total_items);

    container.innerHTML = cart.items.map(item => `
      <div class="card mb-3 border-0 shadow-sm p-3">
        <div class="row align-items-center">
          <div class="col-3 col-md-2">
            <img src="${item.image}" class="img-fluid rounded" alt="${item.product_name}">
          </div>
          <div class="col-9 col-md-5">
            <h6 class="mb-1 fw-bold"><a href="/products/${item.product_id}" class="text-dark text-decoration-none">${item.product_name}</a></h6>
            <div class="text-muted small mb-2">Brand: ${item.brand || 'ShopSphere'}</div>
            <div class="text-primary fw-bold">₹${item.unit_price.toLocaleString('en-IN')}</div>
          </div>
          <div class="col-6 col-md-3 mt-3 mt-md-0">
            <div class="input-group input-group-sm" style="max-width: 120px;">
              <button class="btn btn-outline-secondary" onclick="updateItemQuantity('${item.item_id}', ${item.quantity - 1})">-</button>
              <input type="text" class="form-control text-center" value="${item.quantity}" readonly>
              <button class="btn btn-outline-secondary" onclick="updateItemQuantity('${item.item_id}', ${item.quantity + 1})">+</button>
            </div>
          </div>
          <div class="col-6 col-md-2 text-end mt-3 mt-md-0">
            <div class="fw-bold mb-2">₹${item.total_price.toLocaleString('en-IN')}</div>
            <button class="btn btn-sm btn-outline-danger" onclick="removeItem('${item.item_id}')">
              <i class="bi bi-trash"></i>
            </button>
          </div>
        </div>
      </div>
    `).join('');

    if (summarySubtotal) summarySubtotal.textContent = `₹${cart.subtotal.toLocaleString('en-IN', { minimumFractionDigits: 2 })}`;
    if (summaryTotal) summaryTotal.textContent = `₹${cart.subtotal.toLocaleString('en-IN', { minimumFractionDigits: 2 })}`;
  } catch (e) {
    console.error(e);
  }
}

async function updateItemQuantity(itemId, newQty) {
  try {
    const res = await fetch(`/api/cart/item/${itemId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ quantity: newQty })
    });
    const data = await res.json();
    if (data.success) {
      loadCart();
    } else {
      showToast(data.message, 'warning');
    }
  } catch (err) {
    showToast('Failed to update item quantity.', 'danger');
  }
}

async function removeItem(itemId) {
  try {
    const res = await fetch(`/api/cart/item/${itemId}`, {
      method: 'DELETE'
    });
    const data = await res.json();
    if (data.success) {
      showToast(data.message, 'info');
      loadCart();
    } else {
      showToast(data.message, 'warning');
    }
  } catch (err) {
    showToast('Failed to remove item.', 'danger');
  }
}

async function clearEntireCart() {
  if (!confirm('Are you sure you want to clear your shopping cart?')) return;
  try {
    const res = await fetch('/api/cart/clear', { method: 'DELETE' });
    const data = await res.json();
    if (data.success) {
      showToast('Cart cleared', 'info');
      loadCart();
    }
  } catch (err) {
    showToast('Failed to clear cart', 'danger');
  }
}

