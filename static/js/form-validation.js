/**
 * Validação de formulários do Sistema de Prevenção ao Burnout
 * Este arquivo contém as validações para os formulários de cadastro, login e questionário
 */

// Executa após o carregamento completo da página
document.addEventListener('DOMContentLoaded', function() {
  // Validação do formulário de cadastro
  const registrationForm = document.getElementById('registration-form');
  if (registrationForm) {
    registrationForm.addEventListener('submit', function(event) {
      if (!validateRegistrationForm()) {
        event.preventDefault(); // Impede o envio se inválido
      }
    });
  }

  // Validação do formulário de login
  const loginForm = document.getElementById('login-form');
  if (loginForm) {
    loginForm.addEventListener('submit', function(event) {
      if (!validateLoginForm()) {
        event.preventDefault(); // Impede o envio se inválido
      }
    });
  }

  // Validação do formulário do questionário
  const questionnaireForm = document.getElementById('questionnaire-form');
  if (questionnaireForm) {
    questionnaireForm.addEventListener('submit', function(event) {
      if (!validateQuestionnaireForm()) {
        event.preventDefault(); // Impede o envio se inválido

        // Rola até a primeira questão com erro
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
 * @returns {boolean} true se o formulário for válido
 */
function validateRegistrationForm() {
  let isValid = true;

  // Captura os campos do formulário
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
 * @returns {boolean} true se o formulário for válido
 */
function validateLoginForm() {
  let isValid = true;

  // Captura os campos do formulário
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
 * Valida o formulário do questionário
 * @returns {boolean} true se o formulário for válido
 */
function validateQuestionnaireForm() {
  let isValid = true;

  // Captura todos os blocos de pergunta
  const radioQuestions = document.querySelectorAll('.question-card');

  // Verifica se cada pergunta foi respondida
  radioQuestions.forEach(questionCard => {
    const questionId = questionCard.getAttribute('data-question-id');
    const radioInputs = document.querySelectorAll(`input[name="${questionId}"]`);
    const selectedInput = Array.from(radioInputs).find(input => input.checked);

    if (!selectedInput) {
      // Mostra a mensagem de erro
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

      // Adiciona classe de erro visual
      questionCard.classList.add('is-invalid');
      isValid = false;
    } else {
      // Limpa o erro
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
 * Verifica se o e-mail está no formato válido
 * @param {string} email - E-mail a ser validado
 * @returns {boolean} true se o e-mail for válido
 */
function isValidEmail(email) {
  const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return re.test(email);
}

/**
 * Mostra uma mensagem de erro para um campo de entrada
 * @param {HTMLElement} inputElement - Campo de entrada
 * @param {string} message - Mensagem de erro
 */
function showError(inputElement, message) {
  inputElement.classList.add('is-invalid');

  // Usa div existente ou cria nova para exibir a mensagem
  let feedbackDiv = inputElement.nextElementSibling;
  if (!feedbackDiv || !feedbackDiv.classList.contains('invalid-feedback')) {
    feedbackDiv = document.createElement('div');
    feedbackDiv.className = 'invalid-feedback';
    inputElement.parentNode.insertBefore(feedbackDiv, inputElement.nextSibling);
  }

  feedbackDiv.textContent = message;
}

/**
 * Remove a mensagem de erro de um campo de entrada
 * @param {HTMLElement} inputElement - Campo de entrada
 */
function clearError(inputElement) {
  inputElement.classList.remove('is-invalid');

  // Limpa o conteúdo da div de erro
  const feedbackDiv = inputElement.nextElementSibling;
  if (feedbackDiv && feedbackDiv.classList.contains('invalid-feedback')) {
    feedbackDiv.textContent = '';
  }
}
