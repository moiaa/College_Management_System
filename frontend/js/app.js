/**
 * College Management System - Material 3 Expressive Frontend Engine
 * Authentication, Multi-user Role Switching, Dynamic Navigation & Admin Superpowers.
 */

// ============================================================
// Predefined User Accounts (Dev / Prototype Mode)
// ============================================================
const USERS = {
  'admin': {
    username: 'admin',
    password: 'admin',
    name: 'Администратор Системы',
    role: 'admin',
    roleLabel: 'Администратор',
    avatar: 'АД',
    email: 'admin@college.edu'
  },
  'teacher': {
    username: 'teacher',
    password: '1234',
    name: 'Михаил Ширяев',
    role: 'teacher',
    roleLabel: 'Преподаватель',
    avatar: 'МШ',
    subject: 'Разработка ПО',
    email: 'm.shiriaev@college.edu'
  },
  'student': {
    username: 'student',
    password: '1234',
    name: 'Александров Илья',
    role: 'student',
    roleLabel: 'Студент',
    avatar: 'ИА',
    group: 'ИС-31',
    email: 'i.alexandrov@college.edu'
  }
};

// Permitted tabs according to role specification:
// - Teacher: Gradebook, Schedule, Curriculum, Teacher Portal (NO reports, NO student portal, NO admin panel)
// - Student: Gradebook, Schedule, Student Portal (NO curriculum, NO reports, NO teacher portal, NO admin panel)
// - Admin: ALL tabs + Superpowers!
const ROLE_PERMISSIONS = {
  'admin': ['gradebook', 'schedule', 'curriculum', 'reports', 'student-portal', 'teacher-portal', 'admin-panel'],
  'teacher': ['gradebook', 'schedule', 'curriculum', 'teacher-portal'],
  'student': ['gradebook', 'schedule', 'student-portal']
};

// Sample Database for Teacher Portal & Student Portal
const TEACHERS_DATA = {
  'Михаил Ширяев': {
    name: 'Михаил Ширяев',
    subject: 'Разработка ПО',
    groupsCount: 4,
    hoursWeekly: 18,
    groups: ['ИС-31', 'ОИ31-09', 'ОИ32-09', 'ОИ33-09'],
    consultation: 'Среда 14:00 - 16:00, каб. 302'
  },
  'Моисеева А. А.': {
    name: 'Моисеева А. А.',
    subject: 'Разработка программных модулей',
    groupsCount: 5,
    hoursWeekly: 22,
    groups: ['ОИ31-09', 'ОИ32-09', 'ОИ33-09', 'ОИ21-09', 'ИС-31'],
    consultation: 'Пятница 15:00 - 17:00, каб. 210'
  },
  'Смирнов В. И.': {
    name: 'Смирнов В. И.',
    subject: 'Проектирование баз данных',
    groupsCount: 3,
    hoursWeekly: 16,
    groups: ['ИС-31', 'ОИ32-09', 'ОИ33-09'],
    consultation: 'Понедельник 13:00 - 15:00, каб. 418'
  }
};

// Database of Subjects and Grades for Students
const STUDENT_SUBJECTS_DATA = {
  'Александров Илья': [
    {
      id: 1,
      name: 'Разработка программных модулей',
      code: 'МДК 01.01',
      teacher: 'Моисеева А. А.',
      controlType: 'exam',
      controlLabel: 'Экзамен',
      badgeClass: 'badge-control-exam',
      grades: { '02.09': 5, '04.09': 5, '09.09': 4, '11.09': 5, '16.09': 5, '18.09': 5 },
      attendance: { '02.09': 'P', '04.09': 'P', '09.09': 'P', '11.09': 'P', '16.09': 'P', '18.09': 'P' },
      comment: 'Лаб. работа №2 сдана досрочно'
    },
    {
      id: 2,
      name: 'Проектирование баз данных',
      code: 'МДК 02.01',
      teacher: 'Смирнов В. И.',
      controlType: 'diff',
      controlLabel: 'Дифф. зачёт',
      badgeClass: 'badge-control-diff',
      grades: { '02.09': 4, '04.09': 4, '09.09': 5, '11.09': 4, '16.09': 4, '18.09': 5 },
      attendance: { '02.09': 'P', '04.09': 'P', '09.09': 'P', '11.09': 'P', '16.09': 'P', '18.09': 'P' },
      comment: 'Нормализация схемы БД (3НФ)'
    },
    {
      id: 3,
      name: 'Веб-дизайн и верстка ПО',
      code: 'МДК 03.01',
      teacher: 'Ширяев М. В.',
      controlType: 'exam',
      controlLabel: 'Экзамен',
      badgeClass: 'badge-control-exam',
      grades: { '02.09': 5, '04.09': 4, '09.09': 5, '11.09': null, '16.09': 5, '18.09': 4 },
      attendance: { '02.09': 'P', '04.09': 'P', '09.09': 'P', '11.09': 'A', '16.09': 'P', '18.09': 'P' },
      comment: 'Практикум: Material 3 Expressive'
    },
    {
      id: 4,
      name: 'Компьютерные сети',
      code: 'ОП.06',
      teacher: 'Кузнецов Д. А.',
      controlType: 'diff',
      controlLabel: 'Дифф. зачёт',
      badgeClass: 'badge-control-diff',
      grades: { '02.09': 4, '04.09': 5, '09.09': 4, '11.09': 4, '16.09': null, '18.09': 5 },
      attendance: { '02.09': 'P', '04.09': 'P', '09.09': 'P', '11.09': 'P', '16.09': 'A', '18.09': 'P' },
      comment: 'Настройка маршрутизации и VLAN'
    },
    {
      id: 5,
      name: 'Операционные системы и среды',
      code: 'ОП.04',
      teacher: 'Васильев П. Н.',
      controlType: 'exam',
      controlLabel: 'Экзамен',
      badgeClass: 'badge-control-exam',
      grades: { '02.09': 5, '04.09': 5, '09.09': 5, '11.09': 4, '16.09': 5, '18.09': 5 },
      attendance: { '02.09': 'P', '04.09': 'P', '09.09': 'P', '11.09': 'P', '16.09': 'P', '18.09': 'P' },
      comment: 'Тестирование системных вызовов'
    },
    {
      id: 6,
      name: 'Архитектура аппаратных средств',
      code: 'ОП.02',
      teacher: 'Федорова Е. С.',
      controlType: 'pass',
      controlLabel: 'Зачёт',
      badgeClass: 'badge-control-pass',
      grades: { '02.09': 4, '04.09': 4, '09.09': 4, '11.09': 5, '16.09': 4, '18.09': 4 },
      attendance: { '02.09': 'P', '04.09': 'P', '09.09': 'P', '11.09': 'P', '16.09': 'P', '18.09': 'P' },
      comment: 'Контрольный опрос: микроархитектура'
    },
    {
      id: 7,
      name: 'Иностранный язык в проф. деятельности',
      code: 'ОГСЭ.03',
      teacher: 'Лебедева Н. В.',
      controlType: 'diff',
      controlLabel: 'Дифф. зачёт',
      badgeClass: 'badge-control-diff',
      grades: { '02.09': 5, '04.09': 5, '09.09': 5, '11.09': 5, '16.09': 5, '18.09': 5 },
      attendance: { '02.09': 'P', '04.09': 'P', '09.09': 'P', '11.09': 'P', '16.09': 'P', '18.09': 'P' },
      comment: 'Чтение технической документации'
    }
  ]
};

