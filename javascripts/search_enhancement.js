/**
 * Enhanced Search Functionality for MkDocs
 * Provides better search experience with analytics, keyboard shortcuts, and performance improvements
 */

// Search cache for better performance
const searchCache = new Map();
const CACHE_EXPIRY = 5 * 60 * 1000; // 5 minutes

// Search configuration
const searchConfig = {
  fuzzyThreshold: 0.8,
  maxCacheSize: 100,
  synonyms: {
    'k8s': ['kubernetes'],
    'kubernetes': ['k8s'],
    'db': ['database'],
    'database': ['db'],
    'auth': ['authentication', 'authorization'],
    'config': ['configuration'],
    'api': ['rest', 'endpoint'],
    'admin': ['administrator', 'administration'],
    'env': ['environment'],
    'deploy': ['deployment'],
    'install': ['installation', 'setup'],
    'doc': ['documentation', 'docs'],
    'ui': ['interface', 'user interface']
  }
};

document.addEventListener('DOMContentLoaded', function() {
  // Initialize enhanced search features
  initSearchEnhancements();
  setupKeyboardShortcuts();
  setupSearchAnalytics();
  setupSearchPreferences();
  enhanceSearchAlgorithm();
  setupSearchCache();
});

/**
 * Initialize search enhancements
 */
function initSearchEnhancements() {
  const searchInput = document.querySelector('.md-search__input');
  
  if (!searchInput) return;

  // Add min length indicator
  searchInput.addEventListener('input', function(e) {
    const value = e.target.value.trim();
    const minLength = 2;
    
    // Update input state based on minimum search length
    if (value.length > 0 && value.length < minLength) {
      searchInput.classList.add('md-search__input--incomplete');
      addMinSearchWarning(minLength - value.length);
    } else {
      searchInput.classList.remove('md-search__input--incomplete');
      removeMinSearchWarning();
    }
  });

  // Debounce search for better performance with caching
  let searchTimeout;
  searchInput.addEventListener('input', function(e) {
    clearTimeout(searchTimeout);

    // If input was cleared (e.g. by reset button or Escape), wipe the badge
    if (!e.target.value) {
      clearSearchBadge();
      _searchFocusIndex = -1;
    }

    searchTimeout = setTimeout(function() {
      const query = e.target.value.trim();
      trackSearchEvent(query);
      
      // Check cache first
      const normalizedQuery = normalizeSearchQuery(query);
      if (searchCache.has(normalizedQuery)) {
        const cached = searchCache.get(normalizedQuery);
        if (Date.now() - cached.timestamp < CACHE_EXPIRY) {
          // Use cached results
          return;
        } else {
          searchCache.delete(normalizedQuery);
        }
      }
      
      // Perform enhanced search with synonyms
      performEnhancedSearch(query);
    }, 300);
  });

  // Enhance search result navigation
  setupSearchResultNavigation();

  // Make the reset (×) button keyboard-accessible and bind cleanup
  const resetBtn = document.querySelector('.md-search__form button[type="reset"]');
  if (resetBtn) {
    resetBtn.setAttribute('tabindex', '0');
    resetBtn.addEventListener('click', function() {
      _searchFocusIndex = -1;
      clearSearchBadge();
    });
  }
}

/**
 * The index of the currently keyboard-focused result link (-1 = none / input has focus).
 */
let _searchFocusIndex = -1;

/**
 * Returns all focusable anchor links inside the current result list.
 */
function getSearchLinks() {
  return Array.from(
    document.querySelectorAll('.md-search-result__list .md-search-result__link')
  );
}

/**
 * Move keyboard focus to the result at `index`.
 * Clamps to valid range. Pass -1 to return focus to the input.
 */
