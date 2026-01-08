# Guest User and Sticky Headers Implementation Guide

## Completed Features

### ✅ Guest User System
- **Guest Login**: Username: `guest`, Password: `guest123`
- **Admin Login**: Username: `admin`, Password: (your custom password)
- **Role-Based Permissions**: Guest has read-only access

### ✅ API Protection
All write operations now require admin role:
- Creating bots (`POST /api/bots`)
- Updating bots (`PUT /api/bots/{bot_id}`)
- Deleting bots (`DELETE /api/bots/{bot_id}`)
- Starting/stopping bots
- Updating notes
- Closing trades
- Resetting wallets

### ✅ Backend Updates
- [src/utils/auth.py](src/utils/auth.py) - Added role tracking and `is_admin()` check
- [src/api/auth_routes.py](src/api/auth_routes.py) - Added guest credentials and role return
- [src/api/routes.py](src/api/routes.py) - Added `require_admin()` checks to write endpoints
- [src/main.py](src/main.py) - Templates now receive `role` and `is_admin` variables

## Remaining Tasks

### 1. Add Sticky Header to Homepage

Update `templates/index.html` to add a sticky header at the top:

```html
<!-- Add this right after <body> tag, before video background -->
<nav class="sticky top-0 z-50 bg-gray-900 bg-opacity-95 backdrop-blur-sm border-b border-gray-700">
    <div class="container mx-auto px-4">
        <div class="flex justify-between items-center h-16">
            <!-- Left: Logo/Title -->
            <div class="flex items-center">
                <h1 class="text-xl font-bold text-white">BotForm2</h1>
            </div>

            <!-- Center: Dashboard Stats -->
            <div class="hidden md:flex items-center space-x-6 text-sm">
                <div class="text-center">
                    <div class="text-gray-400 text-xs">Total P/L</div>
                    <div id="headerPL" class="font-semibold text-green-400">$0.00</div>
                </div>
                <div class="text-center">
                    <div class="text-gray-400 text-xs">Win Rate</div>
                    <div id="headerWinRate" class="font-semibold text-white">0%</div>
                </div>
                <div class="text-center">
                    <div class="text-gray-400 text-xs">Wallet Balance</div>
                    <div id="headerWallet" class="font-semibold text-yellow-400">$0.00</div>
                </div>
                <div class="text-center">
                    <div class="text-gray-400 text-xs">24h Growth</div>
                    <div id="header24hGrowth" class="font-semibold text-blue-400">+0%</div>
                </div>
            </div>

            <!-- Right: User Menu -->
            <div class="flex items-center space-x-4">
                <span class="text-gray-400 text-sm">{{ username }}
                    {% if role == 'guest' %}<span class="text-yellow-500">(Guest)</span>{% endif %}
                </span>
                <button id="hamburgerBtn" class="text-white hover:text-blue-400">
                    <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"></path>
                    </svg>
                </button>
            </div>
        </div>
    </div>
</nav>

<!-- Hamburger Menu (Hidden by default) -->
<div id="hamburgerMenu" class="hidden fixed top-16 right-0 z-40 w-64 bg-gray-800 border-l border-gray-700 shadow-xl">
    <div class="p-4 space-y-2">
        <a href="/" class="block px-4 py-2 text-white hover:bg-gray-700 rounded">Dashboard</a>
        <button onclick="logout()" class="block w-full text-left px-4 py-2 text-red-400 hover:bg-gray-700 rounded">Logout</button>
    </div>
</div>
```

Add JavaScript to update header stats:

```javascript
// Add to existing JavaScript in index.html
function updateHeaderStats() {
    // Update header with aggregated stats
    const totalPL = parseFloat(document.getElementById('totalPL').textContent.replace('$', '').replace(',', ''));
    const winRate = document.getElementById('winRate').textContent;
    const wallet = document.getElementById('walletBalance').textContent;

    document.getElementById('headerPL').textContent = document.getElementById('totalPL').textContent;
    document.getElementById('headerWinRate').textContent = winRate;
    document.getElementById('headerWallet').textContent = wallet;
    // TODO: Calculate 24h growth from performance data
}

// Hamburger menu toggle
document.getElementById('hamburgerBtn').addEventListener('click', () => {
    const menu = document.getElementById('hamburgerMenu');
    menu.classList.toggle('hidden');
});

// Close menu when clicking outside
document.addEventListener('click', (e) => {
    const menu = document.getElementById('hamburgerMenu');
    const btn = document.getElementById('hamburgerBtn');
    if (!menu.contains(e.target) && !btn.contains(e.target)) {
        menu.classList.add('hidden');
    }
});

// Logout function
function logout() {
    fetch('/api/auth/logout', { method: 'POST' })
        .then(() => window.location.href = '/login');
}

// Call updateHeaderStats after loading bots
// Add this after the loadBots() success
updateHeaderStats();
```

### 2. Add Sticky Header to Bot Detail Page

Update `templates/bot_detail.html`:

