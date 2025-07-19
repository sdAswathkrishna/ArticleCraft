// main.js

// Initialize page-specific functionality when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    const currentPage = getCurrentPage();

    updateNavbar();

    // Handle search
    const searchForm = document.getElementById('search-form');
    if (searchForm) {
        searchForm.addEventListener('submit', function (e) {
            e.preventDefault();
            const query = document.getElementById('search-input').value.trim();
            if (query) {
                window.location.href = `index.html?search=${encodeURIComponent(query)}`;
            }
        });
    }

    switch(currentPage) {
        case 'index.html':
        case '':
            initIndexPage();
            break;
        case 'register.html':
            initRegisterPage();
            break;
        case 'login.html':
            initLoginPage();
            break;
        case 'write.html':
            initWritePage();
            break;
        case 'read.html':
            initReadPage();
            break;
        case 'profile.html':
            initProfilePage();
            break;
    }
});

// Helper function to get current page name
function getCurrentPage() {
    const path = window.location.pathname;
    return path.split('/').pop() || 'index.html';
}

// Helper function to get URL parameters
function getUrlParameter(name) {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get(name);
}

// Helper function to show messages
function showMessage(elementId, message, isError = false) {
    const element = document.getElementById(elementId);
    if (element) {
        element.textContent = message;
        element.className = isError ? 'error-message' : 'success';
        element.style.display = 'block';
    }
}

// Helper function to hide messages
function hideMessage(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.style.display = 'none';
    }
}

// INDEX PAGE FUNCTIONALITY
function initIndexPage() {
    loadArticles();
}


async function loadArticles() {
    const articleList = document.getElementById('article-list');
    const searchQuery = getUrlParameter('search')?.toLowerCase() || '';

    try {
        articleList.innerHTML = '<div class="loading">Loading articles...</div>';

        const response = await fetch('/articles');
        if (!response.ok) throw new Error('Failed to fetch articles');

        const articles = await response.json();

        const filtered = searchQuery
            ? articles.filter(article =>
                  article.title?.toLowerCase().includes(searchQuery) ||
                  article.content?.toLowerCase().includes(searchQuery)
              )
            : articles;

        if (filtered.length === 0) {
            articleList.innerHTML = '<div class="error">No matching articles found.</div>';
            return;
        }

        articleList.innerHTML = '';
        filtered.forEach(article => {
            const articleElement = createArticleElement(article);
            articleList.appendChild(articleElement);
        });

    } catch (error) {
        console.error('Error loading articles:', error);
        articleList.innerHTML = '<div class="error">Error loading articles. Please try again later.</div>';
    }
}


function createArticleElement(article) {
    const articleDiv = document.createElement('div');
    articleDiv.className = 'article-item';
    articleDiv.style.cursor = 'pointer';

    // Entire article box clickable
    articleDiv.addEventListener('click', () => {
        window.location.href = `read.html?id=${article.id}`;
    });

    const title = document.createElement('h2');
    title.className = 'article-title';
    title.textContent = article.title || 'Untitled';

    const author = document.createElement('div');
    author.className = 'article-author';
    author.textContent = article.author_name ? `By ${article.author_name}` : 'Unknown Author';

    const preview = document.createElement('div');
    preview.className = 'article-preview';
    const content = article.content || '';
    preview.textContent = content.length > 200 ? content.substring(0, 200) + '...' : content;

    // Assemble
    articleDiv.appendChild(title);
    articleDiv.appendChild(author);
    articleDiv.appendChild(preview);

    return articleDiv;
}

// function createArticleElement(article) {
//     const articleDiv = document.createElement('div');
//     articleDiv.className = 'article-item';
    
//     const title = document.createElement('h2');
//     title.className = 'article-title';
    
//     const titleLink = document.createElement('a');
//     titleLink.href = `read.html?id=${article.id}`;
//     titleLink.textContent = article.title || 'Untitled';
//     titleLink.style.textDecoration = 'none';
//     titleLink.style.color = 'inherit';
//     title.appendChild(titleLink);
    
//     const author = document.createElement('div');
//     author.className = 'article-author';
//     author.textContent = article.author_name ? `By ${article.author_name}` : 'Unknown Author';

    
//     const preview = document.createElement('div');
//     preview.className = 'article-preview';
//     const content = article.content || '';
//     preview.textContent = content.length > 200 ? content.substring(0, 200) + '...' : content;
    
//     const readMore = document.createElement('a');
//     readMore.className = 'read-more';
//     readMore.href = `read.html?id=${article.id}`;
//     readMore.textContent = 'Read More';
    
//     articleDiv.appendChild(title);
//     articleDiv.appendChild(author);
//     articleDiv.appendChild(preview);
//     articleDiv.appendChild(readMore);
    
