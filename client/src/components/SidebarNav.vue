<!-- ABOUTME: Collapsible dark sidebar navigation for the SaaS-style layout.
     ABOUTME: Contains logo, nav links with icons, language switcher, profile menu, and collapse toggle. -->
<template>
  <aside class="sidebar" :class="{ collapsed: isCollapsed }">
    <div class="sidebar-header">
      <div class="sidebar-logo">
        <div class="logo-icon">
          <svg width="32" height="32" viewBox="0 0 32 32" fill="none">
            <rect width="32" height="32" rx="8" fill="#3b82f6"/>
            <path d="M9 16L13 12L17 16L23 10" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M9 21L13 17L17 21L23 15" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" opacity="0.5"/>
          </svg>
        </div>
        <div v-show="!isCollapsed" class="logo-text">
          <span class="logo-name">{{ t('nav.companyName') }}</span>
          <span class="logo-subtitle">{{ t('nav.subtitle') }}</span>
        </div>
      </div>
    </div>

    <nav class="sidebar-nav">
      <router-link
        v-for="item in navItems"
        :key="item.path"
        :to="item.path"
        class="nav-item"
        :class="{ active: isActive(item.path) }"
        :title="isCollapsed ? item.label : ''"
      >
        <span class="nav-icon" v-html="item.icon"></span>
        <span v-show="!isCollapsed" class="nav-label">{{ item.label }}</span>
      </router-link>
    </nav>

    <div class="sidebar-footer">
      <div v-show="!isCollapsed" class="footer-item language-item">
        <LanguageSwitcher />
      </div>

      <div class="footer-item profile-item">
        <ProfileMenu
          @show-profile-details="$emit('show-profile-details')"
          @show-tasks="$emit('show-tasks')"
        />
      </div>

      <button
        class="collapse-toggle"
        @click="toggleCollapse"
        :title="isCollapsed ? t('nav.expandSidebar') : t('nav.collapseSidebar')"
      >
        <svg
          width="20"
          height="20"
          viewBox="0 0 20 20"
          fill="none"
          class="collapse-chevron"
          :class="{ flipped: isCollapsed }"
        >
          <path d="M12 4L6 10L12 16" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        <span v-show="!isCollapsed" class="collapse-text">{{ t('nav.collapseSidebar') }}</span>
      </button>
    </div>
  </aside>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from '../composables/useI18n'
import LanguageSwitcher from './LanguageSwitcher.vue'
import ProfileMenu from './ProfileMenu.vue'

const COLLAPSED_KEY = 'sidebar-collapsed'