function getStudentSubjects(studentName) {
  if (STUDENT_SUBJECTS_DATA[studentName]) {
    return STUDENT_SUBJECTS_DATA[studentName];
  }
  return STUDENT_SUBJECTS_DATA['Александров Илья'];
}

// Application State
const state = {
  currentUser: null,
  theme: localStorage.getItem('cms_theme') || 'light',
  currentTab: 'gradebook',
  selectedGroup: 'ИС-31',
  selectedSubject: 'Разработка ПО',
  selectedPeriod: 'Сентябрь 2026',
  studentFilterControl: 'all',
  
  // Admin dynamic target views
  adminTargetTeacher: 'Михаил Ширяев',
  adminTargetStudentId: 1,
  adminGradebookMode: 'group', // 'group' (all students) or 'student' (individual subjects)
  adminGradebookStudentId: 1,

  dates: ['02.09', '04.09', '09.09', '11.09', '16.09', '18.09'],
  
  students: [
    {
      id: 1,
      name: 'Александров Илья',
      grades: { '02.09': 5, '04.09': 4, '09.09': 5, '11.09': null, '16.09': 5, '18.09': 4 },
      attendance: { '02.09': 'P', '04.09': 'P', '09.09': 'P', '11.09': 'A', '16.09': 'P', '18.09': 'P' },
      comment: 'Практическая работа'
    },
    {
      id: 2,
      name: 'Беляева Анна',
      grades: { '02.09': 4, '04.09': 5, '09.09': 5, '11.09': 5, '16.09': 5, '18.09': 5 },
      attendance: { '02.09': 'P', '04.09': 'P', '09.09': 'P', '11.09': 'P', '16.09': 'P', '18.09': 'P' },
      comment: 'Без замечаний'
    },
    {
      id: 3,
      name: 'Васильев Максим',
      grades: { '02.09': 3, '04.09': 4, '09.09': null, '11.09': 4, '16.09': 3, '18.09': 4 },
      attendance: { '02.09': 'P', '04.09': 'P', '09.09': 'A', '11.09': 'P', '16.09': 'P', '18.09': 'P' },
      comment: 'Нужно закрыть пропуск'
    },
    {
      id: 4,
      name: 'Громова София',
      grades: { '02.09': 5, '04.09': 5, '09.09': 4, '11.09': 5, '16.09': 4, '18.09': 5 },
      attendance: { '02.09': 'P', '04.09': 'P', '09.09': 'P', '11.09': 'P', '16.09': 'P', '18.09': 'P' },
      comment: 'Хорошая работа'
    },
    {
      id: 5,
      name: 'Дмитриев Артём',
      grades: { '02.09': null, '04.09': 4, '09.09': 3, '11.09': 4, '16.09': 5, '18.09': null },
      attendance: { '02.09': 'A', '04.09': 'P', '09.09': 'P', '11.09': 'P', '16.09': 'P', '18.09': 'A' },
      comment: 'Ответ у доски'
    },
    {
      id: 6,
      name: 'Егорова Мария',
      grades: { '02.09': 5, '04.09': 5, '09.09': 5, '11.09': 5, '16.09': 5, '18.09': 5 },
      attendance: { '02.09': 'P', '04.09': 'P', '09.09': 'P', '11.09': 'P', '16.09': 'P', '18.09': 'P' },
      comment: 'Отработка до 25.09'
    },
    {
      id: 7,
      name: 'Иванов Кирилл',
      grades: { '02.09': 4, '04.09': 3, '09.09': 4, '11.09': null, '16.09': 4, '18.09': 3 },
      attendance: { '02.09': 'P', '04.09': 'P', '09.09': 'P', '11.09': 'A', '16.09': 'P', '18.09': 'P' },
      comment: 'Без замечаний'
    }
  ]
};

