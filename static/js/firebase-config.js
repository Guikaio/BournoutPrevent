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
  firebase.initializeApp(firebaseConfig);
  
  console.log("Firebase initialized successfully");
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
 * Logout the current user
 * @returns {Promise} - Firebase auth promise
 */
function logoutUser() {
  return firebase.auth().signOut();
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
  if (typeof firebase !== 'undefined') {
    onAuthStateChanged((user) => {
      updateNavigation(user);
    });
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