export default {
  name: 'SidebarNav',
  components: {
    LanguageSwitcher,
    ProfileMenu
  },
  emits: ['show-profile-details', 'show-tasks', 'update:collapsed'],
  setup(props, { emit }) {
    const route = useRoute()
    const { t } = useI18n()
    const isCollapsed = ref(false)

    onMounted(() => {
      const saved = localStorage.getItem(COLLAPSED_KEY)
      if (saved !== null) {
        isCollapsed.value = saved === 'true'
      } else if (window.innerWidth < 1024) {
        isCollapsed.value = true
      }
      emit('update:collapsed', isCollapsed.value)
    })

    const toggleCollapse = () => {
      isCollapsed.value = !isCollapsed.value
      localStorage.setItem(COLLAPSED_KEY, String(isCollapsed.value))
      emit('update:collapsed', isCollapsed.value)
    }

    const isActive = (path) => {
      if (path === '/') return route.path === '/'
      return route.path.startsWith(path)
    }

    const navItems = computed(() => [
      {
        path: '/',
        label: t('nav.overview'),
        icon: '<svg width="20" height="20" viewBox="0 0 20 20" fill="none"><path d="M3 10L10 3L17 10" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/><path d="M5 8.5V16H8.5V12H11.5V16H15V8.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>'
      },
      {
        path: '/inventory',
        label: t('nav.inventory'),
        icon: '<svg width="20" height="20" viewBox="0 0 20 20" fill="none"><rect x="3" y="3" width="14" height="14" rx="2" stroke="currentColor" stroke-width="1.5"/><path d="M3 8H17" stroke="currentColor" stroke-width="1.5"/><path d="M8 8V17" stroke="currentColor" stroke-width="1.5"/></svg>'
      },
      {
        path: '/orders',
        label: t('nav.orders'),
        icon: '<svg width="20" height="20" viewBox="0 0 20 20" fill="none"><path d="M6 2L3 6V17C3 17.5523 3.44772 18 4 18H16C16.5523 18 17 17.5523 17 17V6L14 2H6Z" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/><path d="M3 6H17" stroke="currentColor" stroke-width="1.5"/><path d="M13 10C13 11.6569 11.6569 13 10 13C8.34315 13 7 11.6569 7 10" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>'
      },
      {
        path: '/spending',
        label: t('nav.finance'),
        icon: '<svg width="20" height="20" viewBox="0 0 20 20" fill="none"><path d="M10 2V18" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/><path d="M14 5H8C6.34315 5 5 6.34315 5 8C5 9.65685 6.34315 11 8 11H12C13.6569 11 15 12.3431 15 14C15 15.6569 13.6569 17 12 17H6" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>'
      },
      {
        path: '/demand',
        label: t('nav.demandForecast'),
        icon: '<svg width="20" height="20" viewBox="0 0 20 20" fill="none"><path d="M3 17L7.5 11L11 14L17 3" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/><path d="M14 3H17V6" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>'
      },
      {
        path: '/restocking',
        label: t('nav.restocking'),
        icon: '<svg width="20" height="20" viewBox="0 0 20 20" fill="none"><path d="M3 10H17" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/><path d="M3 6H17" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/><path d="M3 14H11" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/><path d="M14 13L16 15L19 12" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>'
      },
      {
        path: '/reports',
        label: t('nav.reports'),
        icon: '<svg width="20" height="20" viewBox="0 0 20 20" fill="none"><path d="M4 3H12L16 7V17C16 17.5523 15.5523 18 15 18H4C3.44772 18 3 17.5523 3 17V4C3 3.44772 3.44772 3 4 3Z" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/><path d="M12 3V7H16" stroke="currentColor" stroke-width="1.5"/><path d="M7 11H13" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/><path d="M7 14H10" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>'
      }
    ])

    return {
      t,
      isCollapsed,
      toggleCollapse,
      isActive,
      navItems
    }
  }
}
</script>

<style scoped>
.sidebar {
  width: var(--sidebar-width);
  min-width: var(--sidebar-width);
  height: 100vh;
  background: var(--sidebar-bg);
  display: flex;
  flex-direction: column;
  position: sticky;
  top: 0;
  transition: width var(--transition-normal), min-width var(--transition-normal);
  overflow: hidden;
  z-index: 100;
}

.sidebar.collapsed {
  width: var(--sidebar-collapsed-width);
  min-width: var(--sidebar-collapsed-width);
}

/* Header / Logo */
.sidebar-header {
  padding: var(--space-md);
  border-bottom: 1px solid var(--sidebar-border);
  min-height: 70px;
  display: flex;
  align-items: center;
}

.sidebar-logo {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  min-height: 36px;
  overflow: hidden;
}