// ============================================================
// Initialization & Authentication Engine
// ============================================================
document.addEventListener('DOMContentLoaded', () => {
  initTheme();
  initAuth();
  setupNavigation();
  setupModals();
  setupFilters();
  setupProfilePopover();
  setupLoginForm();
});

function initTheme() {
  document.documentElement.setAttribute('data-theme', state.theme);
  updateThemeIcon();
}

function toggleTheme() {
  state.theme = state.theme === 'light' ? 'dark' : 'light';
  localStorage.setItem('cms_theme', state.theme);
  document.documentElement.setAttribute('data-theme', state.theme);
  updateThemeIcon();
  showToast(`Включена ${state.theme === 'dark' ? 'тёмная' : 'светлая'} тема`);
}

function updateThemeIcon() {
  const icon = document.getElementById('theme-icon');
  if (!icon) return;
  icon.innerHTML = state.theme === 'dark' ? '&#9728;' : '&#9790;';
}

function initAuth() {
  const savedUsername = localStorage.getItem('cms_user') || 'teacher';
  const user = USERS[savedUsername] || USERS['teacher'];
  setCurrentUser(user);
}

function setCurrentUser(user) {
  state.currentUser = user;
  localStorage.setItem('cms_user', user.username);

  // Update profile cards in sidebar and popover
  document.getElementById('sidebar-user-avatar').textContent = user.avatar;
  document.getElementById('sidebar-user-name').textContent = user.name;
  document.getElementById('sidebar-user-role').textContent = user.roleLabel;

  const popoverAvatar = document.getElementById('popover-avatar');
  if (popoverAvatar) popoverAvatar.textContent = user.avatar;
  const popoverName = document.getElementById('popover-name');
  if (popoverName) popoverName.textContent = user.name;
  const popoverRole = document.getElementById('popover-role-badge');
  if (popoverRole) popoverRole.textContent = user.roleLabel;

  // Update Role Tabs in Sidebar
  applyRoleTabVisibility(user.role);

  // Ensure current tab is permitted for this role
  const permittedTabs = ROLE_PERMISSIONS[user.role];
  if (!permittedTabs.includes(state.currentTab)) {
    switchTab(permittedTabs[0]);
  } else {
    switchTab(state.currentTab);
  }

  // Update role-specific UI components
  applyRoleViewCustomizations(user);
  renderGradebookTable();
}

function applyRoleTabVisibility(role) {
  const permittedTabs = ROLE_PERMISSIONS[role] || [];
  const navItems = document.querySelectorAll('.nav-item[data-tab]');

  navItems.forEach(item => {
    const tabName = item.getAttribute('data-tab');
    if (permittedTabs.includes(tabName)) {
      item.style.display = 'block';
    } else {
      item.style.display = 'none';
    }
  });

  // Highlight active account button in popover
  document.querySelectorAll('.btn-switch-account').forEach(btn => {
    const btnUser = btn.getAttribute('data-username');
    if (btnUser === state.currentUser.username) {
      btn.classList.add('current');
    } else {
      btn.classList.remove('current');
    }
  });
}

function applyRoleViewCustomizations(user) {
  const addGradeBtn = document.getElementById('btn-add-grade-global');
  const adminBanners = document.querySelectorAll('.admin-superpower-bar');

  // 1. Gradebook action buttons
  if (addGradeBtn) {
    if (user.role === 'student') {
      addGradeBtn.style.display = 'none';
    } else {
      addGradeBtn.style.display = 'inline-flex';
    }
  }

  // 2. Admin Superpower Banners
  adminBanners.forEach(banner => {
    if (user.role === 'admin') {
      banner.style.display = 'flex';
    } else {
      banner.style.display = 'none';
    }
  });

  // 3. Update Teacher & Student Portals based on user or admin target
  updateTeacherPortalView();
  updateStudentPortalView();
}

// ============================================================
// Profile Popover & Login Modal / Switcher
// ============================================================
function setupProfilePopover() {
  const profileCard = document.getElementById('sidebar-profile-card');
  const popover = document.getElementById('profile-popover');

  if (profileCard && popover) {
    profileCard.addEventListener('click', (e) => {
      // Don't toggle popover if theme button was clicked
      if (e.target.closest('.theme-toggle-btn')) return;
      popover.classList.toggle('active');
    });

    // Close on outside click
    document.addEventListener('click', (e) => {
      if (!profileCard.contains(e.target) && !popover.contains(e.target)) {
        popover.classList.remove('active');
      }
    });
  }
}

function quickSwitchUser(username) {
  const targetUser = USERS[username];
  if (targetUser) {
    setCurrentUser(targetUser);
    document.getElementById('profile-popover').classList.remove('active');
    showToast(`Вы переключились на: ${targetUser.name} (${targetUser.roleLabel})`);
  }
}

function handleLogout() {
  document.getElementById('profile-popover').classList.remove('active');
  const loginOverlay = document.getElementById('login-overlay');
  if (loginOverlay) {
    loginOverlay.classList.add('active');
    document.getElementById('login-username').value = '';
    document.getElementById('login-password').value = '';
    document.getElementById('login-error').style.display = 'none';
  }
}

function setupLoginForm() {
  const form = document.getElementById('login-form');
  if (!form) return;

  form.addEventListener('submit', (e) => {
    e.preventDefault();
    const username = document.getElementById('login-username').value.trim();
    const password = document.getElementById('login-password').value.trim();
    const errorElem = document.getElementById('login-error');

    // Authenticate against USERS
    const matchedUser = Object.values(USERS).find(
      u => u.username === username && u.password === password
    );

    if (matchedUser) {
      errorElem.style.display = 'none';
      document.getElementById('login-overlay').classList.remove('active');
      setCurrentUser(matchedUser);
      showToast(`Добро пожаловать, ${matchedUser.name}!`);
    } else {
      errorElem.textContent = 'Неверный логин или пароль!';
      errorElem.style.display = 'block';
    }
  });
}

