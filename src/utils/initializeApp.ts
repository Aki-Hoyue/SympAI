export const initializeApp = () => {
  if (!localStorage.getItem('i18nextLng')) {
    localStorage.setItem('sympai-language', 'en-US');
  }
  if (!localStorage.getItem('sympai-theme')) {
    localStorage.setItem('sympai-theme', 'light');
  }
};
