/**
 * Form validation for the Burnout Prevention System
 * This file contains validations for the registration, login and questionnaire forms
 */

document.addEventListener('DOMContentLoaded', function() {
  // Registration form validation
  const registrationForm = document.getElementById('registration-form');
  if (registrationForm) {
    registrationForm.addEventListener('submit', function(event) {
      if (!validateRegistrationForm()) {
        event.preventDefault();
      }
    });
  }
  
  // Login form validation
  const loginForm = document.getElementById('login-form');
  if (loginForm) {
    loginForm.addEventListener('submit', function(event) {
      if (!validateLoginForm()) {
        event.preventDefault();
      }
    });
  }
  
  // Questionnaire form validation
  const questionnaireForm = document.getElementById('questionnaire-form');
  if (questionnaireForm) {
    questionnaireForm.addEventListener('submit', function(event) {
      if (!validateQuestionnaireForm()) {
        event.preventDefault();
        // Scroll to the first error
        const firstError = document.querySelector('.is-invalid');
        if (firstError) {
          firstError.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
      }
    });
  }
});

/**
 * Validates the registration form
 * @returns {boolean} Whether the form is valid
 */
function validateRegistrationForm() {
  let isValid = true;
  
  // Get form fields
  const nameInput = document.getElementById('name');
  const emailInput = document.getElementById('email');
  const passwordInput = document.getElementById('password');
  const confirmPasswordInput = document.getElementById('confirm-password');
  
  // Validate name
  if (!nameInput.value.trim()) {
    showError(nameInput, 'O nome é obrigatório');
    isValid = false;
  } else {
    clearError(nameInput);
  }
  
  // Validate email
  if (!emailInput.value.trim()) {
    showError(emailInput, 'O e-mail é obrigatório');
    isValid = false;
  } else if (!isValidEmail(emailInput.value)) {
    showError(emailInput, 'Por favor, insira um e-mail válido');
    isValid = false;
  } else {
    clearError(emailInput);
  }
  
  // Validate password
  if (!passwordInput.value) {
    showError(passwordInput, 'A senha é obrigatória');
    isValid = false;
  } else if (passwordInput.value.length < 6) {
    showError(passwordInput, 'A senha deve ter pelo menos 6 caracteres');
    isValid = false;
  } else {
    clearError(passwordInput);
  }
  
  // Validate confirm password
  if (confirmPasswordInput.value !== passwordInput.value) {
    showError(confirmPasswordInput, 'As senhas não coincidem');
    isValid = false;
  } else {
    clearError(confirmPasswordInput);
  }
  
  return isValid;
}

/**
 * Validates the login form
 * @returns {boolean} Whether the form is valid
 */
function validateLoginForm() {
  let isValid = true;
  
  // Get form fields
  const emailInput = document.getElementById('email');
  const passwordInput = document.getElementById('password');
  
  // Validate email
  if (!emailInput.value.trim()) {
    showError(emailInput, 'O e-mail é obrigatório');
    isValid = false;
  } else if (!isValidEmail(emailInput.value)) {
    showError(emailInput, 'Por favor, insira um e-mail válido');
    isValid = false;
  } else {
    clearError(emailInput);
  }
  
  // Validate password
  if (!passwordInput.value) {
    showError(passwordInput, 'A senha é obrigatória');
    isValid = false;
  } else {
    clearError(passwordInput);
  }
  
  return isValid;
}

/**
 * Validates the questionnaire form
 * @returns {boolean} Whether the form is valid
 */
function validateQuestionnaireForm() {
  let isValid = true;
  
  // Get all question fields
  const radioQuestions = document.querySelectorAll('.question-card');
  
  // Check each question
  radioQuestions.forEach(questionCard => {
    const questionId = questionCard.getAttribute('data-question-id');
    const radioInputs = document.querySelectorAll(`input[name="${questionId}"]`);
    const selectedInput = Array.from(radioInputs).find(input => input.checked);
    
    if (!selectedInput) {
      // Show error for the question
      const feedbackDiv = questionCard.querySelector('.invalid-feedback');
      if (feedbackDiv) {
        feedbackDiv.style.display = 'block';
      } else {
        const newFeedback = document.createElement('div');
        newFeedback.className = 'invalid-feedback';
        newFeedback.textContent = 'Por favor, selecione uma opção';
        newFeedback.style.display = 'block';
        questionCard.appendChild(newFeedback);
      }
      
      // Add invalid class to the question card
      questionCard.classList.add('is-invalid');
      isValid = false;
    } else {
      // Clear error
      const feedbackDiv = questionCard.querySelector('.invalid-feedback');
      if (feedbackDiv) {
        feedbackDiv.style.display = 'none';
      }
      questionCard.classList.remove('is-invalid');
    }
  });
  
  return isValid;
}

/**
 * Checks if an email is valid
 * @param {string} email - The email to validate
 * @returns {boolean} Whether the email is valid
 */
function isValidEmail(email) {
  const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return re.test(email);
}

/**
 * Shows an error message for an input
 * @param {HTMLElement} inputElement - The input element
 * @param {string} message - The error message
 */
function showError(inputElement, message) {
  inputElement.classList.add('is-invalid');
  
  // Get or create feedback div
  let feedbackDiv = inputElement.nextElementSibling;
  if (!feedbackDiv || !feedbackDiv.classList.contains('invalid-feedback')) {
    feedbackDiv = document.createElement('div');
    feedbackDiv.className = 'invalid-feedback';
    inputElement.parentNode.insertBefore(feedbackDiv, inputElement.nextSibling);
  }
  
  feedbackDiv.textContent = message;
}

/**
 * Clears error message for an input
 * @param {HTMLElement} inputElement - The input element
 */
function clearError(inputElement) {
  inputElement.classList.remove('is-invalid');
  
  // Clear feedback div
  const feedbackDiv = inputElement.nextElementSibling;
  if (feedbackDiv && feedbackDiv.classList.contains('invalid-feedback')) {
    feedbackDiv.textContent = '';
  }
}