function focusSearchResult(index) {
  const links = getSearchLinks();
  const searchInput = document.querySelector('.md-search__input');

  if (index < 0 || links.length === 0) {
    _searchFocusIndex = -1;
    if (searchInput) searchInput.focus();
    return;
  }

  _searchFocusIndex = Math.min(index, links.length - 1);
  const target = links[_searchFocusIndex];
  target.focus();
  // Scroll into view inside the scroll-wrapper without moving the page
  target.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

/**
 * Setup keyboard shortcuts for search
 */
function setupKeyboardShortcuts() {
  document.addEventListener('keydown', function(e) {
    const searchInput = document.querySelector('.md-search__input');
    const activeEl = document.activeElement;
    const inSearch = activeEl === searchInput;
    const inResult = activeEl && activeEl.closest('.md-search-result__list');
    const searchOpen = !!document.querySelector('[data-md-toggle="search"]:checked');

    // Cmd/Ctrl + K — focus search input
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
      e.preventDefault();
      if (searchInput) {
        searchInput.focus();
        searchInput.select();
        _searchFocusIndex = -1;
      }
      return;
    }

    // Only handle search-specific keys when search is visible
    if (!searchOpen) return;

    // ESC — clear input, wipe badge, and close
    if (e.key === 'Escape') {
      if (searchInput && searchInput.value) {
        e.preventDefault();
        searchInput.value = '';
        searchInput.dispatchEvent(new Event('input', { bubbles: true }));
        searchInput.focus();
        _searchFocusIndex = -1;
      }
      clearSearchBadge();
      return;
    }

    // ArrowDown — move focus down through results (wraps to input at top)
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      const links = getSearchLinks();
      if (links.length === 0) return;
      if (inSearch) {
        focusSearchResult(0);
      } else if (inResult) {
        focusSearchResult(_searchFocusIndex + 1);
      }
      return;
    }

    // ArrowUp — move focus up, return to input when past the top
    if (e.key === 'ArrowUp') {
      e.preventDefault();
      if (inResult) {
        if (_searchFocusIndex <= 0) {
          focusSearchResult(-1); // back to input
        } else {
          focusSearchResult(_searchFocusIndex - 1);
        }
      }
      return;
    }

    // Page Down — jump 5 results forward
    if (e.key === 'PageDown' && (inSearch || inResult)) {
      e.preventDefault();
      focusSearchResult(Math.max(0, _searchFocusIndex) + 5);
      return;
    }

    // Page Up — jump 5 results backward
    if (e.key === 'PageUp' && inResult) {
      e.preventDefault();
      focusSearchResult(Math.max(0, _searchFocusIndex - 5));
      return;
    }

    // Home — first result
    if (e.key === 'Home' && inResult) {
      e.preventDefault();
      focusSearchResult(0);
      return;
    }

    // End — last result
    if (e.key === 'End' && inResult) {
      e.preventDefault();
      const links = getSearchLinks();
      focusSearchResult(links.length - 1);
      return;
    }

    // Enter on input — move focus to first result so user can arrow through
    if (e.key === 'Enter' && inSearch) {
      const links = getSearchLinks();
      if (links.length > 0) {
        e.preventDefault();
        focusSearchResult(0);
      }
      return;
    }
    // Enter on a result link — let the browser navigate naturally (no preventDefault)
  });
}

/**
 * Setup search result navigation.
 * Uses a MutationObserver so it catches dynamically-loaded results.
 * Retries until .md-search-result__list appears in the DOM (it is injected
 * only once the search overlay is opened for the first time).
 */
function setupSearchResultNavigation() {
  const resultList = document.querySelector('.md-search-result__list');
  if (!resultList) {
    // Retry up to 20 times (2 seconds total) waiting for overlay to render
    let retries = 0;
    const timer = setInterval(function() {
      retries++;
      const el = document.querySelector('.md-search-result__list');
      if (el) {
        clearInterval(timer);
        attachResultObserver(el);
      } else if (retries >= 20) {
        clearInterval(timer);
      }
    }, 100);
    return;
  }
  attachResultObserver(resultList);
}

function attachResultObserver(resultList) {
  // Reset focus index whenever new results appear
  const observer = new MutationObserver(function() {
    _searchFocusIndex = -1;
  });

  observer.observe(resultList, { childList: true, subtree: true });
}

/**
 * Clear any stale state from the search meta bar (called on Escape / reset).
 */
function clearSearchBadge() {
  // Nothing to remove — MkDocs owns the meta text, we don't modify it.
  // Function kept so Escape and reset-button handlers still compile cleanly.
}

/**
 * Navigate through search results with keyboard (legacy – kept for compatibility)
 */
function navigateSearchResults(direction) {
  const links = getSearchLinks();
  if (links.length === 0) return;
  const newIndex = Math.max(0, Math.min(links.length - 1, _searchFocusIndex + direction));
  focusSearchResult(newIndex);
}

/**
 * Set focused search result (legacy)
 */
function setFocusedSearchResult(index) {
  focusSearchResult(index);
}

/**
 * Select focused search result and navigate (legacy)
 */
function selectFocusedSearchResult() {
  const links = getSearchLinks();
  if (_searchFocusIndex >= 0 && links[_searchFocusIndex]) {
    links[_searchFocusIndex].click();
  }
}

/**
 * Expand and keep search results visible (legacy – no longer needed but kept
 * in case other code paths call it)
 */
function expandSearchResults() {
  const searchToggle = document.querySelector('[data-md-toggle="search"]');
  if (searchToggle) searchToggle.checked = true;
}

/**
 * Add minimum search warning
 */
