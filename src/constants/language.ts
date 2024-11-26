// languages that have translation files in `public/locales`
export const i18nLanguages = [
  'en-US',
  'zh-CN',
  'zh-TW',
  'da',
  'de',
  'es',
  'fr',
  'it',
  'ja',
  'ms',
  'nb',
  'ro',
  'ru',
  'sv',
] as const;

// languages that are selectable on the web page
export const selectableLanguages = [
  'en-US',
  'zh-CN',
  'zh-TW',
  'da',
  'de',
  'es',
  'fr',
  'it',
  'ja',
  'ms',
  'nb',
  'ro',
  'ru',
  'sv',
] as const;

export const languageCodeToName = {

  'en-US': 'English',
  'zh-CN': '中文（简体）',
  'zh-TW': '中文（繁体）',
  'da': 'Dansk',
  'de': 'Deutsch',
  'es': 'Español',
  'fr': 'Français',
  'it': 'Italiano',
  'ja': '日本語',
  'ms': 'Bahasa Melayu',
  'nb': 'Norsk bokmål',
  'ro': 'Română',
  'ru': 'Русский',
  'sv': 'Svenska',
};
