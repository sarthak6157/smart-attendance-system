/**
 * api.js  –  Smart Attendance System Frontend API Client
 * ========================================================
 * Drop this file in the /frontend_code folder alongside the HTML pages.
 */

const API = (() => {
  // Automatically switch between local development and production backend
  const isLocal = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
  
  // Replace this with your actual Render backend URL once deployed!
 const LIVE_BACKEND_URL = "https://smart-attendance-api-2dol.onrender.com/api";
  
  const BASE_URL = isLocal ? "http://localhost:8000/api" : LIVE_BACKEND_URL;

  // -------------------------------------------------------------------------
  // Token helpers
  // -------------------------------------------------------------------------

  const getToken = () => sessionStorage.getItem("access_token");
  const setToken = (t) => sessionStorage.setItem("access_token", t);
  const clearToken = () => sessionStorage.removeItem("access_token");

  const getUser = () => {
    const raw = sessionStorage.getItem("current_user");
    return raw ? JSON.parse(raw) : null;
  };
  const setUser = (u) => sessionStorage.setItem("current_user", JSON.stringify(u));
  const clearUser = () => sessionStorage.removeItem("current_user");

  // -------------------------------------------------------------------------
  // Core fetch wrapper
  // -------------------------------------------------------------------------

  async function request(path, { method = "GET", body, auth = true } = {}) {
    const headers = { "Content-Type": "application/json" };
    if (auth) {
      const token = getToken();
      if (!token) {
        window.location.href = "./login_page.html";
        return;
      }
      headers["Authorization"] = `Bearer ${token}`;
    }

    const res = await fetch(`${BASE_URL}${path}`, {
      method,
      headers,
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });

    if (res.status === 401) {
      clearToken();
      clearUser();
      window.location.href = "./login_page.html";
      return;
    }

    const data = res.status !== 204 ? await res.json() : null;

    if (!res.ok) {
      const message = data?.detail || `HTTP ${res.status}`;
      throw new Error(message);
    }

    return data;
  }

  // -------------------------------------------------------------------------
  // AUTH
  // -------------------------------------------------------------------------

  const auth = {
    async login(credential, password) {
      const data = await request("/auth/login", {
        method: "POST",
        body: { credential, password },
        auth: false,
      });

      setToken(data.access_token);
      setUser(data.user);
      return data;
    },

    async register(fullName, instId, email, role, password, department = null) {
      return request("/auth/register", {
        method: "POST",
        body: { full_name: fullName, inst_id: instId, email, role, password, department },
        auth: false,
      });
    },

    async me() {
      return request("/auth/me");
    },

    async changePassword(currentPassword, newPassword) {
      return request("/auth/change-password", {
        method: "POST",
        body: { current_password: currentPassword, new_password: newPassword },
      });
    },

    async forgotPassword(email) {
      return request("/auth/forgot-password", {
        method: "POST",
        body: { email },
        auth: false,
      });
    },

    logout() {
      clearToken();
      clearUser();
      window.location.href = "./login_page.html";
    },

    currentUser() {
      return getUser();
    },

    guard(allowedRoles = []) {
      const user = getUser();
      if (!user || !getToken()) {
        window.location.href = "./login_page.html";
        return null;
      }
      if (allowedRoles.length && !allowedRoles.includes(user.role)) {
        const redirects = {
          admin: "./admin_dashboard.html",
          faculty: "./faculty_dashboard.html",
          student: "./student_dashboard.html",
          scanner: "./scan_page.html",
        };
        window.location.href = redirects[user.role] || "./login_page.html";
        return null;
      }
      if (user.status === "pending") {
        window.location.href = "./pending_approval.html";
        return null;
      }
      if (user.status === "facial_required") {
        window.location.href = "./facial_registration.html";
        return null;
      }
      return user;
    },
  };

  // -------------------------------------------------------------------------
  // USERS
  // -------------------------------------------------------------------------

  const users = {
    list({ role, status, search, skip = 0, limit = 50 } = {}) {
      const params = new URLSearchParams();
      if (role)   params.set("role", role);
      if (status) params.set("status", status);
      if (search) params.set("search", search);
      params.set("skip", skip);
      params.set("limit", limit);
      return request(`/users?${params}`);
    },

    get(userId) {
      return request(`/users/${userId}`);
    },

    update(userId, data) {
      return request(`/users/${userId}`, { method: "PATCH", body: data });
    },

    setStatus(userId, status) {
      return request(`/users/${userId}/status`, { method: "PATCH", body: { status } });
    },

    delete(userId) {
      return request(`/users/${userId}`, { method: "DELETE" });
    },

    pending() {
      return request("/users/pending/list");
    },

    bulkApprove(userIds) {
      return request("/users/bulk-approve", { method: "POST", body: userIds });
    },
  };

  // -------------------------------------------------------------------------
  // COURSES
  // -------------------------------------------------------------------------

  const courses = {
    list() {
      return request("/courses");
    },

    get(courseId) {
      return request(`/courses/${courseId}`);
    },

    create(code, name, department, credits = 3) {
      return request("/courses", { method: "POST", body: { code, name, department, credits } });
    },

    delete(courseId) {
      return request(`/courses/${courseId}`, { method: "DELETE" });
    },
  };

  // -------------------------------------------------------------------------
  // SESSIONS
  // -------------------------------------------------------------------------

  const sessions = {
    list({ courseId, facultyId, status, skip = 0, limit = 50 } = {}) {
      const params = new URLSearchParams();
      if (courseId)  params.set("course_id", courseId);
      if (facultyId) params.set("faculty_id", facultyId);
      if (status)    params.set("status", status);
      params.set("skip", skip);
      params.set("limit", limit);
      return request(`/sessions?${params}`);
    },

    get(sessionId) {
      return request(`/sessions/${sessionId}`);
    },

    create({ courseId, title, location, scheduledAt, graceMinutes = 15 }) {
      return request("/sessions", {
        method: "POST",
        body: {
          course_id:     courseId,
          title,
          location,
          scheduled_at:  scheduledAt,
          grace_minutes: graceMinutes,
        },
      });
    },

    update(sessionId, data) {
      return request(`/sessions/${sessionId}`, { method: "PATCH", body: data });
    },

    start(sessionId) {
      return request(`/sessions/${sessionId}/start`, { method: "POST" });
    },

    end(sessionId) {
      return request(`/sessions/${sessionId}/end`, { method: "POST" });
    },

    refreshQR(sessionId) {
      return request(`/sessions/${sessionId}/refresh-qr`, { method: "POST" });
    },

    delete(sessionId) {
      return request(`/sessions/${sessionId}`, { method: "DELETE" });
    },
  };

  // -------------------------------------------------------------------------
  // ATTENDANCE
  // -------------------------------------------------------------------------

  const attendance = {
    markByQR(qrToken) {
      const user = getUser();
      return request("/attendance/qr", {
        method: "POST",
        body: { qr_token: qrToken, student_id: user?.id },
      });
    },

    markByFacial(sessionId) {
      return request(`/attendance/facial?session_id=${sessionId}`, { method: "POST" });
    },

    markManual({ sessionId, studentId, status = "present", notes = null }) {
      return request("/attendance/manual", {
        method: "POST",
        body: { session_id: sessionId, student_id: studentId, status, notes },
      });
    },

    forSession(sessionId) {
      return request(`/attendance/session/${sessionId}`);
    },

    forStudent(studentId, { courseId, skip = 0, limit = 100 } = {}) {
      const params = new URLSearchParams({ skip, limit });
      if (courseId) params.set("course_id", courseId);
      return request(`/attendance/student/${studentId}?${params}`);
    },

    deleteRecord(recordId) {
      return request(`/attendance/${recordId}`, { method: "DELETE" });
    },
  };

  // -------------------------------------------------------------------------
  // BIOMETRICS
  // -------------------------------------------------------------------------

  const biometrics = {
    enroll(userId, source) {
      let base64;
      if (typeof source === "string") {
        base64 = source;
      } else {
        base64 = source.toDataURL("image/jpeg").split(",")[1];
      }
      return request(`/biometrics/users/${userId}/biometrics`, {
        method: "POST",
        body: { image_base64: base64 },
      });
    },

    status(userId) {
      return request(`/biometrics/users/${userId}/biometrics`);
    },

    delete(userId) {
      return request(`/biometrics/users/${userId}/biometrics`, { method: "DELETE" });
    },
  };

  // -------------------------------------------------------------------------
  // REPORTS
  // -------------------------------------------------------------------------

  const reports = {
    overview() {
      return request("/reports/overview");
    },

    byCourse(courseId) {
      return request(`/reports/course/${courseId}`);
    },

    byStudent(studentId) {
      return request(`/reports/student/${studentId}`);
    },

    exportCSV(courseId) {
      const token = getToken();
      const a = document.createElement("a");
      a.href = `${BASE_URL}/reports/course/${courseId}/export`;
      a.download = `attendance_course_${courseId}.csv`;
      fetch(`${BASE_URL}/reports/course/${courseId}/export`, {
        headers: { Authorization: `Bearer ${token}` },
      })
        .then((res) => res.blob())
        .then((blob) => {
          const url = URL.createObjectURL(blob);
          a.href = url;
          document.body.appendChild(a);
          a.click();
          document.body.removeChild(a);
          URL.revokeObjectURL(url);
        });
    },
  };

  const qr = {
    url(token, size = 260) {
      return `https://api.qrserver.com/v1/create-qr-code/?size=${size}x${size}&data=${encodeURIComponent(token)}`;
    },
  };

  return { auth, users, courses, sessions, attendance, biometrics, reports, qr };
})();