function fillAndLogin(username, password) {
  document.getElementById('login-username').value = username;
  document.getElementById('login-password').value = password;
  const matchedUser = USERS[username];
  if (matchedUser) {
    document.getElementById('login-error').style.display = 'none';
    document.getElementById('login-overlay').classList.remove('active');
    setCurrentUser(matchedUser);
    showToast(`Вход выполнен: ${matchedUser.name}`);
  }
}

// ============================================================
// Navigation across modules
// ============================================================
function setupNavigation() {
  const navLinks = document.querySelectorAll('.nav-link[data-tab]');
  navLinks.forEach(link => {
    link.addEventListener('click', (e) => {
      e.preventDefault();
      const targetTab = link.getAttribute('data-tab');
      switchTab(targetTab);
    });
  });
}

function switchTab(tabId) {
  state.currentTab = tabId;
  window.location.hash = tabId;

  // Active state in sidebar
  document.querySelectorAll('.nav-link[data-tab]').forEach(btn => {
    if (btn.getAttribute('data-tab') === tabId) {
      btn.classList.add('active');
    } else {
      btn.classList.remove('active');
    }
  });

  // Switch visible screen container with spring re-trigger
  document.querySelectorAll('.module-screen').forEach(screen => {
    if (screen.id === `screen-${tabId}`) {
      screen.style.display = 'block';
      screen.classList.remove('spring-entering');
      void screen.offsetWidth; // Force CSS reflow to re-trigger spring keyframes
      screen.classList.add('spring-entering');
    } else {
      screen.style.display = 'none';
      screen.classList.remove('spring-entering');
    }
  });

  // Update Top Bar Title & Subtitle
  const titles = {
    'gradebook': { title: 'Электронный журнал', subtitle: 'Оценки и посещаемость учебной группы' },
    'schedule': { title: 'Расписание занятий', subtitle: 'Текущий график пар и аудиторий' },
    'curriculum': { title: 'Рабочие программы', subtitle: 'Учебно-методические комплексы и дисциплины' },
    'reports': { title: 'Отчёты и статистика', subtitle: 'Сводные ведомости, аналитика успеваемости' },
    'student-portal': { title: 'Кабинет студента', subtitle: 'Цифровая зачётная книжка и заявки' },
    'teacher-portal': { title: 'Кабинет преподавателя', subtitle: 'Учебные группы, нагрузка и аттестация' },
    'admin-panel': { title: 'Админ-панель', subtitle: 'Управление пользователями, ролями и системой' }
  };

  const meta = titles[tabId] || titles['gradebook'];
  document.getElementById('current-page-title').textContent = meta.title;
  document.getElementById('current-page-subtitle').textContent = meta.subtitle;

  // Re-trigger view refreshes
  if (tabId === 'gradebook') {
    updateGradebookViewMode();
    renderGradebookTable();
  }
  if (tabId === 'teacher-portal') updateTeacherPortalView();
  if (tabId === 'student-portal') updateStudentPortalView();
}

// ============================================================
// Gradebook Calculations & Dual-Mode Rendering Engine
// ============================================================
function calculateStudentMetrics(student) {
  const validGrades = Object.values(student.grades).filter(g => typeof g === 'number' && !isNaN(g));
  const gpa = validGrades.length > 0
    ? (validGrades.reduce((a, b) => a + b, 0) / validGrades.length).toFixed(1)
    : '0.0';

  const totalLessons = state.dates.length;
  const attendedLessons = Object.values(student.attendance).filter(status => status === 'P').length;
  const attendanceRate = totalLessons > 0 ? Math.round((attendedLessons / totalLessons) * 100) : 0;

  return { gpa, attendanceRate };
}

function calculateGroupMetrics() {
  let totalAttended = 0;
  let totalOpportunities = state.students.length * state.dates.length;

  state.students.forEach(student => {
    totalAttended += Object.values(student.attendance).filter(status => status === 'P').length;
  });

  return totalOpportunities > 0 ? Math.round((totalAttended / totalOpportunities) * 100) : 0;
}

function calculateSubjectMetrics(subject) {
  const validGrades = Object.values(subject.grades).filter(g => typeof g === 'number' && !isNaN(g));
  const gpa = validGrades.length > 0
    ? (validGrades.reduce((a, b) => a + b, 0) / validGrades.length).toFixed(1)
    : '0.0';

  const totalLessons = state.dates.length;
  const attendedLessons = Object.values(subject.attendance).filter(status => status === 'P').length;
  const attendanceRate = totalLessons > 0 ? Math.round((attendedLessons / totalLessons) * 100) : 0;

  return { gpa, attendanceRate };
}

function calculateOverallStudentSubjectMetrics(subjects) {
  let allGrades = [];
  let totalAttended = 0;
  let totalOpportunities = subjects.length * state.dates.length;

  subjects.forEach(sub => {
    Object.values(sub.grades).forEach(g => {
      if (typeof g === 'number' && !isNaN(g)) allGrades.push(g);
    });
    totalAttended += Object.values(sub.attendance).filter(st => st === 'P').length;
  });

  const overallGpa = allGrades.length > 0
    ? (allGrades.reduce((a, b) => a + b, 0) / allGrades.length).toFixed(1)
    : '0.0';
  const overallAtt = totalOpportunities > 0
    ? Math.round((totalAttended / totalOpportunities) * 100)
    : 0;

  return { overallGpa, overallAtt };
}

