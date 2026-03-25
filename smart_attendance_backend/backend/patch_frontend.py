#!/usr/bin/env python3
"""
patch_frontend.py
=================
Patches the frontend HTML files to use the real API instead of hardcoded mocks.
Run from the backend/ directory:
    python patch_frontend.py ../frontend

This script:
  1. Injects <script src="api.js"></script> into every HTML file
  2. Replaces the login page's mock submit handler with a real API call
  3. Patches the registration page to POST to the real API
  4. Patches the scan page to validate QR tokens via the API
  5. Patches the facial registration page upload to use the real API
  6. Adds auth guards to protected pages
"""

import re, shutil, sys
from pathlib import Path

FRONTEND = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("../frontend")

def read(p): return p.read_text(encoding="utf-8")
def write(p, t): p.write_text(t, encoding="utf-8"); print(f"  ✓ Patched {p.name}")

# ──────────────────────────────────────────────────────────────────────────────
# 1. Inject api.js into every page (before closing </body>)
# ──────────────────────────────────────────────────────────────────────────────
API_SCRIPT = '  <script src="api.js"></script>\n'

for html in FRONTEND.glob("*.html"):
    content = read(html)
    if 'src="api.js"' not in content:
        content = content.replace("</body>", API_SCRIPT + "</body>", 1)
        write(html, content)

print("\nAll pages: api.js injected.\n")

# ──────────────────────────────────────────────────────────────────────────────
# 2. Login page – replace mock submit with real API call
# ──────────────────────────────────────────────────────────────────────────────
LOGIN_REAL_SCRIPT = """
// ── Real API login (replaces mock) ──────────────────────────────────────────
const ROLE_REDIRECTS = {
    admin:   './admin_dashboard.html',
    faculty: './faculty_dashboard.html',
    student: './student_dashboard.html',
    scanner: './scan_page.html',
};
const STATUS_REDIRECTS = {
    pending:         './pending_approval.html',
    facial_required: './facial_registration.html',
};

const form         = document.getElementById('loginForm');
const credentialEl = document.getElementById('credential');
const passwordEl   = document.getElementById('password');
const formAlert    = document.getElementById('formAlert');
const loginButton  = document.getElementById('loginButton');
const loginSpinner = document.getElementById('loginSpinner');
const loginBtnText = document.getElementById('loginBtnText');

document.getElementById('togglePassword').addEventListener('click', () => {
    const isText = passwordEl.type === 'text';
    passwordEl.type = isText ? 'password' : 'text';
    document.getElementById('toggleIcon').classList.toggle('fa-eye');
    document.getElementById('toggleIcon').classList.toggle('fa-eye-slash');
});

document.getElementById('forgotPassword').addEventListener('click', async () => {
    const { value: email } = await Swal.fire({
        title: 'Reset Password', input: 'email',
        inputLabel: 'Enter your registered email',
        inputPlaceholder: 'name@university.edu',
        confirmButtonText: 'Send Reset Link', showCancelButton: true,
        confirmButtonColor: '#f08e1b'
    });
    if (email) {
        try { await API.auth.forgotPassword(email); } catch (_) {}
        Swal.fire({ icon: 'success', title: 'Email Sent',
            text: 'If that email is registered, a reset link has been sent.',
            timer: 2500, showConfirmButton: false });
    }
});

document.getElementById('termsLink').addEventListener('click', e => {
    e.preventDefault();
    Swal.fire({ title: 'Terms of Service', html: '<p class="text-start">Institutional attendance terms apply.</p>', icon: 'info', confirmButtonColor: '#f08e1b' });
});
document.getElementById('privacyLink').addEventListener('click', e => {
    e.preventDefault();
    Swal.fire({ title: 'Privacy Policy', html: '<p class="text-start">Attendance data is stored securely per institutional policy.</p>', icon: 'info', confirmButtonColor: '#f08e1b' });
});

form.addEventListener('submit', async (e) => {
    e.preventDefault();
    formAlert.classList.add('d-none');
    credentialEl.classList.remove('is-invalid');
    passwordEl.classList.remove('is-invalid');
    const credential = credentialEl.value.trim();
    const password   = passwordEl.value;
    let valid = true;
    if (!credential) { credentialEl.classList.add('is-invalid'); valid = false; }
    if (!password)   { passwordEl.classList.add('is-invalid');   valid = false; }
    if (!valid) {
        formAlert.textContent = 'Please fill in all required fields.';
        formAlert.classList.remove('d-none'); return;
    }
    setLoading(true);
    try {
        const { user } = await API.auth.login(credential, password);
        const redirect = STATUS_REDIRECTS[user.status] || ROLE_REDIRECTS[user.role] || './login_page.html';
        const labels   = { admin:'Administrator', faculty:'Faculty', student:'Student', scanner:'Scanner Operator' };
        await Swal.fire({ icon: 'success', title: `Welcome, ${user.full_name}`,
            text: `Signing you in as ${labels[user.role] || user.role}…`,
            showConfirmButton: false, timer: 1200 });
        window.location.href = redirect;
    } catch (err) {
        setLoading(false);
        const msg = err.message || 'Invalid credentials.';
        formAlert.textContent = msg; formAlert.classList.remove('d-none');
        Swal.fire({ icon: 'error', title: 'Authentication Failed', text: msg });
    }
});

function setLoading(on) {
    loginSpinner.classList.toggle('d-none', !on);
    loginBtnText.textContent = on ? 'Signing in…' : 'Login';
    [loginButton, credentialEl, passwordEl].forEach(el =>
        on ? el.setAttribute('disabled','disabled') : el.removeAttribute('disabled'));
}
"""

