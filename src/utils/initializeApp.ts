export const initializeApp = () => {
  localStorage.removeItem('i18nextLng');
  
  if (!localStorage.getItem('sympai-language')) {
    localStorage.setItem('sympai-language', 'en-US');
  }
  if (!localStorage.getItem('sympai-theme')) {
    localStorage.setItem('sympai-theme', 'light');
  }
};