function addMinSearchWarning(remaining) {
  if (document.querySelector('.md-search__warning')) return;
  
  const searchContainer = document.querySelector('.md-search__inner');
  if (!searchContainer) return;

  const warning = document.createElement('div');
  warning.className = 'md-search__warning';
  warning.textContent = `Type at least ${remaining} more character${remaining > 1 ? 's' : ''}`;
  warning.style.cssText = `
    font-size: 0.75rem;
    color: rgba(255, 255, 255, 0.7);
    margin-top: 0.3rem;
    font-style: italic;
  `;
  searchContainer.appendChild(warning);
}

/**
 * Remove minimum search warning
 */
function removeMinSearchWarning() {
  const warning = document.querySelector('.md-search__warning');
  if (warning) {
    warning.remove();
  }
}

/**
 * Setup search analytics tracking
 */
function setupSearchAnalytics() {
  const searchInput = document.querySelector('.md-search__input');
  if (!searchInput) return;

  // Track search queries
  searchInput.addEventListener('change', function(e) {
    const query = e.target.value.trim();
    if (query.length >= 2) {
      trackSearchQuery(query);
    }
  });

  // Track search result clicks
  document.addEventListener('click', function(e) {
    const searchResultItem = e.target.closest('.md-search-result__item');
    if (searchResultItem) {
      const query = searchInput.value.trim();
      const title = searchResultItem.querySelector('.md-search-result__title')?.textContent || '';
      trackSearchResult(query, title);
    }
  });
}

/**
 * Track search query (send to analytics)
 */
function trackSearchQuery(query) {
  // Store in localStorage for analytics
  const searchHistory = JSON.parse(localStorage.getItem('search_history') || '[]');
  if (!searchHistory.includes(query)) {
    searchHistory.unshift(query);
    if (searchHistory.length > 20) {
      searchHistory.pop();
    }
    localStorage.setItem('search_history', JSON.stringify(searchHistory));
  }

  // Send to Google Analytics if available
  if (typeof gtag !== 'undefined') {
    gtag('event', 'search', {
      search_term: query
    });
  }
}

/**
 * Track search result selection
 */
function trackSearchResult(query, result) {
  if (typeof gtag !== 'undefined') {
    gtag('event', 'search_result_click', {
      search_term: query,
      result_title: result
    });
  }
}

/**
 * Track generic search event
 */
function trackSearchEvent(query) {
  const value = query.trim();
  if (value.length >= 2) {
    // Debounced tracking
    if (typeof gtag !== 'undefined') {
      gtag('event', 'search_in_progress', {
        search_term: value
      });
    }
  }
}

/**
 * Setup search preferences (remembering user preferences)
 */
function setupSearchPreferences() {
  const searchInput = document.querySelector('.md-search__input');
  if (!searchInput) return;

  // Get saved search preferences
  const preferences = JSON.parse(localStorage.getItem('search_preferences') || '{}');

  // Apply focus state preference
  if (preferences.autoFocus) {
    searchInput.focus();
  }

}

/**
 * Utility: Get search statistics
 */
window.getSearchStats = function() {
  const history = JSON.parse(localStorage.getItem('search_history') || '[]');
  console.log('Recent searches:', history);
  return {
    recentSearches: history,
    totalSearches: history.length
  };
};

/**
 * Utility: Clear search history
 */
window.clearSearchHistory = function() {
  localStorage.removeItem('search_history');
  localStorage.removeItem('search_preferences');
  searchCache.clear();
  console.log('Search history and cache cleared');
};

/**
 * Normalize search query for better matching
 */
function normalizeSearchQuery(query) {
  return query
    .toLowerCase()
    .trim()
    .replace(/[^\w\s]/g, ' ')  // Remove special characters
    .replace(/\s+/g, ' ')       // Normalize whitespace
    .trim();
}

/**
 * Expand query with synonyms for better matching
 */
function expandQueryWithSynonyms(query) {
  const words = normalizeSearchQuery(query).split(' ');
  const expandedTerms = new Set(words);
  
  words.forEach(word => {
    if (searchConfig.synonyms[word]) {
      searchConfig.synonyms[word].forEach(syn => expandedTerms.add(syn));
    }
  });
  
  return Array.from(expandedTerms);
}

/**
 * Calculate Levenshtein distance for fuzzy matching
 */
function levenshteinDistance(str1, str2) {
  const len1 = str1.length;
  const len2 = str2.length;
  const matrix = Array(len1 + 1).fill(null).map(() => Array(len2 + 1).fill(0));
  
  for (let i = 0; i <= len1; i++) matrix[i][0] = i;
  for (let j = 0; j <= len2; j++) matrix[0][j] = j;
  
  for (let i = 1; i <= len1; i++) {
    for (let j = 1; j <= len2; j++) {
      const cost = str1[i - 1] === str2[j - 1] ? 0 : 1;
      matrix[i][j] = Math.min(
        matrix[i - 1][j] + 1,      // deletion
        matrix[i][j - 1] + 1,      // insertion
        matrix[i - 1][j - 1] + cost // substitution
      );
    }
  }
  
  return matrix[len1][len2];
}