function isStudentGradebookMode() {
  if (!state.currentUser) return false;
  if (state.currentUser.role === 'student') return true;
  if (state.currentUser.role === 'admin' && state.adminGradebookMode === 'student') return true;
  return false;
}

function getActiveStudentForGradebook() {
  if (state.currentUser.role === 'student') {
    return state.students.find(s => s.name === state.currentUser.name) || state.students[0];
  }
  if (state.currentUser.role === 'admin' && state.adminGradebookMode === 'student') {
    return state.students.find(s => s.id === state.adminGradebookStudentId) || state.students[0];
  }
  return state.students[0];
}

function updateGradebookViewMode() {
  const isStudentMode = isStudentGradebookMode();
  const activeStudent = getActiveStudentForGradebook();

  // 1. First & Last Column Headers
  const firstColHeader = document.getElementById('gradebook-first-col-header');
  const lastColHeader = document.getElementById('gradebook-last-col-header');

  if (firstColHeader) {
    firstColHeader.textContent = isStudentMode ? 'Предметы' : 'Студент';
  }
  if (lastColHeader) {
    lastColHeader.textContent = isStudentMode ? 'Форма контроля' : 'Действия';
  }

  // 2. Filters configuration
  const groupLabel = document.getElementById('filter-group-label');
  const groupSelect = document.getElementById('filter-group');
  const studentChip = document.getElementById('student-chip-display');
  const studentChipName = document.getElementById('student-chip-name');

  const subjectLabel = document.getElementById('filter-subject-label');
  const subjectSelect = document.getElementById('filter-subject');
  const studentControlSelect = document.getElementById('filter-student-control');

  const kpiLabel = document.getElementById('gradebook-kpi-label');
  const kpiValue = document.getElementById('group-attendance-kpi');

  if (isStudentMode) {
    if (groupLabel) groupLabel.textContent = 'Студент / Группа';
    if (groupSelect) groupSelect.style.display = 'none';
    if (studentChip) studentChip.style.display = 'inline-flex';
    if (studentChipName) studentChipName.textContent = `${activeStudent.name} (${state.selectedGroup})`;

    if (subjectLabel) subjectLabel.textContent = 'Дисциплины';
    if (subjectSelect) subjectSelect.style.display = 'none';
    if (studentControlSelect) studentControlSelect.style.display = 'block';

    const subjects = getStudentSubjects(activeStudent.name);
    const { overallGpa, overallAtt } = calculateOverallStudentSubjectMetrics(subjects);

    if (kpiLabel) kpiLabel.textContent = 'Средний балл (GPA)';
    if (kpiValue) {
      kpiValue.innerHTML = `${overallGpa} <span style="font-size:12px; font-weight:600; color:var(--md-sys-color-on-surface-variant); margin-left:6px;">(Посещ. ${overallAtt}%)</span>`;
    }

    // Dynamic Top App Bar for Gradebook tab
    if (state.currentTab === 'gradebook') {
      const pageTitle = document.getElementById('current-page-title');
      const pageSubtitle = document.getElementById('current-page-subtitle');
      if (pageTitle) pageTitle.textContent = 'Мой электронный журнал';
      if (pageSubtitle) pageSubtitle.textContent = `Успеваемость и посещаемость по дисциплинам • ${activeStudent.name} (${state.selectedGroup})`;
    }
  } else {
    if (groupLabel) groupLabel.textContent = 'Группа';
    if (groupSelect) groupSelect.style.display = 'block';
    if (studentChip) studentChip.style.display = 'none';

    if (subjectLabel) subjectLabel.textContent = 'Предмет';
    if (subjectSelect) subjectSelect.style.display = 'block';
    if (studentControlSelect) studentControlSelect.style.display = 'none';

    if (kpiLabel) kpiLabel.textContent = 'Посещаемость';
    if (kpiValue) kpiValue.textContent = `${calculateGroupMetrics()}%`;

    if (state.currentTab === 'gradebook') {
      const pageTitle = document.getElementById('current-page-title');
      const pageSubtitle = document.getElementById('current-page-subtitle');
      if (pageTitle) pageTitle.textContent = 'Электронный журнал';
      if (pageSubtitle) pageSubtitle.textContent = `Оценки и посещаемость группы ${state.selectedGroup} • ${state.selectedSubject}`;
    }
  }
}

