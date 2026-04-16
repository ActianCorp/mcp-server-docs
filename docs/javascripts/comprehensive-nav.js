(function() {
  console.log('Comprehensive nav script loaded');
  
  function buildComprehensiveNav() {
    console.log('Building comprehensive navigation...');
    
    const sidebar = document.querySelector('.md-sidebar--primary .md-sidebar__scrollwrap');
    if (!sidebar) {
      console.error('Sidebar not found');
      return;
    }

    if (sidebar.dataset.enhanced) {
      console.log('Already enhanced');
      return;
    }
    sidebar.dataset.enhanced = 'true';

    const tabs = document.querySelectorAll('.md-tabs__link');
    console.log(`Found ${tabs.length} tabs`);
    
    if (!tabs.length) {
      console.error('No tabs found');
      return;
    }

    const navContainer = document.createElement('nav');
    navContainer.className = 'md-nav md-nav--primary comprehensive-nav';
    navContainer.setAttribute('data-md-level', '0');

    const navList = document.createElement('ul');
    navList.className = 'md-nav__list';

    const sectionsWithSubs = {
      'analytics-engine': [
        { name: 'Tools', path: 'tools/index.html' },
        { name: 'Resources', path: 'resources/index.html' },
        { name: 'Prompts', path: 'prompts/index.html' }
      ],
      'ingres': [
        { name: 'Tools', path: 'tools/index.html' },
        { name: 'Resources', path: 'resources/index.html' },
        { name: 'Prompts', path: 'prompts/index.html' }
      ],
      'hcl-informix': [
        { name: 'Tools', path: 'tools/index.html' },
        { name: 'Resources', path: 'resources/index.html' },
        { name: 'Prompts', path: 'prompts/index.html' }
      ],
      'nosql': [
        { name: 'Authentication', path: 'authentication/index.html' },
        { name: 'Tools', path: 'tools/index.html' },
        { name: 'Resources', path: 'resources/index.html' },
        { name: 'Prompts', path: 'prompts/index.html' }
      ],
      'zen': [
        { name: 'Tools', path: 'tools/index.html' },
        { name: 'Resources', path: 'resources/index.html' },
        { name: 'Prompts', path: 'prompts/index.html' }
      ],
      'authentication': [
        { name: 'Auth0', path: 'auth0/index.html' },
        { name: 'Keycloak', path: 'keycloak/index.html' }
      ]
    };

    const currentPath = window.location.pathname;

    // Detect the site root by resolving the first tab (Home) base path
    // e.g. if served from /site/, siteRoot = '/site/'
    let siteRoot = '/';
    try {
      const firstTab = document.querySelector('.md-tabs__link');
      if (firstTab) {
        const firstUrl = new URL(firstTab.getAttribute('href'), window.location.origin);
        siteRoot = firstUrl.pathname.replace(/index\.html$/, '');
      }
    } catch(e) {}

    console.log('Detected siteRoot:', siteRoot);

    tabs.forEach((tab, index) => {
      const tabHref = tab.getAttribute('href');
      if (!tabHref || tabHref === '#') return;

      const tabText = tab.textContent.trim();
      
      let sectionKey = tabHref;
      let sectionBasePath = '';

      try {
        const url = new URL(tabHref, window.location.origin);
        sectionBasePath = url.pathname.replace(/index\.html$/, '');
        const pathParts = url.pathname.split('/').filter(p => p);
        sectionKey = pathParts[pathParts.length - 1];
        if (sectionKey === 'index.html' && pathParts.length > 1) {
          sectionKey = pathParts[pathParts.length - 2];
        }
      } catch (e) {
        sectionKey = tabHref.replace('./', '').replace('/index.html', '').replace('.html', '');
        sectionBasePath = '/' + sectionKey + '/';
      }
      
      const hasSubs = sectionKey in sectionsWithSubs;

      // FIXED: If this tab's basePath is exactly the siteRoot, it's the Home tab.
      // Use exact match so it only highlights on the root page, not every page.
      const isHomeTab = sectionBasePath === siteRoot;
      const isActive = isHomeTab
        ? currentPath === siteRoot || currentPath === siteRoot + 'index.html'
        : currentPath.startsWith(sectionBasePath);

      console.log(`Processing tab: ${tabText}, key: ${sectionKey}, basePath: ${sectionBasePath}, isActive: ${isActive}`);

      const listItem = document.createElement('li');
      listItem.className = hasSubs ? 'md-nav__item md-nav__item--section' : 'md-nav__item';

      if (hasSubs) {
        const toggle = document.createElement('input');
        toggle.className = 'md-nav__toggle md-toggle';
        toggle.type = 'checkbox';
        toggle.id = `comprehensive-nav-${index}`;
        
        if (isActive) {
          toggle.checked = true;
        }

        const label = document.createElement('div');
        label.className = 'md-nav__link md-nav__link--index';
        
        const sectionLink = document.createElement('a');
        sectionLink.href = tabHref;
        sectionLink.textContent = tabText;
        sectionLink.style.flexGrow = '1';
        sectionLink.style.textDecoration = 'none';
        sectionLink.style.color = 'inherit';
        
        if (isActive) {
          sectionLink.classList.add('md-nav__link--active');
          label.classList.add('md-nav__link--active');
        }
        
        const toggleBtn = document.createElement('span');
        toggleBtn.className = 'nav-toggle-btn';
        toggleBtn.style.cursor = 'pointer';
        toggleBtn.style.padding = '0';
        toggleBtn.style.margin = '0';
        toggleBtn.style.marginLeft = '0.25rem';
        toggleBtn.innerHTML = '›';
        toggleBtn.style.fontSize = '1rem';
        toggleBtn.style.transition = 'transform 0.25s';
        toggleBtn.style.display = 'inline-flex';
        toggleBtn.style.alignItems = 'center';
        toggleBtn.style.justifyContent = 'center';
        toggleBtn.style.userSelect = 'none';
        toggleBtn.style.lineHeight = '1';
        toggleBtn.style.width = '1rem';
        toggleBtn.style.height = '1rem';
        toggleBtn.style.flexShrink = '0';
        
        label.appendChild(sectionLink);
        label.appendChild(toggleBtn);
        
        label.style.display = 'flex';
        label.style.alignItems = 'center';
        label.style.justifyContent = 'space-between';
        label.style.cursor = 'pointer';
        label.style.userSelect = 'none';

        const subNav = document.createElement('nav');
        subNav.className = 'md-nav';
        subNav.setAttribute('data-md-level', '1');
        
        const subList = document.createElement('ul');
        subList.className = 'md-nav__list';
        
        const subsections = sectionsWithSubs[sectionKey];
        
        subsections.forEach(subsection => {
          const subItem = document.createElement('li');
          subItem.className = 'md-nav__item';
          const subLink = document.createElement('a');
          subLink.className = 'md-nav__link';
          const basePath = tabHref.replace('index.html', '');
          subLink.href = basePath + subsection.path;
          subLink.textContent = subsection.name;
          
          try {
            const subUrl = new URL(basePath + subsection.path, window.location.origin);
            const subBasePath = subUrl.pathname.replace(/index\.html$/, '');
            if (currentPath.startsWith(subBasePath)) {
              subLink.classList.add('md-nav__link--active');
            }
          } catch (e) {
            const subSegment = subsection.path.replace('/index.html', '');
            if (
              currentPath.includes('/' + subSegment + '/') ||
              currentPath.endsWith('/' + subSegment)
            ) {
              subLink.classList.add('md-nav__link--active');
            }
          }
          
          subItem.appendChild(subLink);
          subList.appendChild(subItem);
        });
        
        subNav.appendChild(subList);

        toggleBtn.addEventListener('click', function(e) {
          console.log(`Toggle clicked on ${tabText}`);
          e.preventDefault();
          e.stopPropagation();
          
          toggle.checked = !toggle.checked;
          
          if (toggle.checked) {
            subNav.style.setProperty('display', 'block', 'important');
            listItem.classList.add('expanded');
            toggleBtn.style.transform = 'rotate(90deg)';
          } else {
            subNav.style.setProperty('display', 'none', 'important');
            listItem.classList.remove('expanded');
            toggleBtn.style.transform = 'rotate(0deg)';
          }
        }, true);
        
        if (isActive) {
          subNav.style.setProperty('display', 'block', 'important');
          listItem.classList.add('expanded');
          toggle.checked = true;
          toggleBtn.style.transform = 'rotate(90deg)';
        } else {
          subNav.style.setProperty('display', 'none', 'important');
          toggle.checked = false;
          toggleBtn.style.transform = 'rotate(0deg)';
        }

        listItem.appendChild(toggle);
        listItem.appendChild(label);
        listItem.appendChild(subNav);
      } else {
        const link = document.createElement('a');
        link.className = 'md-nav__link';
        link.href = tabHref;
        link.textContent = tabText;
        
        if (isActive) {
          link.classList.add('md-nav__link--active');
        }
        
        listItem.appendChild(link);
      }

      navList.appendChild(listItem);
    });

    navContainer.appendChild(navList);
    console.log('Navigation structure built');

    const existingPrimaryNav = sidebar.querySelector('.md-nav--primary');
    if (existingPrimaryNav) {
      existingPrimaryNav.parentNode.insertBefore(navContainer, existingPrimaryNav);
      existingPrimaryNav.style.display = 'none';
    } else {
      sidebar.prepend(navContainer);
    }
  }

  if (typeof document$ !== 'undefined') {
    console.log('Using document$ subscription');
    document$.subscribe(buildComprehensiveNav);
  } else if (document.readyState === 'loading') {
    console.log('Using DOMContentLoaded event');
    document.addEventListener('DOMContentLoaded', buildComprehensiveNav);
  } else {
    console.log('DOM already loaded, running immediately');
    buildComprehensiveNav();
  }
})();