//     return articleDiv;
// }

// REGISTER PAGE FUNCTIONALITY
function initRegisterPage() {
    localStorage.removeItem('user_id');
    localStorage.removeItem('is_logged_in');

    const form = document.getElementById('register-form');
    if (form) {
        form.addEventListener('submit', handleRegister);
    }
}

async function handleRegister(event) {
    event.preventDefault();
    
    const username = document.getElementById('username').value;
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;
    
    try {
        hideMessage('form-message');
        
        const response = await fetch('/register', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                username: username,
                email: email,
                password: password
            })
        });
        
        if (response.ok) {
            showMessage('form-message', 'Registration successful! Redirecting to login...');
            setTimeout(() => {
                window.location.href = 'login.html';
            }, 2000);
        } else {
            const errorData = await response.json();
            showMessage('form-message', errorData.detail || 'Registration failed', true);
        }
        
    } catch (error) {
        console.error('Registration error:', error);
        showMessage('form-message', 'Network error. Please try again.', true);
    }
}

// LOGIN PAGE FUNCTIONALITY
function initLoginPage() {
    const form = document.getElementById('login-form');
    if (form) {
        form.addEventListener('submit', handleLogin);
    }
}

async function handleLogin(event) {
    event.preventDefault();
    
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;
    
    try {
        hideMessage('form-message');
        
        const response = await fetch('/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                email: email,
                password: password
            })
        });
        
        if (response.ok) {
            const user = await response.json();
            localStorage.setItem('user_id', user.id);
            localStorage.setItem('is_logged_in', 'true');

            showMessage('form-message', 'Login successful! Redirecting...');
            setTimeout(() => {
                window.location.href = 'index.html';
            }, 1500);
        } else {
            const errorData = await response.json();
            showMessage('form-message', errorData.detail || 'Login failed', true);
        }
        
    } catch (error) {
        console.error('Login error:', error);
        showMessage('form-message', 'Network error. Please try again.', true);
    }
}

// WRITE PAGE FUNCTIONALITY
function initWritePage() {
    const generateBtn = document.getElementById('generate-btn');
    const form = document.getElementById('write-form');
    
    if (generateBtn) {
        generateBtn.addEventListener('click', handleGenerateArticle);
    }
    
    if (form) {
        form.addEventListener('submit', handlePublishArticle);
    }
}

async function handleGenerateArticle() {
    const title = document.getElementById('title').value;
    const numSimilarArticles = parseInt(document.getElementById('num_similar_articles').value) || 3;
    
    if (!title.trim()) {
        showMessage('generation-message', 'Please enter a title first', true);
        return;
    }
    
    try {
        hideMessage('generation-message');
        showMessage('generation-message', 'Generating article...');
        
        const response = await fetch('/articles/generate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                request: {
                    title: title,
                    num_similar_articles: numSimilarArticles
                },
                user_id: parseInt(localStorage.getItem('user_id'))
            })
        });
        
        if (response.ok) {
            const data = await response.json();
            document.getElementById('content').value = data.content || data.generated_content || '';
            showMessage('generation-message', 'Article generated successfully!');
        } else {
            const errorData = await response.json();
            showMessage('generation-message', errorData.detail || 'Generation failed', true);
        }
        
    } catch (error) {
        console.error('Generation error:', error);
        showMessage('generation-message', 'Network error. Please try again.', true);
    }
}

async function handlePublishArticle(event) {
    event.preventDefault();
    
    const title = document.getElementById('title').value;
    const content = document.getElementById('content').value;
    
    if (!title.trim() || !content.trim()) {
        showMessage('form-message', 'Please provide both title and content', true);
        return;
    }
    
    try {
        hideMessage('form-message');
        
        const response = await fetch('/articles/create', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                article: {
                    title: title,
                    content: content
                },
                user_id: parseInt(localStorage.getItem('user_id'))
            })
        });
        
        if (response.ok) {
            showMessage('form-message', 'Article published successfully! Redirecting...');
            setTimeout(() => {
                window.location.href = 'index.html';
            }, 2000);
        } else {
            const errorData = await response.json();
            showMessage('form-message', errorData.detail || 'Publishing failed', true);
        }
        
    } catch (error) {
        console.error('Publishing error:', error);
        showMessage('form-message', 'Network error. Please try again.', true);
    }
}

// READ PAGE FUNCTIONALITY
function initReadPage() {
    const articleId = getUrlParameter('id');
    if (articleId) {
        loadArticle(articleId);
        initLikeButton(articleId);
    } else {
        showMessage('error-message', 'No article ID provided', true);
    }
}

