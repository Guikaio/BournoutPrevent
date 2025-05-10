/**
 * Configuração do Firebase para o Sistema de Prevenção ao Burnout
 * Este arquivo inicializa o Firebase e gerencia as funções de autenticação
 */

// Inicializa o Firebase com as configurações fornecidas
function initializeFirebase(apiKey, projectId, appId) {
  const firebaseConfig = {
    apiKey: apiKey,
    authDomain: `${projectId}.firebaseapp.com`,
    projectId: projectId,
    storageBucket: `${projectId}.appspot.com`,
    messagingSenderId: "123456789012", // Placeholder, não utilizamos mensagens
    appId: appId
  };

  // Inicializa o Firebase apenas se ainda não estiver inicializado
  if (!firebase.apps.length) {
    firebase.initializeApp(firebaseConfig);
  }

  console.log("Firebase inicializado com sucesso");

  // Inicia o listener de autenticação
  setupAuthListener();
}

// Configura o ouvinte para mudanças no estado de autenticação
function setupAuthListener() {
  firebase.auth().onAuthStateChanged((user) => {
    updateNavigation(user);

    if (user) {
      // Usuário está logado
      console.log("Usuário logado:", user.displayName);

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
          console.error("Erro ao comunicar com o servidor:", error);
        });
      }
    } else {
      // Usuário está deslogado
      console.log("Usuário deslogado");
    }
  });
}

// Registra um novo usuário com email e senha
function registerUser(email, password, name) {
  return firebase.auth().createUserWithEmailAndPassword(email, password)
    .then((userCredential) => {
      // Atualiza o nome do usuário
      return userCredential.user.updateProfile({
        displayName: name
      }).then(() => {
        return userCredential;
      });
    });
}

// Realiza login com email e senha
function loginUser(email, password) {
  return firebase.auth().signInWithEmailAndPassword(email, password);
}

// Realiza login com conta do Google
function signInWithGoogle() {
  const provider = new firebase.auth.GoogleAuthProvider();
  return firebase.auth().signInWithPopup(provider);
}

// Faz logout do usuário atual
function logoutUser() {
  return firebase.auth().signOut().then(() => {
    // Após o logout no Firebase, redireciona para o logout do servidor
    window.location.href = '/logout';
  });
}

// Retorna o usuário autenticado atual
function getCurrentUser() {
  return firebase.auth().currentUser;
}

// Escuta mudanças na autenticação e chama o callback fornecido
function onAuthStateChanged(callback) {
  return firebase.auth().onAuthStateChanged(callback);
}

// Ao carregar a página, configura os eventos de autenticação
document.addEventListener('DOMContentLoaded', function() {
  if (typeof firebase !== 'undefined' && firebase.apps.length > 0) {
    // Botão de logout
    const logoutBtn = document.getElementById('logout-button');
    if (logoutBtn) {
      logoutBtn.addEventListener('click', function(e) {
        e.preventDefault();
        logoutUser();
      });
    }

    // Formulário de login
    const loginForm = document.getElementById('login-form');
    if (loginForm) {
      loginForm.addEventListener('submit', function(e) {
        e.preventDefault();

        if (!validateLoginForm()) return;

        const email = document.getElementById('email').value;
        const password = document.getElementById('password').value;

        loginUser(email, password)
          .catch(error => {
            console.error("Erro no login:", error);
            alert("Erro ao fazer login: " + error.message);
          });
      });
    }

    // Formulário de cadastro
    const registrationForm = document.getElementById('registration-form');
    if (registrationForm) {
      registrationForm.addEventListener('submit', function(e) {
        e.preventDefault();

        if (!validateRegistrationForm()) return;

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

// Atualiza a navegação com base na autenticação
function updateNavigation(user) {
  const authNavItems = document.querySelectorAll('.auth-nav-item');
  const unauthNavItems = document.querySelectorAll('.unauth-nav-item');

  if (user) {
    // Exibe itens para usuários autenticados
    authNavItems.forEach(item => item.style.display = 'block');
    unauthNavItems.forEach(item => item.style.display = 'none');

    // Atualiza o nome do usuário no menu
    const userNameElement = document.getElementById('user-name');
    if (userNameElement && user.displayName) {
      userNameElement.textContent = user.displayName;
    }
  } else {
    // Exibe itens para visitantes
    authNavItems.forEach(item => item.style.display = 'none');
    unauthNavItems.forEach(item => item.style.display = 'block');
  }
}
