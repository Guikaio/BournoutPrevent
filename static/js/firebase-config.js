/**
 * Configuração do Firebase para o Sistema de Prevenção de Burnout
 * Este arquivo inicializa o Firebase e fornece funções de autenticação
 */

// Inicializa o Firebase com a configuração fornecida
function initializeFirebase(apiKey, projectId, appId) {
  const firebaseConfig = {
    apiKey: apiKey,
    authDomain: `${projectId}.firebaseapp.com`,
    projectId: projectId,
    storageBucket: `${projectId}.appspot.com`,
    messagingSenderId: "123456789012", // Este é um valor fictício pois não usamos mensagens
    appId: appId
  };

  // Inicializa o Firebase
  if (!firebase.apps.length) {
    firebase.initializeApp(firebaseConfig);
  }
  
  console.log("Firebase inicializado com sucesso");
  
  // Configura o ouvinte de estado de autenticação
  setupAuthListener();
}

/**
 * Configura o ouvinte de estado de autenticação
 */
function setupAuthListener() {
  firebase.auth().onAuthStateChanged((user) => {
    updateNavigation(user);
    
    if (user) {
      // Usuário está autenticado
      console.log("Usuário autenticado:", user.displayName);
      
      // Verifica se está na página de login ou cadastro e precisa redirecionar
      const currentPage = window.location.pathname;
      if (currentPage.includes('/login') || currentPage.includes('/register')) {
        // Cria sessão no servidor
        const data = new FormData();
        data.append('email', user.email);
        data.append('name', user.displayName);
        data.append('firebase_uid', user.uid);
        
        fetch('/auth/firebase-api', {
          method: 'POST',
          body: data
        })
        .then(response => response.json())
        .then(data => {
          if (data.success && data.redirect) {
            window.location.href = data.redirect;
          } else {
            console.error("Erro ao sincronizar autenticação:", data.error);
          }
        })
        .catch(error => {
          console.error("Erro ao sincronizar estado de autenticação com o servidor:", error);
        });
      }
    } else {
      // Usuário não está autenticado
      console.log("Usuário não está autenticado");
    }
  });
}

/**
 * Registra um novo usuário com e-mail e senha
 * @param {string} email - E-mail do usuário
 * @param {string} password - Senha do usuário
 * @param {string} name - Nome do usuário
 * @returns {Promise} - Promessa de autenticação do Firebase
 */
function registerUser(email, password, name) {
  return firebase.auth().createUserWithEmailAndPassword(email, password)
    .then((userCredential) => {
      // Atualiza o perfil para adicionar o nome
      return userCredential.user.updateProfile({
        displayName: name
      }).then(() => {
        return userCredential;
      });
    });
}

/**
 * Faz login de um usuário com e-mail e senha
 * @param {string} email - E-mail do usuário
 * @param {string} password - Senha do usuário
 * @returns {Promise} - Promessa de autenticação do Firebase
 */
function loginUser(email, password) {
  return firebase.auth().signInWithEmailAndPassword(email, password);
}

/**
 * Faz login com Google
 * @returns {Promise} - Promessa de autenticação do Firebase
 */
function signInWithGoogle() {
  const provider = new firebase.auth.GoogleAuthProvider();
  return firebase.auth().signInWithPopup(provider);
}

/**
 * Faz logout do usuário atual
 * @returns {Promise} - Promessa de autenticação do Firebase
 */
function logoutUser() {
  return firebase.auth().signOut().then(() => {
    // Após sair do Firebase, sai da sessão do servidor
    window.location.href = '/logout';
  });
}

/**
 * Obtém o usuário autenticado atual
 * @returns {Object|null} - Objeto do usuário Firebase ou null se não autenticado
 */
function getCurrentUser() {
  return firebase.auth().currentUser;
}

/**
 * Ouve mudanças no estado de autenticação
 * @param {Function} callback - Função de callback que recebe o objeto do usuário
 * @returns {Function} - Função para cancelar a escuta
 */
function onAuthStateChanged(callback) {
  return firebase.auth().onAuthStateChanged(callback);
}

// Escuta por mudanças de autenticação e atualiza a interface
document.addEventListener('DOMContentLoaded', function() {
  // Verifica se o Firebase está definido
  if (typeof firebase !== 'undefined' && firebase.apps.length > 0) {
    // Configura o botão de logout
    const logoutBtn = document.getElementById('logout-button');
    if (logoutBtn) {
      logoutBtn.addEventListener('click', function(e) {
        e.preventDefault();
        logoutUser();
      });
    }
    
    // Configura o formulário de login com e-mail e senha
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
            console.error("Erro no login:", error);
            alert("Erro ao fazer login: " + error.message);
          });
      });
    }
    
    // Configura o formulário de cadastro
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
            console.error("Erro no cadastro:", error);
            alert("Erro ao criar conta: " + error.message);
          });
      });
    }
  }
});

/**
 * Atualiza a navegação com base no estado de autenticação
 * @param {Object|null} user - Objeto do usuário Firebase ou null
 */
function updateNavigation(user) {
  const authNavItems = document.querySelectorAll('.auth-nav-item');
  const unauthNavItems = document.querySelectorAll('.unauth-nav-item');
  
  if (user) {
    // Usuário autenticado
    authNavItems.forEach(item => item.style.display = 'block');
    unauthNavItems.forEach(item => item.style.display = 'none');
    
    // Atualiza o nome do usuário se estiver disponível
    const userNameElement = document.getElementById('user-name');
    if (userNameElement && user.displayName) {
      userNameElement.textContent = user.displayName;
    }
  } else {
    // Usuário não autenticado
    authNavItems.forEach(item => item.style.display = 'none');
    unauthNavItems.forEach(item => item.style.display = 'block');
  }
}
