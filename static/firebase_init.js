// Initialize Firebase
firebase.initializeApp(firebaseConfig);
const auth = firebase.auth();

// Toast notification function
function showToast(message, type = 'success') {
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.innerHTML = `<span>${message}</span>${type === 'loading' ? '<div class="loader"></div>' : ''}`;
  document.body.appendChild(toast);
  if (type !== 'loading') {
    setTimeout(() => {
      toast.style.animation = 'slideIn 0.3s ease-out reverse';
      setTimeout(() => toast.remove(), 300);
    }, 3000);
  }
  return toast;
}