function renderGradebookTable() {
  const tableHead = document.getElementById('gradebook-dates-header');
  const tableBody = document.getElementById('gradebook-table-body');
  if (!tableBody) return;

  // 1. Synchronize header and filter states
  updateGradebookViewMode();

  // 2. Render Date Headers
  if (tableHead) {
    tableHead.innerHTML = state.dates.map(date => `<th>${date}</th>`).join('');
  }

  const isStudentMode = isStudentGradebookMode();
  const activeStudent = getActiveStudentForGradebook();

  if (isStudentMode) {
    // ==========================================
    // STUDENT VIEW: Rows are SUBJECTS
    // ==========================================
    let subjects = getStudentSubjects(activeStudent.name);

    // Apply control type filter if needed
    if (state.studentFilterControl && state.studentFilterControl !== 'all') {
      subjects = subjects.filter(s => s.controlType === state.studentFilterControl);
    }

    tableBody.innerHTML = subjects.map((subject, idx) => {
      const { gpa, attendanceRate } = calculateSubjectMetrics(subject);

      // Date cells
      const dateCells = state.dates.map(date => {
        const grade = subject.grades[date];
        const att = subject.attendance[date];

        let cellContent = '—';
        let cellClass = 'grade-empty';

        if (att === 'A') {
          cellContent = 'Н';
          cellClass = 'grade-absent';
        } else if (grade === 5) {
          cellContent = '5';
          cellClass = 'grade-5';
        } else if (grade === 4) {
          cellContent = '4';
          cellClass = 'grade-4';
        } else if (grade === 3) {
          cellContent = '3';
          cellClass = 'grade-3';
        } else if (grade === 2) {
          cellContent = '2';
          cellClass = 'grade-3';
        }

        const clickHandler = `showStudentGradeDetail('${subject.name.replace(/'/g, "\\'")}', '${date}', '${cellContent}', '${subject.teacher.replace(/'/g, "\\'")}')`;

        return `
          <td>
            <button class="grade-cell-btn ${cellClass}" 
                    onclick="${clickHandler}"
                    title="${subject.name}: ${cellContent === 'Н' ? 'Пропуск' : (cellContent === '—' ? 'Нет оценки' : 'Оценка ' + cellContent)}">${cellContent}</button>
          </td>
        `;
      }).join('');

      return `
        <tr data-subject-id="${subject.id}" style="--row-index: ${idx};">
          <td class="col-student">
            <div class="subject-meta-cell">
              <span class="subject-name">${subject.name}</span>
              <div class="subject-info">
                <span class="subject-code-badge">${subject.code}</span>
                <span>${subject.teacher}</span>
              </div>
            </div>
          </td>
          ${dateCells}
          <td><span class="badge-gpa">${gpa}</span></td>
          <td><span class="badge-attendance">${attendanceRate}%</span></td>
          <td class="comment-cell" title="${subject.comment || ''}">${subject.comment || '—'}</td>
          <td>
            <span class="badge-control-type ${subject.badgeClass}">${subject.controlLabel}</span>
          </td>
        </tr>
      `;
    }).join('');

  } else {
    // ==========================================
    // TEACHER / ADMIN GROUP VIEW: Rows are STUDENTS
    // ==========================================
    tableBody.innerHTML = state.students.map((student, idx) => {
      const { gpa, attendanceRate } = calculateStudentMetrics(student);

      // Date cells
      const dateCells = state.dates.map(date => {
        const grade = student.grades[date];
        const att = student.attendance[date];

        let cellContent = '—';
        let cellClass = 'grade-empty';

        if (att === 'A') {
          cellContent = 'Н';
          cellClass = 'grade-absent';
        } else if (grade === 5) {
          cellContent = '5';
          cellClass = 'grade-5';
        } else if (grade === 4) {
          cellContent = '4';
          cellClass = 'grade-4';
        } else if (grade === 3) {
          cellContent = '3';
          cellClass = 'grade-3';
        } else if (grade === 2) {
          cellContent = '2';
          cellClass = 'grade-3';
        }

        const clickHandler = `openCellEditor(${student.id}, '${date}', ${grade}, '${att}')`;

        return `
          <td>
            <button class="grade-cell-btn ${cellClass}" 
                    onclick="${clickHandler}"
                    title="Нажмите для выставления/изменения">${cellContent}</button>
          </td>
        `;
      }).join('');

      const actionsCol = `
        <td>
          <div class="row-actions">
            <button class="btn-icon-action" onclick="openStudentQuickEdit(${student.id})">Изменить</button>
            <span style="opacity: 0.3;">·</span>
            <button class="btn-icon-action delete" onclick="deleteStudent(${student.id})">Удалить</button>
          </div>
        </td>
      `;

      return `
        <tr data-student-id="${student.id}" style="--row-index: ${idx};">
          <td class="col-student">${student.name}</td>
          ${dateCells}
          <td><span class="badge-gpa">${gpa}</span></td>
          <td><span class="badge-attendance">${attendanceRate}%</span></td>
          <td class="comment-cell" title="${student.comment || ''}">${student.comment || '—'}</td>
          ${actionsCol}
        </tr>
      `;
    }).join('');
  }

  // Bounce KPI Indicator on recalculation
  const kpiBlock = document.getElementById('gradebook-kpi-block');
  if (kpiBlock) {
    kpiBlock.classList.remove('kpi-pop');
    void kpiBlock.offsetWidth;
    kpiBlock.classList.add('kpi-pop');
  }
}

function showStudentGradeDetail(subjectName, date, mark, teacher) {
  let statusText = mark === 'Н' ? 'Пропуск занятия (Н)' : (mark === '—' ? 'Занятие без оценки' : `Оценка «${mark}»`);
  showToast(`«${subjectName}» • ${date}: ${statusText} (${teacher})`);
}

// ============================================================
// Modals & Interactive Grade Editing
// ============================================================
let editingContext = null;

function setupModals() {
  const pills = document.querySelectorAll('.grade-radio-pill');
  pills.forEach(pill => {
    pill.addEventListener('click', () => {
      pills.forEach(p => p.classList.remove('selected'));
      pill.classList.add('selected');
      const val = pill.getAttribute('data-val');
      document.getElementById('modal-grade-value').value = val;
    });
  });

  const studentSelect = document.getElementById('modal-student-select');
  if (studentSelect) {
    studentSelect.innerHTML = state.students.map(s => 
      `<option value="${s.id}">${s.name}</option>`
    ).join('');
  }

  const dateSelect = document.getElementById('modal-date-select');
  if (dateSelect) {
    dateSelect.innerHTML = state.dates.map(d => 
      `<option value="${d}">${d}</option>`
    ).join('');
  }
}

function openAddGradeModal() {
  if (state.currentUser && state.currentUser.role === 'student') {
    showToast('У студентов нет прав на выставление оценок!');
    return;
  }
  editingContext = null;
  document.getElementById('modal-title').textContent = 'Добавить оценку';
  document.getElementById('modal-comment').value = '';
  document.getElementById('modal-attendance-checkbox').checked = true;

  selectGradePill(5);
  document.getElementById('grade-modal').classList.add('active');
}