async function loadArticle(articleId) {
    try {
        showMessage('loading-message', 'Loading article...');
        
        const response = await fetch(`/articles/${articleId}`);
        
        if (!response.ok) {
            throw new Error('Article not found');
        }
        
        const data = await response.json();
        
        hideMessage('loading-message');
        displayArticle(data.article);
        displayRecommendedArticles(data.recommended || []);
        
    } catch (error) {
        console.error('Error loading article:', error);
        hideMessage('loading-message');
        showMessage('error-message', 'Error loading article. Please try again.', true);
    }
}

function displayArticle(article) {
    document.getElementById('article-title').textContent = article.title || 'Untitled';
    document.getElementById('article-author').textContent = article.author_name ? `By ${article.author_name}` : 'Unknown Author';
    document.getElementById('article-body').textContent = article.content || '';
    
    const articleContent = document.getElementById('article-content');
    if (articleContent) {
        articleContent.style.display = 'block';
    }
}

function displayRecommendedArticles(recommended) {
    const recommendedList = document.getElementById('recommended-list');
    
    if (!recommendedList) return;
    
    if (recommended.length === 0) {
        recommendedList.innerHTML = '<div class="error">No recommended articles found.</div>';
        return;
    }
    
    recommendedList.innerHTML = '';
    
    recommended.forEach(item => {
        const recommendedDiv = document.createElement('div');
        recommendedDiv.className = 'recommended-item';
        
        const title = document.createElement('h3');
        title.className = 'recommended-title';
        title.textContent = item.clean_title || 'Untitled';
        
        // const similarity = document.createElement('div');
        // similarity.className = 'recommended-similarity';
        // similarity.textContent = `Similarity: ${(item.similarity * 100).toFixed(1)}%`;
        
        const preview = document.createElement('div');
        preview.className = 'recommended-preview';
        const text = item.clean_text || '';
        preview.textContent = text.length > 200 ? text.substring(0, 200) + '...' : text;
        
        recommendedDiv.appendChild(title);
        // recommendedDiv.appendChild(similarity);
        recommendedDiv.appendChild(preview);
        
        recommendedList.appendChild(recommendedDiv);
    });
}

function initLikeButton(articleId) {
    const likeBtn = document.getElementById('like-btn');
    if (likeBtn) {
        likeBtn.addEventListener('click', () => handleLike(articleId));
    }
}

async function handleLike(articleId) {
    try {
        hideMessage('like-message');
        
        const response = await fetch(`/articles/${articleId}/like`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(parseInt(localStorage.getItem('user_id')))
        });
        
        if (response.ok) {
            showMessage('like-message', 'Article liked!');
        } else {
            const errorData = await response.json();
            showMessage('like-message', errorData.detail || 'Like failed', true);
        }
        
    } catch (error) {
        console.error('Like error:', error);
        showMessage('like-message', 'Network error. Please try again.', true);
    }
}

// PROFILE PAGE FUNCTIONALITY
function initProfilePage() {
    const userId = getUrlParameter('user_id') || localStorage.getItem('user_id');
    if (userId) {
        loadUserArticles(userId);
    } else {
        showMessage('error-message', 'No user ID provided', true);
    }
}

async function loadUserArticles(userId) {
    const userArticles = document.getElementById('user-articles');
    
    try {
        showMessage('loading-message', 'Loading user articles...');
        
        const response = await fetch(`/users/${userId}/articles`);
        
        if (!response.ok) {
            throw new Error('Failed to fetch user articles');
        }
        
        const articles = await response.json();
        
        hideMessage('loading-message');
        
        if (articles.length === 0) {
            userArticles.innerHTML = '<div class="error">No articles found for this user.</div>';
            return;
        }
        
        userArticles.innerHTML = '';
        
        articles.forEach(article => {
            const articleElement = createArticleElement(article);
            userArticles.appendChild(articleElement);
        });
        
    } catch (error) {
        console.error('Error loading user articles:', error);
        hideMessage('loading-message');
        showMessage('error-message', 'Error loading user articles. Please try again.', true);
    }
}


function updateNavbar() {
    const navLinks = document.getElementById('nav-links');
    const userId = localStorage.getItem('user_id');
    const isLoggedIn = localStorage.getItem('is_logged_in') === 'true';

    if (!navLinks) return;

    navLinks.innerHTML = '';

    if (userId && isLoggedIn) {
        // ✍️ Write
        const writeLink = document.createElement('li');
        writeLink.innerHTML = `<a href="write.html">✍️ Write</a>`;
        navLinks.appendChild(writeLink);

        // 👤 Profile icon only
        const profileLink = document.createElement('li');
        profileLink.innerHTML = `<a href="profile.html">👤</a>`;
        navLinks.appendChild(profileLink);
    } else {
        // Login only
        const loginLink = document.createElement('li');
        loginLink.innerHTML = `<a href="login.html">Login</a>`;
        navLinks.appendChild(loginLink);
    }
}