```html
<!-- Add after <body> tag -->
<nav class="sticky top-0 z-50 bg-gray-900 bg-opacity-95 backdrop-blur-sm border-b border-gray-700">
    <div class="container mx-auto px-4">
        <div class="flex justify-between items-center h-16">
            <!-- Left: Back button and Bot Name -->
            <div class="flex items-center space-x-4">
                <a href="/" class="text-blue-400 hover:text-blue-300">
                    <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18"></path>
                    </svg>
                </a>
                <div>
                    <h1 id="headerBotName" class="text-lg font-semibold text-white">Loading...</h1>
                    <p id="headerTargetUser" class="text-xs text-gray-400">Target: ...</p>
                </div>
            </div>

            <!-- Center: Bot Stats -->
            <div class="hidden md:flex items-center space-x-6 text-sm">
                <div class="text-center">
                    <div class="text-gray-400 text-xs">Total P/L</div>
                    <div id="headerBotPL" class="font-semibold text-green-400">$0.00</div>
                </div>
                <div class="text-center">
                    <div class="text-gray-400 text-xs">24h Growth</div>
                    <div id="headerBot24h" class="font-semibold text-blue-400">+0%</div>
                </div>
                <div class="text-center">
                    <div class="text-gray-400 text-xs">Target 24h</div>
                    <div id="headerTarget24h" class="font-semibold text-purple-400">+0%</div>
                </div>
            </div>

            <!-- Right: User Menu -->
            <div class="flex items-center space-x-4">
                <span class="text-gray-400 text-sm">{{ username }}
                    {% if role == 'guest' %}<span class="text-yellow-500">(Guest)</span>{% endif %}
                </span>
                <button id="hamburgerBtn" class="text-white hover:text-blue-400">
                    <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"></path>
                    </svg>
                </button>
            </div>
        </div>
    </div>
</nav>
```

### 3. Disable Buttons for Guest Users

In BOTH template files, wrap admin-only buttons with Jinja conditionals:

```html
<!-- Example: New Bot button -->
{% if is_admin %}
<button id="newBotBtn" class="btn btn-primary">+ New Bot</button>
{% endif %}

<!-- Example: Start/Stop buttons -->
{% if is_admin %}
<button onclick="startBot('{{ bot_id }}', 'paper')" class="btn btn-success">Start Paper</button>
<button onclick="stopBot('{{ bot_id }}')" class="btn btn-danger">Stop</button>
{% else %}
<button disabled class="btn btn-secondary opacity-50 cursor-not-allowed">Start Paper (Admin Only)</button>
<button disabled class="btn btn-secondary opacity-50 cursor-not-allowed">Stop (Admin Only)</button>
{% endif %}

<!-- Example: Delete button -->
{% if is_admin %}
<button onclick="deleteBot('{{ bot_id }}')" class="btn btn-danger">Delete</button>
{% endif %}
```

Also add JavaScript checks:

```javascript
// Add to existing JavaScript
const isAdmin = {{ is_admin|tojson }};

// Disable form submission for guests
if (!isAdmin) {
    document.getElementById('createBotForm')?.addEventListener('submit', (e) => {
        e.preventDefault();
        alert('Guest users cannot create bots. Please log in as admin.');
    });
}

// Show friendly error for API calls from guest
async function apiCall(url, method, data) {
    if (!isAdmin && ['POST', 'PUT', 'DELETE'].includes(method)) {
        alert('This action requires admin privileges.');
        return;
    }
    // ... rest of API call logic
}
```

## Testing Guide

### Test Guest User

1. **Logout** if currently logged in
2. **Login** with username: `guest`, password: `guest123`
3. **Verify**:
   - Can see dashboard
   - Can view bot details
   - Cannot see "New Bot" button
   - Cannot start/stop bots
   - Cannot delete bots
   - API calls to write endpoints return 403 Forbidden

### Test Admin User

1. **Logout**
2. **Login** with admin credentials
3. **Verify**:
   - Can see all buttons
   - Can create bots
   - Can start/stop bots
   - Can delete bots
   - All write operations work

## Current Status

✅ **Backend Complete**:
- Guest user created
- Role-based permissions implemented
- API endpoints protected
- Session management updated

⚠️ **Frontend Pending**:
- Sticky headers need to be added to templates
- Buttons need conditional rendering based on `is_admin`
- Hamburger menu needs to be added
- Header stats need JavaScript updates

## Quick Implementation Steps

1. Update `templates/index.html` with sticky header
2. Update `templates/bot_detail.html` with sticky header
3. Wrap all admin-only buttons with `{% if is_admin %}` conditionals
4. Add JavaScript for header stats updates
5. Add hamburger menu toggle functionality
6. Test with both guest and admin users

## Notes

- The `{{ is_admin }}` and `{{ role }}` variables are already being passed to templates
- Backend protection is in place, frontend is just for UX
- Even if a guest user bypasses frontend restrictions, backend will reject write operations
- 24h growth calculations will need to be implemented based on performance snapshot data
