/**
 * Smart Search functionality for ILDMS
 * Handles text highlighting and navigation within document content
 */

class SmartSearch {
    constructor(searchQuery, searchTerms) {
        this.currentIndex = 0;
        this.matches = [];
        this.markInstance = null;
        this.searchQuery = searchQuery || '';
        this.searchTerms = searchTerms || [];
        
        if (this.searchQuery) {
            this.init();
        }
    }
    
    init() {
        // Wait for page to fully load
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.performInit());
        } else {
            this.performInit();
        }
    }
    
    performInit() {
        // Initialize Mark.js on content areas with more comprehensive selectors
        const contentSelectors = [
            '.document-content',
            '.transcript-content', 
            '.word-document-content',
            '#pdf-viewer',
            '.card-body',
            'p',
            'div',
            'span',
            '.alert',
            '[class*="content"]'
        ];
        
        const contentElements = [];
        
        // Find all elements that contain actual text content
        document.querySelectorAll('*').forEach(el => {
            // Skip script, style, and other non-content elements
            if (['SCRIPT', 'STYLE', 'META', 'LINK', 'HEAD'].includes(el.tagName)) {
                return;
            }
            
            // Check if element has direct text content (not just from children)
            const textContent = this.getDirectTextContent(el);
            if (textContent && textContent.trim().length > 10) {
                contentElements.push(el);
            }
        });
        
        console.log(`Smart Search: Found ${contentElements.length} content elements to search`);
        
        if (contentElements.length > 0) {
            this.highlightMatches(contentElements);
            this.setupNavigation();
        } else {
            console.warn('Smart Search: No content elements found for search highlighting');
        }
    }
    
    getDirectTextContent(element) {
        // Get only the direct text content, not from child elements
        let text = '';
        for (let node of element.childNodes) {
            if (node.nodeType === Node.TEXT_NODE) {
                text += node.textContent;
            }
        }
        return text;
    }
    
    hasTextContent(element) {
        return element.textContent && element.textContent.trim().length > 0;
    }
    
    highlightMatches(elements) {
        let totalHighlighted = 0;
        const processedElements = new Set();
        
        // Process each element
        elements.forEach(element => {
            if (!element || processedElements.has(element)) return;
            processedElements.add(element);
            
            const markInstance = new Mark(element);
            
            // First, try to mark individual search terms
            if (this.searchTerms && this.searchTerms.length > 0) {
                this.searchTerms.forEach(term => {
                    if (term && term.trim()) {
                        markInstance.mark(term.trim(), {
                            className: 'search-highlight',
                            separateWordSearch: false,
                            accuracy: {
                                'value': 'partially',
                                'limiters': [',', '.', ':', ';', '!', '?', '-', '(', ')']
                            },
                            ignoreJoiners: true,
                            wildcards: 'enabled',
                            caseSensitive: false,
                            ignorePunctuation: [',', '.', ':', ';', '!', '?', '-', '(', ')'],
                            done: (totalMarks) => {
                                totalHighlighted += totalMarks;
                                console.log(`Marked "${term}": ${totalMarks} matches`);
                                this.updateMatches();
                            }
                        });
                    }
                });
            }
            
            // Fallback: if no specific terms or no matches, try the full query
            if (this.searchTerms.length === 0 && this.searchQuery) {
                markInstance.mark(this.searchQuery, {
                    className: 'search-highlight',
                    separateWordSearch: true,
                    accuracy: 'partially',
                    caseSensitive: false,
                    done: (totalMarks) => {
                        totalHighlighted += totalMarks;
                        console.log(`Marked full query "${this.searchQuery}": ${totalMarks} matches`);
                        this.updateMatches();
                    }
                });
            }
            
            this.markInstance = markInstance;
        });
        
        // Additional pass: search in text content directly
        setTimeout(() => {
            const allText = document.body.textContent || document.body.innerText || '';
            const searchTermsToCheck = this.searchTerms.length > 0 ? this.searchTerms : [this.searchQuery];
            
            let foundMatches = 0;
            searchTermsToCheck.forEach(term => {
                if (term && allText.toLowerCase().includes(term.toLowerCase())) {
                    foundMatches++;
                }
            });
            
            console.log(`Smart Search: Found ${foundMatches} terms in document text`);
            
            if (foundMatches === 0) {
                console.warn('Smart Search: No matches found in document. Search terms:', this.searchTerms, 'Query:', this.searchQuery);
            }
        }, 500);
    }
    
    updateMatches() {
        this.matches = Array.from(document.querySelectorAll('.search-highlight'));
        const counter = document.getElementById('search-counter');
        
        if (counter) {
            counter.textContent = `${this.matches.length} matches found`;
        }
        
        if (this.matches.length > 0) {
            this.highlightCurrentMatch();
            // Auto-scroll to first match after a short delay
            setTimeout(() => {
                this.scrollToFirstMatch();
            }, 100);
        }
        
        this.updateNavigationState();
    }
    
    highlightCurrentMatch() {
        // Remove current highlighting
        this.matches.forEach(match => match.classList.remove('current'));
        
        // Add current highlighting
        if (this.matches[this.currentIndex]) {
            this.matches[this.currentIndex].classList.add('current');
        }
    }
    
    scrollToFirstMatch() {
        if (this.matches.length > 0) {
            this.scrollToMatch(0);
        }
    }
    
    scrollToMatch(index) {
        if (index >= 0 && index < this.matches.length) {
            this.currentIndex = index;
            this.highlightCurrentMatch();
            
            const match = this.matches[index];
            const offset = 120; // Offset from top to account for fixed headers
            
            const elementTop = match.getBoundingClientRect().top + window.pageYOffset - offset;
            
            window.scrollTo({
                top: elementTop,
                behavior: 'smooth'
            });
            
            // Flash the current match
            match.style.transform = 'scale(1.1)';
            setTimeout(() => {
                match.style.transform = 'scale(1)';
            }, 300);
            
            // Update counter with current position
            const counter = document.getElementById('search-counter');
            if (counter && this.matches.length > 0) {
                counter.textContent = `${index + 1} of ${this.matches.length} matches`;
            }
        }
    }
    
    nextMatch() {
        if (this.matches.length === 0) return;
        
        this.currentIndex = (this.currentIndex + 1) % this.matches.length;
        this.scrollToMatch(this.currentIndex);
    }
    
    prevMatch() {
        if (this.matches.length === 0) return;
        
        this.currentIndex = this.currentIndex === 0 ? this.matches.length - 1 : this.currentIndex - 1;
        this.scrollToMatch(this.currentIndex);
    }
    
    setupNavigation() {
        const nextBtn = document.getElementById('next-match');
        const prevBtn = document.getElementById('prev-match');
        
        if (nextBtn) {
            nextBtn.addEventListener('click', () => this.nextMatch());
        }
        
        if (prevBtn) {
            prevBtn.addEventListener('click', () => this.prevMatch());
        }
        
        // Keyboard navigation
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey || e.metaKey) {
                switch(e.key) {
                    case 'ArrowDown':
                    case 'g':
                        e.preventDefault();
                        this.nextMatch();
                        break;
                    case 'ArrowUp':
                    case 'G':
                        e.preventDefault();
                        this.prevMatch();
                        break;
                }
            }
            
            // F3 and Shift+F3 for next/previous (like browsers)
            if (e.key === 'F3') {
                e.preventDefault();
                if (e.shiftKey) {
                    this.prevMatch();
                } else {
                    this.nextMatch();
                }
            }
        });
    }
    
    updateNavigationState() {
        const nextBtn = document.getElementById('next-match');
        const prevBtn = document.getElementById('prev-match');
        
        if (this.matches.length === 0) {
            if (nextBtn) nextBtn.disabled = true;
            if (prevBtn) prevBtn.disabled = true;
        } else {
            if (nextBtn) nextBtn.disabled = false;
            if (prevBtn) nextBtn.disabled = false;
        }
    }
    
    clear() {
        if (this.markInstance) {
            this.markInstance.unmark();
        }
        this.matches = [];
        this.currentIndex = 0;
        
        const counter = document.getElementById('search-counter');
        if (counter) {
            counter.textContent = '0 matches found';
        }
    }
}

// Global functions
function clearSearch() {
    const url = new URL(window.location);
    url.searchParams.delete('q');
    window.location.href = url.toString();
}

// Initialize search when DOM is ready
function initSmartSearch(searchQuery, searchTerms) {
    if (typeof Mark === 'undefined') {
        console.warn('Mark.js library not loaded. Search highlighting will not work.');
        return null;
    }
    
    return new SmartSearch(searchQuery, searchTerms);
}

// Export for use in templates
window.SmartSearch = SmartSearch;
window.initSmartSearch = initSmartSearch;
window.clearSearch = clearSearch;