.logo-icon {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.logo-text {
  display: flex;
  flex-direction: column;
  overflow: hidden;
  white-space: nowrap;
}

.logo-name {
  font-size: var(--text-sm);
  font-weight: 700;
  color: var(--sidebar-text-active);
  line-height: 1.2;
}

.logo-subtitle {
  font-size: var(--text-xs);
  color: var(--sidebar-text);
  line-height: 1.3;
}

/* Navigation links */
.sidebar-nav {
  flex: 1;
  overflow-y: auto;
  padding: var(--space-sm);
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  padding: 10px 12px;
  border-radius: 6px;
  color: var(--sidebar-text);
  text-decoration: none;
  font-size: var(--text-sm);
  font-weight: 500;
  transition: all var(--transition-fast);
  white-space: nowrap;
  position: relative;
}

.nav-item:hover {
  background: var(--sidebar-hover-bg);
  color: var(--sidebar-text-active);
}

.nav-item.active {
  background: rgba(59, 130, 246, 0.15);
  color: #60a5fa;
}

.nav-item.active::before {
  content: '';
  position: absolute;
  left: 0;
  top: 6px;
  bottom: 6px;
  width: 3px;
  border-radius: 0 3px 3px 0;
  background: var(--sidebar-accent);
}

.nav-icon {
  flex-shrink: 0;
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.nav-icon :deep(svg) {
  display: block;
}

.nav-label {
  overflow: hidden;
  text-overflow: ellipsis;
}

/* Collapsed state: center nav items */
.sidebar.collapsed .nav-item {
  justify-content: center;
  padding: 10px;
}

/* Footer */
.sidebar-footer {
  border-top: 1px solid var(--sidebar-border);
  padding: var(--space-sm);
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
}

.footer-item {
  display: flex;
  align-items: center;
}

/* Override LanguageSwitcher for dark sidebar */
.sidebar :deep(.language-switcher) {
  width: 100%;
}

.sidebar :deep(.language-button) {
  background: transparent;
  border-color: var(--sidebar-border);
  color: var(--sidebar-text);
  width: 100%;
  justify-content: flex-start;
}

.sidebar :deep(.language-button:hover) {
  background: var(--sidebar-hover-bg);
  border-color: var(--sidebar-hover-bg);
  color: var(--sidebar-text-active);
}

.sidebar :deep(.language-button .globe-icon) {
  color: var(--sidebar-text);
}

.sidebar :deep(.language-button .chevron) {
  color: var(--sidebar-text);
}

/* Language dropdown opens upward in sidebar */
.sidebar :deep(.language-switcher .dropdown-menu) {
  bottom: 100%;
  top: auto;
  margin-bottom: 0.5rem;
  left: 0;
  right: auto;
}

/* Override ProfileMenu for dark sidebar */
.sidebar :deep(.profile-menu) {
  width: 100%;
}

.sidebar :deep(.profile-button) {
  background: transparent;
  border-color: var(--sidebar-border);
  color: var(--sidebar-text);
  width: 100%;
  justify-content: flex-start;
}

.sidebar :deep(.profile-button:hover) {
  background: var(--sidebar-hover-bg);
  border-color: var(--sidebar-hover-bg);
}

.sidebar :deep(.profile-name) {
  color: var(--sidebar-text-active);
}

.sidebar :deep(.profile-button .chevron) {
  color: var(--sidebar-text);
}

/* Profile dropdown opens upward in sidebar */
.sidebar :deep(.profile-menu .dropdown-menu) {
  bottom: 100%;
  top: auto;
  margin-bottom: 0.5rem;
  left: 0;
  right: auto;
}

/* Collapsed: hide text in profile, center avatar */
.sidebar.collapsed :deep(.profile-button) {
  justify-content: center;
  padding: 0.5rem;
}

.sidebar.collapsed :deep(.profile-name),
.sidebar.collapsed :deep(.profile-button .chevron) {
  display: none;
}

/* Collapse toggle button */
.collapse-toggle {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  padding: 10px 12px;
  border-radius: 6px;
  background: none;
  border: none;
  color: var(--sidebar-text);
  font-size: var(--text-sm);
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition-fast);
  font-family: inherit;
  white-space: nowrap;
  width: 100%;
}

.collapse-toggle:hover {
  background: var(--sidebar-hover-bg);
  color: var(--sidebar-text-active);
}

.collapse-chevron {
  flex-shrink: 0;
  transition: transform var(--transition-normal);
}

.collapse-chevron.flipped {
  transform: rotate(180deg);
}

.collapse-text {
  overflow: hidden;
  text-overflow: ellipsis;
}

/* Collapsed: center the toggle */
.sidebar.collapsed .collapse-toggle {
  justify-content: center;
  padding: 10px;
}

/* Responsive: default to collapsed on small screens */
@media (max-width: 1023px) {
  .sidebar:not(.collapsed) {
    width: var(--sidebar-collapsed-width);
    min-width: var(--sidebar-collapsed-width);
  }
}
</style>