function openCellEditor(studentId, date, currentGrade, currentAttendance) {
  if (state.currentUser && state.currentUser.role === 'student') return;

  editingContext = { studentId, date };
  const student = state.students.find(s => s.id === studentId);
  if (!student) return;

  document.getElementById('modal-title').textContent = `Оценка: ${student.name} (${date})`;
  document.getElementById('modal-student-select').value = studentId;
  document.getElementById('modal-date-select').value = date;
  document.getElementById('modal-comment').value = student.comment || '';
  document.getElementById('modal-attendance-checkbox').checked = currentAttendance !== 'A';

  selectGradePill(currentGrade || 5);
  document.getElementById('grade-modal').classList.add('active');
}

function selectGradePill(val) {
  document.querySelectorAll('.grade-radio-pill').forEach(pill => {
    if (pill.getAttribute('data-val') == val) {
      pill.classList.add('selected');
    } else {
      pill.classList.remove('selected');
    }
  });
  document.getElementById('modal-grade-value').value = val || 5;
}

function closeModal() {
  document.getElementById('grade-modal').classList.remove('active');
  editingContext = null;
}

function saveGradeFromModal() {
  const studentId = parseInt(document.getElementById('modal-student-select').value, 10);
  const date = document.getElementById('modal-date-select').value;
  const gradeVal = parseInt(document.getElementById('modal-grade-value').value, 10);
  const isPresent = document.getElementById('modal-attendance-checkbox').checked;
  const comment = document.getElementById('modal-comment').value.trim();

  const student = state.students.find(s => s.id === studentId);
  if (!student) return;

  student.attendance[date] = isPresent ? 'P' : 'A';
  student.grades[date] = isPresent ? gradeVal : null;
  if (comment) {
    student.comment = comment;
  }

  renderGradebookTable();
  closeModal();
  showToast(`Оценка для ${student.name} сохранена!`);
}

function openStudentQuickEdit(studentId) {
  const student = state.students.find(s => s.id === studentId);
  if (!student) return;
  const newName = prompt('Изменить ФИО студента:', student.name);
  if (newName && newName.trim()) {
    student.name = newName.trim();
    renderGradebookTable();
    showToast('Данные студента обновлены');
  }
}

function deleteStudent(studentId) {
  const student = state.students.find(s => s.id === studentId);
  if (!student) return;
  if (confirm(`Вы уверены, что хотите удалить студента ${student.name}?`)) {
    state.students = state.students.filter(s => s.id !== studentId);
    renderGradebookTable();
    showToast('Студент удален из ведомости');
  }
}

// ============================================================
// Teacher Portal & Student Portal View Updates
// ============================================================
function updateTeacherPortalView() {
  const teacherName = state.currentUser.role === 'admin'
    ? state.adminTargetTeacher
    : (state.currentUser.name || 'Михаил Ширяев');

  const data = TEACHERS_DATA[teacherName] || TEACHERS_DATA['Михаил Ширяев'];

  const nameElem = document.getElementById('teacher-view-name');
  const subjectElem = document.getElementById('teacher-view-subject');
  const groupsElem = document.getElementById('teacher-view-groups');
  const hoursElem = document.getElementById('teacher-view-hours');
  const consultElem = document.getElementById('teacher-view-consult');

  if (nameElem) nameElem.textContent = data.name;
  if (subjectElem) subjectElem.textContent = data.subject;
  if (groupsElem) groupsElem.textContent = data.groups.join(', ');
  if (hoursElem) hoursElem.textContent = `${data.hoursWeekly} ч/нед. (${data.groupsCount} группы)`;
  if (consultElem) consultElem.textContent = data.consultation;
}

function updateStudentPortalView() {
  let student = null;
  if (state.currentUser.role === 'admin') {
    student = state.students.find(s => s.id === state.adminTargetStudentId) || state.students[0];
  } else if (state.currentUser.role === 'student') {
    student = state.students.find(s => s.name === state.currentUser.name) || state.students[0];
  } else {
    student = state.students[0];
  }

  const { gpa, attendanceRate } = calculateStudentMetrics(student);

  const nameElem = document.getElementById('student-view-name');
  const gpaElem = document.getElementById('student-view-gpa');
  const attElem = document.getElementById('student-view-att');
  const statusElem = document.getElementById('student-view-status');

  if (nameElem) nameElem.textContent = student.name;
  if (gpaElem) gpaElem.textContent = `GPA: ${gpa} / 5.0`;
  if (attElem) attElem.textContent = `Посещаемость: ${attendanceRate}%`;
  if (statusElem) {
    statusElem.textContent = parseFloat(gpa) >= 4.5
      ? 'Академическая стипендия назначена • Задолженностей нет'
      : (parseFloat(gpa) >= 3.5 ? 'Успевает в срок • Задолженностей нет' : 'Имеются академические задолженности');
  }
}

