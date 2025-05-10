/**
 * Validação de formulários para o Sistema de Prevenção de Burnout
 * Este arquivo contém validações para os formulários de cadastro, login e questionário
 */

document.addEventListener('DOMContentLoaded', function() {
  // Validação do formulário de cadastro
  const registrationForm = document.getElementById('registration-form');
  if (registrationForm) {
    registrationForm.addEventListener('submit', function(event) {
      if (!validateRegistrationForm()) {
        event.preventDefault();
      }
    });
  }
  
  // Validação do formulário de login
  const loginForm = document.getElementById('login-form');
  if (loginForm) {
    loginForm.addEventListener('submit', function(event) {
      if (!validateLoginForm()) {
        event.preventDefault();
      }
    });
  }
  
  // Validação do formulário de questionário
  const questionnaireForm = document.getElementById('questionnaire-form');
  if (questionnaireForm) {
    questionnaireForm.addEventListener('submit', function(event) {
      if (!validateQuestionnaireForm()) {
        event.preventDefault();
        // Rola até o primeiro erro
        const firstError = document.querySelector('.is-invalid');
        if (firstError) {
          firstError.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
      }
    });
  }
});

/**
 * Valida o formulário de cadastro
 * @returns {boolean} Se o formulário é válido
 */
function validateRegistrationForm() {
  let isValid = true;
  
  // Obtém os campos do formulário
  const nameInput = document.getElementById('name');
  const emailInput = document.getElementById('email');
  const passwordInput = document.getElementById('password');
  const confirmPasswordInput = document.getElementById('confirm-password');
  
  // Valida nome
  if (!nameInput.value.trim()) {
    showError(nameInput, 'O nome é obrigatório');
    isValid = false;
  } else {
    clearError(nameInput);
  }
  
  // Valida e-mail
  if (!emailInput.value.trim()) {
    showError(emailInput, 'O e-mail é obrigatório');
    isValid = false;
  } else if (!isValidEmail(emailInput.value)) {
    showError(emailInput, 'Por favor, insira um e-mail válido');
    isValid = false;
  } else {
    clearError(emailInput);
  }
  
  // Valida senha
  if (!passwordInput.value) {
    showError(passwordInput, 'A senha é obrigatória');
    isValid = false;
  } else if (passwordInput.value.length < 6) {
    showError(passwordInput, 'A senha deve ter pelo menos 6 caracteres');
    isValid = false;
  } else {
    clearError(passwordInput);
  }
  
  // Valida confirmação de senha
  if (confirmPasswordInput.value !== passwordInput.value) {
    showError(confirmPasswordInput, 'As senhas não coincidem');
    isValid = false;
  } else {
    clearError(confirmPasswordInput);
  }
  
  return isValid;
}

/**
 * Valida o formulário de login
 * @returns {boolean} Se o formulário é válido
 */
function validateLoginForm() {
  let isValid = true;
  
  // Obtém os campos do formulário
  const emailInput = document.getElementById('email');
  const passwordInput = document.getElementById('password');
  
  // Valida e-mail
  if (!emailInput.value.trim()) {
    showError(emailInput, 'O e-mail é obrigatório');
    isValid = false;
  } else if (!isValidEmail(emailInput.value)) {
    showError(emailInput, 'Por favor, insira um e-mail válido');
    isValid = false;
  } else {
    clearError(emailInput);
  }
  
  // Valida senha
  if (!passwordInput.value) {
    showError(passwordInput, 'A senha é obrigatória');
    isValid = false;
  } else {
    clearError(passwordInput);
  }
  
  return isValid;
}

/**
 * Valida o formulário de questionário
 * @returns {boolean} Se o formulário é válido
 */
function validateQuestionnaireForm() {
  let isValid = true;
  
  // Obtém todos os campos das perguntas
  const radioQuestions = document.querySelectorAll('.question-card');
  
  // Verifica cada pergunta
  radioQuestions.forEach(questionCard => {
    const questionId = questionCard.getAttribute('data-question-id');
    const radioInputs = document.querySelectorAll(`input[name="${questionId}"]`);
    const selectedInput = Array.from(radioInputs).find(input => input.checked);
    
    if (!selectedInput) {
      // Mostra erro para a pergunta
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
      
      // Adiciona classe de erro ao card da pergunta
      questionCard.classList.add('is-invalid');
      isValid = false;
    } else {
      // Limpa erro
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
 * Verifica se um e-mail é válido
 * @param {string} email - O e-mail a ser validado
 * @returns {boolean} Se o e-mail é válido
 */
function isValidEmail(email) {
  const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return re.test(email);
}

/**
 * Mostra uma mensagem de erro para um campo
 * @param {HTMLElement} inputElement - O campo de entrada
 * @param {string} message - A mensagem de erro
 */
function showError(inputElement, message) {
  inputElement.classList.add('is-invalid');
  
  // Obtém ou cria o elemento de feedback
  let feedbackDiv = inputElement.nextElementSibling;
  if (!feedbackDiv || !feedbackDiv.classList.contains('invalid-feedback')) {
    feedbackDiv = document.createElement('div');
    feedbackDiv.className = 'invalid-feedback';
    inputElement.parentNode.insertBefore(feedbackDiv, inputElement.nextSibling);
  }
  
  feedbackDiv.textContent = message;
}

/**
 * Limpa a mensagem de erro de um campo
 * @param {HTMLElement} inputElement - O campo de entrada
 */
function clearError(inputElement) {
  inputElement.classList.remove('is-invalid');
  
  // Limpa o elemento de feedback
  const feedbackDiv = inputElement.nextElementSibling;
  if (feedbackDiv && feedbackDiv.classList.contains('invalid-feedback')) {
    feedbackDiv.textContent = '';
  }
}
