(function () {

  var SECTIONS = [
    {
      key: '',
      label: 'Home',
      href: 'index.html',
      pages: []
    },
    {
      key: 'intro',
      label: 'Introduction',
      href: 'intro/index.html',
      pages: []
    },
    {
      key: 'get-started',
      label: 'Get Started',
      href: 'get-started/index.html',
      pages: []
    },
    {
      key: 'mcp-clients',
      label: 'Connecting MCP Clients',
      href: 'mcp-clients/index.html',
      pages: []
    },
    {
      key: 'authentication',
      label: 'Authentication',
      href: 'authentication/index.html',
      pages: [
        { name: 'Auth0 Setup Guide', href: 'authentication/auth0/index.html' },
        { name: 'Keycloak Setup Guide', href: 'authentication/keycloak/index.html' }
      ]
    },
    {
      key: 'ingres',
      label: 'Actian Ingres',
      href: 'ingres/index.html',
      pages: [
        { name: 'Tools', href: 'ingres/tools/index.html' },
        { name: 'Resources', href: 'ingres/resources/index.html' },
        { name: 'Prompts', href: 'ingres/prompts/index.html' }
      ]
    },
    {
      key: 'hcl-informix',
      label: 'HCL Informix\u00ae',
      href: 'hcl-informix/index.html',
      pages: [
        { name: 'Tools', href: 'hcl-informix/tools/index.html' },
        { name: 'Resources', href: 'hcl-informix/resources/index.html' },
        { name: 'Prompts', href: 'hcl-informix/prompts/index.html' }
      ]
    },
    {
      key: 'zen',
      label: 'Actian Zen',
      href: 'zen/index.html',
      pages: [
        { name: 'Tools', href: 'zen/tools/index.html' },
        { name: 'Resources', href: 'zen/resources/index.html' },
        { name: 'Prompts', href: 'zen/prompts/index.html' }
      ]
    },
    {
      key: 'nosql',
      label: 'Actian NoSQL Database',
      href: 'nosql/index.html',
      pages: [
        { name: 'Authentication', href: 'nosql/authentication/index.html', pages: [
          { name: 'Auth0', href: 'nosql/authentication/auth0/index.html' },
          { name: 'Keycloak', href: 'nosql/authentication/keycloak/index.html' }
        ]},
        { name: 'Tools', href: 'nosql/tools/index.html' },
        { name: 'Resources', href: 'nosql/resources/index.html' },
        { name: 'Prompts', href: 'nosql/prompts/index.html' }
      ]
    },
    {
      key: 'analytics-engine',
      label: 'Actian Analytics Engine',
      href: 'analytics-engine/index.html',
      pages: [
        { name: 'Tools', href: 'analytics-engine/tools/index.html' },
        { name: 'Resources', href: 'analytics-engine/resources/index.html' },
        { name: 'Prompts', href: 'analytics-engine/prompts/index.html' }
      ]
    }
  ];

  // ── Helpers ───────────────────────────────────────────────────────────────

  function getSiteRoot() {
    var tab = document.querySelector('.md-tabs__link');
    if (tab && tab.href) {
      return tab.href.substring(0, tab.href.lastIndexOf('/') + 1);
    }
    return window.location.origin + '/';
  }

  function getSiteRootPath() {
    var tab = document.querySelector('.md-tabs__link');
    if (tab && tab.href) {
      var url  = new URL(tab.href);
      var path = url.pathname;
      var idx  = path.indexOf('/', 1);
      return idx !== -1 ? path.substring(0, idx + 1) : '/';
    }
    return '/';
  }

  function normHref(href) {
    return href
      .replace(/\/index\.html$/, '')
      .replace(/\.html$/, '')
      .replace(/\/$/, '');
  }

  // ── Active-state helpers ──────────────────────────────────────────────────

  function isHomePage(currentPath) {
    var root = getSiteRootPath();
    return (
      currentPath === root ||
      currentPath === root + 'index.html' ||
      currentPath === root.replace(/\/$/, '')
    );
  }

  function isSectionActive(currentPath, sectionKey) {
    if (!sectionKey) return isHomePage(currentPath);

    // Strip the site root so we match only from the first meaningful segment
    var root = getSiteRootPath();
    var relativePath = currentPath;
    if (relativePath.indexOf(root) === 0) {
      relativePath = relativePath.slice(root.length);
    } else if (root !== '/' && relativePath.indexOf(root.replace(/\/$/, '')) === 0) {
      relativePath = relativePath.slice(root.replace(/\/$/, '').length).replace(/^\//, '');
    }

    var pathSegs = relativePath.split('/').filter(Boolean).map(function(s) {
      return s.replace(/\.html$/, '');
    });
    var keySegs = sectionKey.split('/').filter(Boolean);

    // Anchor match to the start of the relative path — no scanning
    if (pathSegs.length < keySegs.length) return false;
    for (var i = 0; i < keySegs.length; i++) {
      if (pathSegs[i] !== keySegs[i]) return false;
    }
    return true;
  }

  function isPageActive(currentPath, href) {
    var norm = normHref(href);
    if (!norm) return false;

    var pathSegs = currentPath.split('/').filter(Boolean);
    var hrefSegs = norm.split('/').filter(Boolean);
    if (hrefSegs.length === 0) return false;

    outer:
    for (var s = 0; s <= pathSegs.length - hrefSegs.length; s++) {
      for (var i = 0; i < hrefSegs.length; i++) {
        var hs = hrefSegs[i].replace(/\.html$/, '');
        var ps = pathSegs[s + i].replace(/\.html$/, '');
        if (ps !== hs) continue outer;
      }
      return true;
    }
    return false;
  }

  function subtreeHasActive(pages, currentPath) {
    for (var i = 0; i < pages.length; i++) {
      if (isPageActive(currentPath, pages[i].href)) return true;
      if (pages[i].pages && subtreeHasActive(pages[i].pages, currentPath)) return true;
    }
    return false;
  }

  // ── Tab active-state ──────────────────────────────────────────────────────

  function getTabLabelText(tabLink) {
    var text = '';
    tabLink.childNodes.forEach(function (node) {
      if (node.nodeType === Node.TEXT_NODE) text += node.textContent;
    });
    text = text.trim();
    return text || (tabLink.textContent || '').trim();
  }

  function fixTabLinks() {
    var base        = getSiteRoot();
    var currentPath = window.location.pathname;

    var activeSectionKey = null;
    SECTIONS.forEach(function (section) {
      if (isSectionActive(currentPath, section.key)) {
        if (activeSectionKey === null || section.key.length > activeSectionKey.length) {
          activeSectionKey = section.key;
        }
      }
    });

    document.querySelectorAll('.md-tabs__item').forEach(function (tabItem) {
      var tabLink = tabItem.querySelector('.md-tabs__link');
      if (!tabLink) return;

      var labelText = getTabLabelText(tabLink);
      var section   = null;
      for (var i = 0; i < SECTIONS.length; i++) {
        if (SECTIONS[i].label === labelText) { section = SECTIONS[i]; break; }
      }

      if (section) {
        tabLink.href = base + section.href;
      }

      var isActive = section ? (section.key === activeSectionKey) : false;

      if (isActive) {
        tabItem.classList.add('md-tabs__item--active');
        tabLink.classList.add('md-tabs__link--active');
      } else {
        tabItem.classList.remove('md-tabs__item--active');
        tabLink.classList.remove('md-tabs__link--active');
      }
    });
  }

  // ── Sidebar builder ───────────────────────────────────────────────────────

  function buildPageList(pages, base, currentPath, depth) {
    var ul = document.createElement('ul');
    ul.className = 'cn-sublist cn-sublist--depth-' + depth;

    pages.forEach(function (page) {
      var li = document.createElement('li');
      li.className = 'cn-subitem';

      var hasChildren = page.pages && page.pages.length > 0;
      var pageActive  = isPageActive(currentPath, page.href);

      if (hasChildren) {
        var row = document.createElement('div');
        row.className = 'cn-subheader';

        var a = document.createElement('a');
        a.href        = base + page.href;
        a.className   = 'cn-sublink cn-sublink--parent' + (pageActive ? ' cn-sublink--active' : '');
        a.textContent = page.name;
        row.appendChild(a);

        var arrow = document.createElement('span');
        arrow.className = 'cn-arrow cn-arrow--sub';
        arrow.innerHTML = '&#8250;';

        var childList           = buildPageList(page.pages, base, currentPath, depth + 1);
        var anyDescendantActive = subtreeHasActive(page.pages, currentPath);
        var collapsed           = !(pageActive || anyDescendantActive);

        arrow.style.transform   = collapsed ? 'rotate(0deg)' : 'rotate(90deg)';
        childList.style.display = collapsed ? 'none'         : '';

        row.appendChild(arrow);
        li.appendChild(row);
        li.appendChild(childList);

        (function (arrowEl, listEl, initCollapsed) {
          var isCollapsed = initCollapsed;
          arrowEl.addEventListener('click', function (e) {
            e.preventDefault();
            e.stopPropagation();
            isCollapsed = !isCollapsed;
            listEl.style.display    = isCollapsed ? 'none'         : '';
            arrowEl.style.transform = isCollapsed ? 'rotate(0deg)' : 'rotate(90deg)';
          });
        })(arrow, childList, collapsed);

      } else {
        var a = document.createElement('a');
        a.href        = base + page.href;
        a.className   = 'cn-sublink' + (pageActive ? ' cn-sublink--active' : '');
        a.textContent = page.name;
        li.appendChild(a);
      }

      ul.appendChild(li);
    });

    return ul;
  }

  // ── Scroll to active link ─────────────────────────────────────────────────

  function scrollToActive(sidebar) {
    var activeLink = sidebar.querySelector('.cn-sublink--active, .cn-label--active');
    if (!activeLink) return;

    // Use scrollIntoView with 'nearest' so it only scrolls the minimum amount
    // needed to bring the active link into view — no overscrolling or centering.
    // 'instant' avoids any smooth-scroll animation fighting Material's own scroll.
    requestAnimationFrame(function () {
      if (activeLink.getBoundingClientRect().height > 0) {
        activeLink.scrollIntoView({ block: 'nearest', behavior: 'instant' });
      }
    });
  }

  // ── Main nav builder ──────────────────────────────────────────────────────

  function buildNav() {
    var sidebar = document.querySelector('.md-sidebar--primary .md-sidebar__scrollwrap');
    if (!sidebar) return;

    var currentPath = window.location.pathname;
    var base        = getSiteRoot();

    var nav = document.createElement('nav');
    nav.className = 'cn-nav';

    var activeSectionKey = null;
    SECTIONS.forEach(function (section) {
      if (isSectionActive(currentPath, section.key)) {
        if (activeSectionKey === null || section.key.length > activeSectionKey.length) {
          activeSectionKey = section.key;
        }
      }
    });

    SECTIONS.forEach(function (section) {
      var isActive = (section.key === activeSectionKey);

      var item = document.createElement('div');
      item.className = 'cn-item' + (isActive ? ' cn-item--active' : '');

      var header = document.createElement('div');
      header.className = 'cn-header';

      var link = document.createElement('a');
      link.href        = base + section.href;
      link.className   = 'cn-label' + (isActive ? ' cn-label--active' : '');
      link.textContent = section.label;
      header.appendChild(link);

      if (section.pages && section.pages.length > 0) {
        var arrow = document.createElement('span');
        arrow.className = 'cn-arrow';
        arrow.innerHTML = '&#8250;';

        var subList = buildPageList(section.pages, base, currentPath, 1);

        var collapsed = !isActive;
        arrow.style.transform = collapsed ? 'rotate(0deg)' : 'rotate(90deg)';
        subList.style.display = collapsed ? 'none' : '';

        header.appendChild(arrow);
        item.appendChild(header);
        item.appendChild(subList);

        (function (arrowEl, listEl, initCollapsed) {
          var isCollapsed = initCollapsed;
          arrowEl.addEventListener('click', function (e) {
            e.preventDefault();
            e.stopPropagation();
            isCollapsed = !isCollapsed;
            listEl.style.display    = isCollapsed ? 'none'         : '';
            arrowEl.style.transform = isCollapsed ? 'rotate(0deg)' : 'rotate(90deg)';
          });
        })(arrow, subList, collapsed);

      } else {
        item.appendChild(header);
      }

      nav.appendChild(item);
    });

    var nativeNav = sidebar.querySelector('.md-nav--primary');
    if (nativeNav) nativeNav.style.display = 'none';

    var inner = sidebar.querySelector('.md-sidebar__inner');
    if (inner) {
      var existing = inner.querySelector('.cn-nav');
      if (existing) {
        // Atomic swap — replaceChild removes old and inserts new in one DOM op,
        // so the sidebar is never left empty between redraws (no jump).
        inner.replaceChild(nav, existing);
      } else {
        inner.insertBefore(nav, inner.firstChild);
      }
    }

    scrollToActive(sidebar);
  }

  // ── Boot ──────────────────────────────────────────────────────────────────

  function init() {
    buildNav();
    fixTabLinks();
  }

  if (typeof document$ !== 'undefined') {
    document$.subscribe(init);
  } else if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

})();