// ============================================================
// Filters & Admin Switcher Event Handlers
// ============================================================
function setupFilters() {
  const groupSelect = document.getElementById('filter-group');
  const subjectSelect = document.getElementById('filter-subject');
  const periodSelect = document.getElementById('filter-period');
  const studentControlSelect = document.getElementById('filter-student-control');

  if (groupSelect) {
    groupSelect.addEventListener('change', (e) => {
      state.selectedGroup = e.target.value;
      renderGradebookTable();
      showToast(`Выбрана группа: ${state.selectedGroup}`);
    });
  }
  if (subjectSelect) {
    subjectSelect.addEventListener('change', (e) => {
      state.selectedSubject = e.target.value;
      renderGradebookTable();
      showToast(`Выбран предмет: ${state.selectedSubject}`);
    });
  }
  if (periodSelect) {
    periodSelect.addEventListener('change', (e) => {
      state.selectedPeriod = e.target.value;
      renderGradebookTable();
      showToast(`Период: ${state.selectedPeriod}`);
    });
  }
  if (studentControlSelect) {
    studentControlSelect.addEventListener('change', (e) => {
      state.studentFilterControl = e.target.value;
      renderGradebookTable();
      showToast(`Фильтр дисциплин: ${e.target.options[e.target.selectedIndex].text}`);
    });
  }

  // Admin Superpower Switcher in Gradebook
  const adminGradebookMode = document.getElementById('admin-gradebook-mode');
  const adminGradebookStudentSelect = document.getElementById('admin-gradebook-student-select');

  if (adminGradebookStudentSelect) {
    adminGradebookStudentSelect.innerHTML = state.students.map(s => 
      `<option value="${s.id}">${s.name}</option>`
    ).join('');
    adminGradebookStudentSelect.addEventListener('change', (e) => {
      state.adminGradebookStudentId = parseInt(e.target.value, 10);
      renderGradebookTable();
      showToast(`Просмотр журнала студента: ${e.target.options[e.target.selectedIndex].text}`);
    });
  }

  if (adminGradebookMode) {
    adminGradebookMode.addEventListener('change', (e) => {
      state.adminGradebookMode = e.target.value;
      if (adminGradebookStudentSelect) {
        adminGradebookStudentSelect.style.display = e.target.value === 'student' ? 'block' : 'none';
      }
      renderGradebookTable();
      showToast(`Режим ведомости: ${e.target.value === 'student' ? 'Журнал предметов студента' : 'Ведомость группы'}`);
    });
  }

  // Admin Switcher in Teacher Portal
  const adminTeacherSelect = document.getElementById('admin-teacher-select');
  if (adminTeacherSelect) {
    adminTeacherSelect.addEventListener('change', (e) => {
      state.adminTargetTeacher = e.target.value;
      updateTeacherPortalView();
      showToast(`Просмотр кабинета: ${state.adminTargetTeacher}`);
    });
  }

  // Admin Switcher in Student Portal
  const adminStudentSelect = document.getElementById('admin-student-select');
  if (adminStudentSelect) {
    adminStudentSelect.innerHTML = state.students.map(s => 
      `<option value="${s.id}">${s.name}</option>`
    ).join('');
    adminStudentSelect.addEventListener('change', (e) => {
      state.adminTargetStudentId = parseInt(e.target.value, 10);
      updateStudentPortalView();
      showToast(`Просмотр профиля: ${e.target.options[e.target.selectedIndex].text}`);
    });
  }

  // Admin Schedule Group Switcher
  const adminScheduleGroup = document.getElementById('admin-schedule-group');
  if (adminScheduleGroup) {
    adminScheduleGroup.addEventListener('change', (e) => {
      const scheduleGroupTitle = document.getElementById('schedule-group-title');
      if (scheduleGroupTitle) {
        scheduleGroupTitle.textContent = `Расписание занятий группы ${e.target.value}`;
      }
      showToast(`Расписание переключено на: ${e.target.value}`);
    });
  }
}

function exportGradebook() {
  const isStudentMode = isStudentGradebookMode();
  const activeStudent = getActiveStudentForGradebook();

  if (isStudentMode) {
    let csv = `Предмет,Код,Преподаватель,Форма контроля,${state.dates.join(',')},Средний балл,Посещаемость,Комментарии\n`;
    const subjects = getStudentSubjects(activeStudent.name);
    subjects.forEach(s => {
      const { gpa, attendanceRate } = calculateSubjectMetrics(s);
      const gradesRow = state.dates.map(d => s.attendance[d] === 'A' ? 'Н' : (s.grades[d] || '—')).join(',');
      csv += `"${s.name}","${s.code}","${s.teacher}","${s.controlLabel}",${gradesRow},${gpa},${attendanceRate}%,"${s.comment}"\n`;
    });

    const blob = new Blob(["\uFEFF" + csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `Ведомость_успеваемости_${activeStudent.name.replace(/\s+/g, '_')}_${state.selectedPeriod.replace(/\s+/g, '_')}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    showToast(`Выписка оценок студента ${activeStudent.name} успешно экспортирована в CSV!`);
  } else {
    let csv = `Студент,${state.dates.join(',')},Средний,Посещаемость,Комментарии\n`;
    state.students.forEach(s => {
      const { gpa, attendanceRate } = calculateStudentMetrics(s);
      const gradesRow = state.dates.map(d => s.attendance[d] === 'A' ? 'Н' : (s.grades[d] || '—')).join(',');
      csv += `"${s.name}",${gradesRow},${gpa},${attendanceRate}%,"${s.comment}"\n`;
    });

    const blob = new Blob(["\uFEFF" + csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `Ведомость_${state.selectedGroup}_${state.selectedSubject}_${state.selectedPeriod}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    showToast('Ведомость успешно экспортирована в CSV!');
  }
}

// ============================================================
// Material 3 Toast / Snackbar
// ============================================================
let toastTimeout = null;
function showToast(message) {
  let toast = document.getElementById('m3-toast');
  if (!toast) {
    toast = document.createElement('div');
    toast.id = 'm3-toast';
    toast.className = 'expressive-toast';
    document.body.appendChild(toast);
  }

  toast.innerHTML = `<span>&#10003;</span> ${message}`;
  
  // Re-trigger spring bounce animation
  toast.classList.remove('show');
  void toast.offsetWidth; // Force CSS reflow
  toast.classList.add('show');

  if (toastTimeout) clearTimeout(toastTimeout);
  toastTimeout = setTimeout(() => {
    toast.classList.remove('show');
  }, 3200);
}
