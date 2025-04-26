/**
 * Firebase configuration for the Burnout Prevention System
 * This file initializes Firebase and provides authentication functions
 */

// Initialize Firebase with provided configuration
function initializeFirebase(apiKey, projectId, appId) {
  const firebaseConfig = {
    apiKey: apiKey,
    authDomain: `${projectId}.firebaseapp.com`,
    projectId: projectId,
    storageBucket: `${projectId}.appspot.com`,
    messagingSenderId: "123456789012", // This is a placeholder as we don't need messaging
    appId: appId
  };

  // Initialize Firebase
  if (!firebase.apps.length) {
    firebase.initializeApp(firebaseConfig);
  }
  
  console.log("Firebase initialized successfully");
  
  // Set up auth state listener
  setupAuthListener();
}

/**
 * Set up authentication state listener
 */
function setupAuthListener() {
  firebase.auth().onAuthStateChanged((user) => {
    updateNavigation(user);
    
    if (user) {
      // User is signed in
      console.log("User is signed in:", user.displayName);
      
      // Check if we're on login or register page and need to redirect
      const currentPage = window.location.pathname;
      if (currentPage.includes('/login') || currentPage.includes('/register')) {
        // Create session on server side
        const data = new FormData();
        data.append('email', user.email);
        data.append('name', user.displayName);
        data.append('firebase_uid', user.uid);
        
        fetch('/login', {
          method: 'POST',
          body: data
        })
        .then(response => {
          if (response.redirected) {
            window.location.href = response.url;
          }
        })
        .catch(error => {
          console.error("Error syncing auth state with server:", error);
        });
      }
    } else {
      // User is signed out
      console.log("User is signed out");
    }
  });
}

/**
 * Register a new user with email and password
 * @param {string} email - User's email
 * @param {string} password - User's password
 * @param {string} name - User's name
 * @returns {Promise} - Firebase auth promise
 */
function registerUser(email, password, name) {
  return firebase.auth().createUserWithEmailAndPassword(email, password)
    .then((userCredential) => {
      // Update profile to add display name
      return userCredential.user.updateProfile({
        displayName: name
      }).then(() => {
        return userCredential;
      });
    });
}

/**
 * Login a user with email and password
 * @param {string} email - User's email
 * @param {string} password - User's password
 * @returns {Promise} - Firebase auth promise
 */
function loginUser(email, password) {
  return firebase.auth().signInWithEmailAndPassword(email, password);
}

/**
 * Sign in with Google
 * @returns {Promise} - Firebase auth promise
 */
function signInWithGoogle() {
  const provider = new firebase.auth.GoogleAuthProvider();
  return firebase.auth().signInWithPopup(provider);
}

/**
 * Logout the current user
 * @returns {Promise} - Firebase auth promise
 */
function logoutUser() {
  return firebase.auth().signOut().then(() => {
    // After signing out from Firebase, sign out from the server session
    window.location.href = '/logout';
  });
}

/**
 * Get the current authenticated user
 * @returns {Object|null} - Firebase user object or null if not authenticated
 */
function getCurrentUser() {
  return firebase.auth().currentUser;
}

/**
 * Listen for auth state changes
 * @param {Function} callback - Callback function that receives the user object
 * @returns {Function} - Unsubscribe function
 */
function onAuthStateChanged(callback) {
  return firebase.auth().onAuthStateChanged(callback);
}

// Listen for authentication changes and update UI
document.addEventListener('DOMContentLoaded', function() {
  // Check if Firebase is defined
  if (typeof firebase !== 'undefined' && firebase.apps.length > 0) {
    // Setup logout button
    const logoutBtn = document.getElementById('logout-button');
    if (logoutBtn) {
      logoutBtn.addEventListener('click', function(e) {
        e.preventDefault();
        logoutUser();
      });
    }
    
    // Setup email/password login form
    const loginForm = document.getElementById('login-form');
    if (loginForm) {
      loginForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        if (!validateLoginForm()) {
          return;
        }
        
        const email = document.getElementById('email').value;
        const password = document.getElementById('password').value;
        
        loginUser(email, password)
          .catch(error => {
            console.error("Login error:", error);
            alert("Erro ao fazer login: " + error.message);
          });
      });
    }
    
    // Setup registration form
    const registrationForm = document.getElementById('registration-form');
    if (registrationForm) {
      registrationForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        if (!validateRegistrationForm()) {
          return;
        }
        
        const name = document.getElementById('name').value;
        const email = document.getElementById('email').value;
        const password = document.getElementById('password').value;
        
        registerUser(email, password, name)
          .catch(error => {
            console.error("Registration error:", error);
            alert("Erro ao criar conta: " + error.message);
          });
      });
    }
  }
});

/**
 * Update navigation based on authentication state
 * @param {Object|null} user - Firebase user object or null
 */
function updateNavigation(user) {
  const authNavItems = document.querySelectorAll('.auth-nav-item');
  const unauthNavItems = document.querySelectorAll('.unauth-nav-item');
  
  if (user) {
    // User is signed in
    authNavItems.forEach(item => item.style.display = 'block');
    unauthNavItems.forEach(item => item.style.display = 'none');
    
    // Update user display name if available
    const userNameElement = document.getElementById('user-name');
    if (userNameElement && user.displayName) {
      userNameElement.textContent = user.displayName;
    }
  } else {
    // User is signed out
    authNavItems.forEach(item => item.style.display = 'none');
    unauthNavItems.forEach(item => item.style.display = 'block');
  }
}
