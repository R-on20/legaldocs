/**
 * Debug version of Smart Search for ILDMS
 */

function debugSmartSearch(searchQuery, searchTerms) {
    console.log('=== DEBUG SMART SEARCH ===');
    console.log('Search Query:', searchQuery);
    console.log('Search Terms:', searchTerms);
    
    // Check if Mark.js is loaded
    if (typeof Mark === 'undefined') {
        console.error('❌ Mark.js library not loaded!');
        return;
    }
    console.log('✅ Mark.js library loaded');
    
    // Find content areas
    const selectors = [
        '.document-content',
        '.transcript-content',
        '.word-document-content'
    ];
    
    let foundElements = [];
    selectors.forEach(selector => {
        const elements = document.querySelectorAll(selector);
        console.log(`Selector "${selector}": found ${elements.length} elements`);
        
        elements.forEach((el, index) => {
            const textLength = el.textContent ? el.textContent.trim().length : 0;
            console.log(`  Element ${index}: ${textLength} characters`);
            if (textLength > 0) {
                foundElements.push(el);
                // Show first 200 characters of content
                const preview = el.textContent.trim().substring(0, 200);
                console.log(`  Content preview: "${preview}..."`);
                
                // Check if the search term exists in this content (case-insensitive)
                const searchTerm = searchQuery.toLowerCase();
                const contentLower = el.textContent.toLowerCase();
                const hasMatch = contentLower.includes(searchTerm);
                console.log(`  Content contains "${searchTerm}": ${hasMatch}`);
                
                if (hasMatch) {
                    // Show where it appears
                    const index = contentLower.indexOf(searchTerm);
                    const start = Math.max(0, index - 50);
                    const end = Math.min(contentLower.length, index + searchTerm.length + 50);
                    const context = el.textContent.substring(start, end);
                    console.log(`  Match context: "...${context}..."`);
                }
            }
        });
    });
    
    console.log(`Total elements with content: ${foundElements.length}`);
    
    if (foundElements.length === 0) {
        console.error('❌ No content elements found!');
        return;
    }
    
    // Try highlighting
    let totalMarked = 0;
    foundElements.forEach((element, index) => {
        console.log(`Processing element ${index + 1}/${foundElements.length}`);
        
        const markInstance = new Mark(element);
        
        if (searchTerms && searchTerms.length > 0) {
            searchTerms.forEach(term => {
                if (term && term.trim()) {
                    console.log(`  Marking term: "${term}"`);
                    markInstance.mark(term.trim(), {
                        className: 'search-highlight',
                        done: (markedCount) => {
                            console.log(`    Marked ${markedCount} instances of "${term}"`);
                            totalMarked += markedCount;
                            updateCounter();
                        }
                    });
                }
            });
        } else {
            // Fallback to full query
            console.log(`  Marking full query: "${searchQuery}"`);
            markInstance.mark(searchQuery, {
                className: 'search-highlight',
                done: (markedCount) => {
                    console.log(`    Marked ${markedCount} instances of full query`);
                    totalMarked += markedCount;
                    updateCounter();
                }
            });
        }
    });
    
    function updateCounter() {
        const counter = document.getElementById('search-counter');
        if (counter) {
            counter.textContent = `${totalMarked} matches found`;
            console.log(`✅ Updated counter: ${totalMarked} matches`);
        }
    }
    
    console.log('=== END DEBUG ===');
    return {
        elementsFound: foundElements.length,
        totalMarked: totalMarked
    };
}

// Export for global use
window.debugSmartSearch = debugSmartSearch;
