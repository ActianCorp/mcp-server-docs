// Custom navigation to show all sections in sidebar while keeping tabs
(function() {
  console.log('Comprehensive nav script loaded');
  
  function buildComprehensiveNav() {
    console.log('Building comprehensive navigation...');
    
    const sidebar = document.querySelector('.md-sidebar--primary .md-sidebar__scrollwrap');
    if (!sidebar) {
      console.error('Sidebar not found');
      return;
    }

    // Only run once
    if (sidebar.dataset.enhanced) {
      console.log('Already enhanced');
      return;
    }
    sidebar.dataset.enhanced = 'true';

    // Get all navigation tabs
    const tabs = document.querySelectorAll('.md-tabs__link');
    console.log(`Found ${tabs.length} tabs`);
    
    if (!tabs.length) {
      console.error('No tabs found');
      return;
    }

    // Create comprehensive navigation container
    const navContainer = document.createElement('nav');
    navContainer.className = 'md-nav md-nav--primary comprehensive-nav';
    navContainer.setAttribute('data-md-level', '0');

    const navList = document.createElement('ul');
    navList.className = 'md-nav__list';

    // Define which sections have subsections and their structure
    const sectionsWithSubs = {
      'analytics_engine': [
        { name: 'Tools', path: 'tools/index.html' },
        { name: 'Resources', path: 'resources/index.html' },
        { name: 'Prompts', path: 'prompts/index.html' }
      ],
      'ingres': [
        { name: 'Tools', path: 'tools/index.html' },
        { name: 'Resources', path: 'resources/index.html' },
        { name: 'Prompts', path: 'prompts/index.html' }
      ],
      'hcl_informix': [
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

    // Build navigation from tabs
    tabs.forEach((tab, index) => {
      const tabHref = tab.getAttribute('href');
      if (!tabHref || tabHref === '#') return;

      const tabText = tab.textContent.trim();
      
      // Extract section key from URL (handle both relative and absolute URLs)
      let sectionKey = tabHref;
      try {
        const url = new URL(tabHref, window.location.origin);
        const pathParts = url.pathname.split('/').filter(p => p);
        // Get the last meaningful part before index.html
        sectionKey = pathParts[pathParts.length - 1];
        if (sectionKey === 'index.html' && pathParts.length > 1) {
          sectionKey = pathParts[pathParts.length - 2];
        }
      } catch (e) {
        // Fallback for relative paths
        sectionKey = tabHref.replace('./', '').replace('/index.html', '').replace('.html', '');
      }
      
      const hasSubs = sectionKey in sectionsWithSubs;

      console.log(`Processing tab: ${tabText}, key: ${sectionKey}, has subs: ${hasSubs}`);

      const listItem = document.createElement('li');
      listItem.className = hasSubs ? 'md-nav__item md-nav__item--section' : 'md-nav__item';

      const currentPath = window.location.pathname;
      const isActive = currentPath.includes(sectionKey);

      if (hasSubs) {
        // Create toggle for sections with subsections
        const toggle = document.createElement('input');
        toggle.className = 'md-nav__toggle md-toggle';
        toggle.type = 'checkbox';
        toggle.id = `comprehensive-nav-${index}`;
        
        // Expand current section
        if (isActive) {
          toggle.checked = true;
        }

        const label = document.createElement('div');
        label.className = 'md-nav__link md-nav__link--index';
        
        // Create a link for the section name that navigates to the page
        const sectionLink = document.createElement('a');
        sectionLink.href = tabHref;
        sectionLink.textContent = tabText;
        sectionLink.style.flexGrow = '1';
        sectionLink.style.textDecoration = 'none';
        sectionLink.style.color = 'inherit';
        
        // Mark as active if on this section
        if (isActive) {
          sectionLink.classList.add('md-nav__link--active');
          label.classList.add('md-nav__link--active');
        }
        
        // Create toggle button for the arrow
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
        
        // Make label a flex container
        label.style.display = 'flex';
        label.style.alignItems = 'center';
        label.style.justifyContent = 'space-between';
        label.style.cursor = 'pointer';
        label.style.userSelect = 'none';

        // Create subsections navigation
        const subNav = document.createElement('nav');
        subNav.className = 'md-nav';
        subNav.setAttribute('data-md-level', '1');
        
        const subList = document.createElement('ul');
        subList.className = 'md-nav__list';
        
        // Get subsections for this section
        const subsections = sectionsWithSubs[sectionKey];
        
        subsections.forEach(subsection => {
          const subItem = document.createElement('li');
          subItem.className = 'md-nav__item';
          const subLink = document.createElement('a');
          subLink.className = 'md-nav__link';
          const basePath = tabHref.replace('index.html', '');
          subLink.href = basePath + subsection.path;
          subLink.textContent = subsection.name;
          
          // Mark as active if current page
          if (currentPath.includes(subsection.path)) {
            subLink.classList.add('md-nav__link--active');
          }
          
          subItem.appendChild(subLink);
          subList.appendChild(subItem);
        });
        
        subNav.appendChild(subList);

        // Add click handler to toggle button only
        toggleBtn.addEventListener('click', function(e) {
          console.log(`Toggle clicked on ${tabText}`);
          e.preventDefault();
          e.stopPropagation();
          
          toggle.checked = !toggle.checked;
          console.log(`Toggle state changed to: ${toggle.checked}`);
          
          // Manually toggle visibility and expanded class with !important
          if (toggle.checked) {
            subNav.style.setProperty('display', 'block', 'important');
            listItem.classList.add('expanded');
            toggleBtn.style.transform = 'rotate(90deg)';
            console.log(`Expanded ${tabText}`);
          } else {
            subNav.style.setProperty('display', 'none', 'important');
            listItem.classList.remove('expanded');
            toggleBtn.style.transform = 'rotate(0deg)';
            console.log(`Collapsed ${tabText}`);
          }
        }, true);
        
        // Set initial visibility and expanded class with !important
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
        // Simple link for sections without subsections
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

    // Replace or prepend to existing navigation
    const existingPrimaryNav = sidebar.querySelector('.md-nav--primary');
    if (existingPrimaryNav) {
      existingPrimaryNav.parentNode.insertBefore(navContainer, existingPrimaryNav);
      existingPrimaryNav.style.display = 'none';
      console.log('Navigation inserted before existing nav');
    } else {
      sidebar.prepend(navContainer);
      console.log('Navigation prepended to sidebar');
    }
  }

  // Try multiple initialization methods
  if (typeof document$ !== 'undefined') {
    // Material for MkDocs observable
    console.log('Using document$ subscription');
    document$.subscribe(buildComprehensiveNav);
  } else if (document.readyState === 'loading') {
    // Document still loading
    console.log('Using DOMContentLoaded event');
    document.addEventListener('DOMContentLoaded', buildComprehensiveNav);
  } else {
    // DOM already loaded
    console.log('DOM already loaded, running immediately');
    buildComprehensiveNav();
  }
})();
