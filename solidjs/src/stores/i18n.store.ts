import { createSignal, createMemo } from "solid-js";

export type SupportedLanguage = "en" | "hi" | "mr" | "pa";

const translations: Record<SupportedLanguage, Record<string, string>> = {
  en: {
    "app.title": "CropSense AI",
    "nav.home": "Home",
    "nav.dashboard": "Dashboard",
    "nav.farms": "Farms",
    "nav.diagnose": "AI Doctor",
    "nav.livestock": "Pashu Hub",
    "nav.soil": "Soil & Satellite",
    "nav.marketplace": "Marketplace",
    "nav.bookings": "Advance Bookings",
    "nav.strategy": "Annual Strategy",
    "nav.assistant": "AI Voice Assistant",
    "nav.settings": "Settings",
    "auth.signin": "Sign In",
    "auth.signup": "Sign Up",
    "auth.signout": "Sign Out",
    "status.offline": "You are currently offline. Changes will sync when connected.",
    "status.connected": "Online",
    "action.refresh": "Refresh",
    "action.save": "Save Changes",
    "action.cancel": "Cancel",
  },
  hi: {
    "app.title": "क्रॉपसेंस एआई",
    "nav.home": "होम",
    "nav.dashboard": "डैशबोर्ड",
    "nav.farms": "खेत",
    "nav.diagnose": "फसल डॉक्टर",
    "nav.livestock": "पशु हब",
    "nav.soil": "मृदा व उपग्रह",
    "nav.marketplace": "मंडी / बाज़ार",
    "nav.bookings": "अग्रिम अनुबंध",
    "nav.strategy": "वार्षिक रणनीति",
    "nav.assistant": "आवाज़ सहायक",
    "nav.settings": "सेटिंग्स",
    "auth.signin": "लॉग इन",
    "auth.signup": "साइन अप",
    "auth.signout": "लॉग आउट",
    "status.offline": "आप अभी ऑफलाइन हैं। नेटवर्क आने पर बदलाव सिंक होंगे।",
    "status.connected": "ऑनलाइन",
    "action.refresh": "ताज़ा करें",
    "action.save": "सुरक्षित करें",
    "action.cancel": "रद्द करें",
  },
  mr: {
    "app.title": "क्रॉपसेन्स एआय",
    "nav.home": "मुख्यपृष्ठ",
    "nav.dashboard": "डॅशबोर्ड",
    "nav.farms": "शेतजमीन",
    "nav.diagnose": "पीक डॉक्टर",
    "nav.livestock": "पशु हब",
    "nav.soil": "माती व उपग्रह",
    "nav.marketplace": "बाजारपेठ",
    "nav.bookings": "आगाऊ करार",
    "nav.strategy": "वार्षिक नियोजन",
    "nav.assistant": "व्हॉइस असिस्टंट",
    "nav.settings": "सेटिंग्ज",
    "auth.signin": "साइन इन",
    "auth.signup": "नोंदणी",
    "auth.signout": "लॉग आउट",
    "status.offline": "तुम्ही ऑफलाइन आहात. कनेक्टिव्हिटी आल्यावर बदल सेव्ह होतील.",
    "status.connected": "ऑनलाइन",
    "action.refresh": "रिफ्रेश",
    "action.save": "जतन करा",
    "action.cancel": "रद्द करा",
  },
  pa: {
    "app.title": "ਕ੍ਰੌਪਸੈਂਸ ਏਆਈ",
    "nav.home": "ਮੁੱਖ ਪੰਨਾ",
    "nav.dashboard": "ਡੈਸ਼ਬੋਰਡ",
    "nav.farms": "ਖੇਤ",
    "nav.diagnose": "ਫ਼ਸਲ ਡਾਕਟਰ",
    "nav.livestock": "ਪਸ਼ੂ ਹੱਬ",
    "nav.soil": "ਮਿੱਟੀ ਤੇ ਸੈਟੇਲਾਈਟ",
    "nav.marketplace": "ਮੰਡੀ",
    "nav.bookings": "ਐਡਵਾਂਸ ਬੁਕਿੰਗ",
    "nav.strategy": "ਸਾਲਾਨਾ ਰਣਨੀਤੀ",
    "nav.assistant": "ਵੌਇਸ ਅਸਿਸਟੈਂਟ",
    "nav.settings": "ਸੈਟਿੰਗਾਂ",
    "auth.signin": "ਲਾਗਇਨ",
    "auth.signup": "ਸਾਇਨ ਅੱਪ",
    "auth.signout": "ਲਾਗ ਆਉਟ",
    "status.offline": "ਤੁਸੀਂ ਆਫਲਾਈਨ ਹੋ। ਨੈੱਟਵਰਕ ਆਉਣ 'ਤੇ ਬਦਲਾਅ ਸੇਵ ਹੋਣਗੇ।",
    "status.connected": "ਔਨਲਾਈਨ",
    "action.refresh": "ਤਾਜ਼ਾ ਕਰੋ",
    "action.save": "ਸੰਭਾਲੋ",
    "action.cancel": "ਰੱਦ ਕਰੋ",
  },
};

const initialLang = (localStorage.getItem("app_lang") as SupportedLanguage) || "en";
const [lang, setLangState] = createSignal<SupportedLanguage>(initialLang);

export const currentLanguage = createMemo(() => lang());

export function setLanguage(newLang: SupportedLanguage): void {
  setLangState(newLang);
  localStorage.setItem("app_lang", newLang);
}

export function t(key: string): string {
  const current = lang();
  return translations[current]?.[key] || translations.en[key] || key;
}