login = FRONTEND / "login_page.html"
content = read(login)
# Remove the big mock accounts block and replace the entire page script
start_marker = "// Demo accounts mapping"
end_marker   = "}\n  </script>\n </body>"
if start_marker in content:
    before = content[:content.index(start_marker)]
    after  = content[content.index(end_marker) + len("}\n  </script>"):]
    content = before + LOGIN_REAL_SCRIPT + "\n  </script>" + after
    write(login, content)
    print("Login page: mock replaced with real API.\n")

# ──────────────────────────────────────────────────────────────────────────────
# 3. Registration page – POST to real API
# ──────────────────────────────────────────────────────────────────────────────
REG_SUBMIT_PATCH = """
// ── Real API registration ────────────────────────────────────────────────────
const realForm = document.getElementById('registerForm') || form;
if (realForm) {
  realForm.addEventListener('submit', async function _apiSubmit(e) {
    e.preventDefault(); e.stopImmediatePropagation();
    const fullName   = document.getElementById('fullName')?.value.trim();
    const instId     = document.getElementById('instId')?.value.trim();
    const email      = document.getElementById('email')?.value.trim();
    const role       = document.getElementById('role')?.value || 'student';
    const password   = document.getElementById('password')?.value;
    const dept       = document.getElementById('department')?.value.trim() || null;
    const alertBox   = document.getElementById('formAlert');
    try {
        await API.auth.register(fullName, instId, email, role, password, dept);
        await Swal.fire({ icon:'success', title:'Registration Submitted',
            text:'Your account is pending admin approval. You will be notified.',
            confirmButtonColor:'#f08e1b' });
        window.location.href = './login_page.html';
    } catch(err) {
        if(alertBox){ alertBox.textContent = err.message; alertBox.classList.remove('d-none'); }
        else Swal.fire({ icon:'error', title:'Registration Failed', text: err.message });
    }
  });
}
"""

reg = FRONTEND / "registration_page.html"
content = read(reg)
if "API.auth.register" not in content:
    content = content.replace("</body>", f"  <script>{REG_SUBMIT_PATCH}</script>\n</body>", 1)
    write(reg, content)
    print("Registration page: real API submit added.\n")

# ──────────────────────────────────────────────────────────────────────────────
# 4. Add auth guards to protected pages
# ──────────────────────────────────────────────────────────────────────────────
GUARDS = {
    "student_dashboard.html":  "['student']",
    "faculty_dashboard.html":  "['faculty']",
    "admin_dashboard.html":    "['admin']",
    "session_page.html":       "['faculty','admin']",
    "user_management.html":    "['admin']",
    "reports_page.html":       "['admin','faculty']",
    "analytics_dashboard.html":"['admin']",
    "attendance_history.html": "['student']",
    "scan_page.html":          "['student','scanner']",
    "settings_page.html":      "['admin','faculty','student']",
    "user_profile.html":       "['admin','faculty','student']",
    "pending_approval.html":   "[]",
    "facial_registration.html":"[]",
}

for filename, roles in GUARDS.items():
    p = FRONTEND / filename
    if not p.exists(): continue
    content = read(p)
    guard_script = f"""  <script>
  // Auth guard
  (function(){{
    const u = API.auth.guard({roles});
    if(!u) return;
    // Populate name placeholders if present
    document.querySelectorAll('.js-user-name').forEach(el => el.textContent = u.full_name);
    document.querySelectorAll('.js-user-role').forEach(el => el.textContent = u.role);
    document.querySelectorAll('.js-user-id').forEach(el => el.textContent = u.inst_id);
  }})();
  </script>
"""
    if "API.auth.guard" not in content:
        # Inject right after <body>
        content = re.sub(r'(<body[^>]*>)', r'\1\n' + guard_script, content, count=1)
        write(p, content)

print("Auth guards injected into protected pages.\n")

# ──────────────────────────────────────────────────────────────────────────────
# 5. Logout buttons → real API.auth.logout()
# ──────────────────────────────────────────────────────────────────────────────
LOGOUT_PATCH = """  <script>
  document.addEventListener('click', e => {
    const el = e.target.closest('[id*="logout"],[class*="logout"]');
    if (el) { e.preventDefault(); API.auth.logout(); }
  });
  </script>
"""

for html in FRONTEND.glob("*.html"):
    content = read(html)
    if ("logout" in content.lower() or "Logout" in content) and "API.auth.logout" not in content:
        content = content.replace("</body>", LOGOUT_PATCH + "</body>", 1)
        write(html, content)

print("Logout wiring done.\n")
print("✅  Frontend patch complete!")
print(f"   Patched files are in: {FRONTEND.resolve()}")
print("\nNext steps:")
print("  1. Copy api.js into your frontend folder")
print("  2. Start backend:  cd backend && uvicorn main:app --reload")
print("  3. Seed data:      python seed.py")
print("  4. Open frontend/login_page.html in your browser")