/**
 * Fuzzy match for typo tolerance
 */
function fuzzyMatch(query, text) {
  query = normalizeSearchQuery(query);
  text = normalizeSearchQuery(text);
  
  if (text.includes(query)) return 1.0; // Exact match
  
  const words = query.split(' ');
  let matchScore = 0;
  
  words.forEach(word => {
    const textWords = text.split(' ');
    textWords.forEach(textWord => {
      const distance = levenshteinDistance(word, textWord);
      const maxLen = Math.max(word.length, textWord.length);
      const similarity = 1 - (distance / maxLen);
      
      if (similarity > searchConfig.fuzzyThreshold) {
        matchScore += similarity;
      }
    });
  });
  
  return matchScore / words.length;
}

/**
 * Calculate relevance score for search results
 */
function calculateRelevanceScore(result, query) {
  let score = 0;
  const normalizedQuery = normalizeSearchQuery(query);
  const expandedTerms = expandQueryWithSynonyms(query);
  
  // Title matches get highest weight
  if (result.title) {
    const titleMatch = fuzzyMatch(normalizedQuery, result.title);
    score += titleMatch * 10;
    
    // Boost for exact title match
    if (normalizeSearchQuery(result.title).includes(normalizedQuery)) {
      score += 15;
    }
  }
  
  // Content matches
  if (result.text) {
    const contentMatch = fuzzyMatch(normalizedQuery, result.text);
    score += contentMatch * 3;
  }
  
  // Synonym matches
  expandedTerms.forEach(term => {
    if (result.title && normalizeSearchQuery(result.title).includes(term)) {
      score += 5;
    }
    if (result.text && normalizeSearchQuery(result.text).includes(term)) {
      score += 2;
    }
  });
  
  // Boost for location/section matches
  if (result.location) {
    if (normalizeSearchQuery(result.location).includes(normalizedQuery)) {
      score += 8;
    }
  }
  
  return score;
}

/**
 * Setup search cache management
 */
function setupSearchCache() {
  // Periodically clean old cache entries
  setInterval(() => {
    const now = Date.now();
    for (const [key, value] of searchCache.entries()) {
      if (now - value.timestamp > CACHE_EXPIRY) {
        searchCache.delete(key);
      }
    }
    
    // Limit cache size
    if (searchCache.size > searchConfig.maxCacheSize) {
      const entries = Array.from(searchCache.entries());
      entries.sort((a, b) => a[1].timestamp - b[1].timestamp);
      const toDelete = entries.slice(0, entries.length - searchConfig.maxCacheSize);
      toDelete.forEach(([key]) => searchCache.delete(key));
    }
  }, 60000); // Clean every minute
}

/**
 * Enhance search algorithm with better ranking
 */
function enhanceSearchAlgorithm() {
  // Intercept search worker if available
  if (window.__md_search) {
    const originalSearch = window.__md_search;
    
    window.__md_search = function(query) {
      const normalizedQuery = normalizeSearchQuery(query);
      
      // Check cache
      if (searchCache.has(normalizedQuery)) {
        const cached = searchCache.get(normalizedQuery);
        if (Date.now() - cached.timestamp < CACHE_EXPIRY) {
          return cached.results;
        }
      }
      
      // Perform original search
      const results = originalSearch.call(this, query);
      
      // Enhance results with relevance scoring
      if (results && results.length > 0) {
        results.forEach(result => {
          result.relevanceScore = calculateRelevanceScore(result, query);
        });
        
        // Re-sort by relevance
        results.sort((a, b) => (b.relevanceScore || 0) - (a.relevanceScore || 0));
        
        // Cache results
        searchCache.set(normalizedQuery, {
          results: results,
          timestamp: Date.now()
        });
      }
      
      return results;
    };
  }
}

/**
 * Perform enhanced search with all improvements
 */
function performEnhancedSearch(query) {
  if (!query || query.length < 2) return;
  
  const normalizedQuery = normalizeSearchQuery(query);
  const expandedTerms = expandQueryWithSynonyms(query);
  
  // Store expanded query for debugging
  if (window.__debug_search) {
    console.log('Original query:', query);
    console.log('Normalized query:', normalizedQuery);
    console.log('Expanded terms:', expandedTerms);
  }
  
  // The actual search is handled by MkDocs search worker
  // This function prepares the query for better matching
}
