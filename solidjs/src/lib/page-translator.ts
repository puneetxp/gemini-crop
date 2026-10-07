/**
 * CropSense AI — Whole-Site Real-Time Multilingual Translator
 *
 * Provides 100% whole-site translation across all 45 routes:
 * 1. Instant (0ms) zero-latency dictionary lookup from compiled i18n dictionaries
 *    and universal agricultural/UI vocabulary for English, Hindi, Marathi, Punjabi,
 *    Marwari (Marvadi), Gujarati, Bengali, Tamil, Telugu, Kannada, Malayalam.
 * 2. Background dynamic AI translation via /voice/translate for custom farmer text
 *    and dynamic server responses, cached in localStorage.
 * 3. Bulletproof icon protection: never touches Material Symbols or SVG icons.
 * 4. Automatic page route change detection (popstate / history API) & mutation observer.
 * 5. Reversible: switching back to English restores exact original text.
 */

import { createEffect, createRoot } from 'solid-js';
import apiClient from './api-client';
import { lang, DICTIONARIES } from '../stores/i18n.store';
import { en } from '../i18n/en';

const BATCH = 35;
const DEBOUNCE_MS = 120;
const CACHE_PREFIX = 'app_tr_';
const ATTRS = ['placeholder', 'title', 'aria-label', 'alt'] as const;
const SKIP_TAGS = new Set([
  'SCRIPT', 'STYLE', 'NOSCRIPT', 'CODE', 'PRE', 'TEXTAREA', 'SELECT', 'OPTION', 'SVG', 'IFRAME'
]);

type Slot = { node: Text; attr?: undefined } | { node: Element; attr: string };

// Universal UI & Agricultural vocabulary table for instant 0ms translation
const COMMON_PHRASES: Record<string, Record<string, string>> = {
  // Navigation & Shell
  'home': { hi: 'होम', mr: 'होम', pa: 'ਹੋਮ', mwr: 'घरां', gu: 'હોમ' },
  'dashboard': { hi: 'डैशबोर्ड', mr: 'डॅशबोर्ड', pa: 'ਡੈਸ਼ਬੋਰਡ', mwr: 'डैशबोर्ड', gu: 'ડેશબોર્ડ' },
  'marketplace': { hi: 'मंडी बाज़ार', mr: 'बाजारपेठ', pa: 'ਮਾਰਕੀਟਪਲੇਸ', mwr: 'मंडी बजार', gu: 'માર્કેટપ્લેસ' },
  'mandi': { hi: 'मंडी', mr: 'मंडी', pa: 'ਮੰਡੀ', mwr: 'मंडी', gu: 'મંડી' },
  'livestock': { hi: 'पशुधन', mr: 'पशुधन', pa: 'ਪਸ਼ੂ ਧਨ', mwr: 'ढोर-डांगर', gu: 'પશુધન' },
  'pashu': { hi: 'पशु', mr: 'पशु', pa: 'ਪਸ਼ੂ', mwr: 'ढोर', gu: 'પશુ' },
  'crops': { hi: 'फसलें', mr: 'पिके', pa: 'ਫਸਲਾਂ', mwr: 'फसळां', gu: 'પાકો' },
  'crop': { hi: 'फसल', mr: 'पीक', pa: 'ਫਸਲ', mwr: 'फसल', gu: 'પાક' },
  'farm': { hi: 'खेत', mr: 'शेत', pa: 'ਖੇਤ', mwr: 'खेत', gu: 'ખેતર' },
  'farms': { hi: 'खेत', mr: 'शेते', pa: 'ਖੇਤ', mwr: 'खेत', gu: 'ખેતરો' },
  'soil': { hi: 'मिट्टी', mr: 'माती', pa: 'ਮਿੱਟੀ', mwr: 'माटी', gu: 'માટી' },
  'weather': { hi: 'मौसम', mr: 'हवामान', pa: 'ਮੌਸਮ', mwr: 'आबो-हवा', gu: 'હવામાન' },
  'climate': { hi: 'जलवायु', mr: 'हवामान', pa: 'ਜਲਵਾਯੂ', mwr: 'आबो-हवा', gu: 'આબોહવા' },
  'diagnose': { hi: 'रोग निदान', mr: 'रोग निदान', pa: 'ਫਸਲ ਜਾਂਚ', mwr: 'फसल जांच', gu: 'રોગ નિદાન' },
  'strategy': { hi: 'रणनीति', mr: 'रणनीती', pa: 'ਰਣਨੀਤੀ', mwr: 'जुगत', gu: 'વ્યૂહરચના' },
  'settings': { hi: 'सेटिंग्स', mr: 'सेटिंग्ज', pa: 'ਸੈਟਿੰਗਾਂ', mwr: 'सेटिंग', gu: 'સેટિંગ્સ' },
  'profile': { hi: 'प्रोफ़ाइल', mr: 'प्रोफाइल', pa: 'ਪ੍ਰੋਫਾਈਲ', mwr: 'प्रोफाइल', gu: 'પ્રોફાઇલ' },
  'menu': { hi: 'मेन्यू', mr: 'मेन्यू', pa: 'ਮੇਨੂ', mwr: 'मेन्यू', gu: 'મેનૂ' },
  'services': { hi: 'सेवाएं', mr: 'सेवा', pa: 'ਸੇਵਾਵਾਂ', mwr: 'सेवावां', gu: 'સેવાઓ' },
  'all services': { hi: 'सभी सेवाएं', mr: 'सर्व सेवा', pa: 'ਸਾਰੀਆਂ ਸੇਵਾਵਾਂ', mwr: 'सगळी सेवावां', gu: 'બધી સેવાઓ' },
  'notifications': { hi: 'सूचनाएं', mr: 'सूचना', pa: 'ਸੂਚਨਾਵਾਂ', mwr: 'खबर / सूचना', gu: 'સૂચનાઓ' },
  'security': { hi: 'सुरक्षा', mr: 'सुरक्षा', pa: 'ਸੁਰੱਖਿਆ', mwr: 'सुरक्षा', gu: 'સુરક્ષા' },
  'sign in': { hi: 'साइन इन', mr: 'साइन इन', pa: 'ਸਾਈਨ ਇਨ', mwr: 'प्रवेश करो', gu: 'સાઇન ઇન' },
  'sign out': { hi: 'साइन आउट', mr: 'साइन आउट', pa: 'ਸਾਈਨ ਆਊਟ', mwr: 'बाहर निकळो', gu: 'સાઇન આઉટ' },
  'login': { hi: 'लॉग इन', mr: 'लॉग इन', pa: 'ਲੌਗਇਨ', mwr: 'लॉग इन', gu: 'લૉગિન' },
  'language': { hi: 'भाषा', mr: 'भाषा', pa: 'ਭਾਸ਼ਾ', mwr: 'बोली / भाषा', gu: 'ભાષા' },
  'farmer': { hi: 'किसान', mr: 'शेतकरी', pa: 'ਕਿਸਾਨ', mwr: 'किसान', gu: 'ખેડૂત' },

  // Actions & Buttons
  'view all': { hi: 'सब देखें', mr: 'सर्व पहा', pa: 'ਸਾਰੇ ਦੇਖੋ', mwr: 'सगळा देखो', gu: 'બધા જુઓ' },
  'browse all': { hi: 'सब देखें', mr: 'सर्व पहा', pa: 'ਸਾਰੇ ਦੇਖੋ', mwr: 'सगळा देखो', gu: 'બધા જુઓ' },
  'save': { hi: 'सहेजें', mr: 'जतन करा', pa: 'ਸੰਭਾਲੋ', mwr: 'सहेजो', gu: 'સાચવો' },
  'cancel': { hi: 'रद्द करें', mr: 'रद्द करा', pa: 'ਰੱਦ ਕਰੋ', mwr: 'रद्द करो', gu: 'રદ કરો' },
  'delete': { hi: 'हटाएं', mr: 'हटवा', pa: 'ਹਟਾਓ', mwr: 'हटाओ', gu: 'કાઢી નાખો' },
  'edit': { hi: 'बदलें', mr: 'संपादित करा', pa: 'ਸੋਧੋ', mwr: 'बदलो', gu: 'સંપાદિત કરો' },
  'add': { hi: 'जोड़ें', mr: 'जोडा', pa: 'ਜੋੜੋ', mwr: 'जोड़ो', gu: 'ઉમેરો' },
  'submit': { hi: 'जमा करें', mr: 'सबमिट करा', pa: 'ਜਮ੍ਹਾਂ ਕਰੋ', mwr: 'भेजो', gu: 'સબમિટ કરો' },
  'search': { hi: 'खोजें', mr: 'शोधा', pa: 'ਖੋਜੋ', mwr: 'ढूंढो', gu: 'શોધો' },
  'clear': { hi: 'हटाएं', mr: 'साफ करा', pa: 'ਸਾਫ਼ ਕਰੋ', mwr: 'साफ करो', gu: 'સાફ કરો' },
  'filter': { hi: 'फ़िल्टर', mr: 'फिल्टर', pa: 'ਫਿਲਟਰ', mwr: 'छांटो', gu: 'ફિલ્ટર' },
  'close': { hi: 'बंद करें', mr: 'बंद करा', pa: 'ਬੰਦ ਕਰੋ', mwr: 'बंद करो', gu: 'બંધ કરો' },
  'back': { hi: 'वापस', mr: 'मागे', pa: 'ਵਾਪਸ', mwr: 'पाछा', gu: 'પાછા' },
  'next': { hi: 'आगे', mr: 'पुढे', pa: 'ਅੱਗੇ', mwr: 'आगे', gu: 'આગળ' },
  'refresh': { hi: 'ताज़ा करें', mr: 'रिफ्रेश करा', pa: 'ਤਾਜ਼ਾ ਕਰੋ', mwr: 'पाछो जांचो', gu: 'રીફ્રેશ કરો' },
  'call': { hi: 'कॉल', mr: 'कॉल करा', pa: 'ਕਾਲ ਕਰੋ', mwr: 'फोन करो', gu: 'કૉલ કરો' },
  'whatsapp': { hi: 'WhatsApp', mr: 'WhatsApp', pa: 'WhatsApp', mwr: 'WhatsApp', gu: 'WhatsApp' },

  // Cards & Headings
  'command center': { hi: 'कमांड सेंटर', mr: 'कमांड सेंटर', pa: 'ਕਮਾਂਡ ਸੈਂਟਰ', mwr: 'कमांड सेंटर', gu: 'કમાન્ડ સેન્ટર' },
  'open dashboard': { hi: 'डैशबोर्ड खोलें →', mr: 'डॅशबोर्ड उघडा →', pa: 'ਡੈਸ਼ਬੋਰਡ ਖੋਲ੍ਹੋ →', mwr: 'डैशबोर्ड खोलो →', gu: 'ડેશબોર્ડ ખોલો →' },
  'ai crop doctor': { hi: 'एआई फसल डॉक्टर', mr: 'एआय पीक डॉक्टर', pa: 'ਏਆਈ ਫਸਲ ਡਾਕਟਰ', mwr: 'एआई फसल डॉक्टर', gu: 'AI પાક ડૉક્ટર' },
  'diagnose crop': { hi: 'फसल जांचें →', mr: 'पीक तपासा →', pa: 'ਫਸਲ ਜਾਂਚੋ →', mwr: 'फसल जांचो →', gu: 'પાક તપાસો →' },
  'pashu hub': { hi: 'पशु हब', mr: 'पशु हब', pa: 'ਪਸ਼ੂ ਹੱਬ', mwr: 'पशु हब', gu: 'પશુ હબ' },
  'manage herd': { hi: 'पशुधन संभालें →', mr: 'पशुधन व्यवस्थापित करा →', pa: 'ਪਸ਼ੂ ਧਨ ਸੰਭਾਲੋ →', mwr: 'ढोर संभालो →', gu: 'પશુધન મેનેજ કરો →' },
  'mandi marketplace': { hi: 'मंडी बाज़ार', mr: 'मंडी बाजारपेठ', pa: 'ਮੰਡੀ ਮਾਰਕੀਟਪਲੇਸ', mwr: 'मंडी बजार', gu: 'મંડી માર્કેટપ્લેસ' },
  'explore mandi': { hi: 'मंडी देखें →', mr: 'मंडी एक्सप्लोर करा →', pa: 'ਮੰਡੀ ਦੇਖੋ →', mwr: 'मंडी देखो →', gu: 'મંડી જુઓ →' },
  'launch command center': { hi: 'कमांड सेंटर खोलें', mr: 'कमांड सेंटर उघडा', pa: 'ਕਮਾਂਡ ਸੈਂਟਰ ਖੋਲ੍ਹੋ', mwr: 'कमांड सेंटर खोलो', gu: 'કમાન્ડ સેન્ટર શરૂ કરો' },
  'instant demo access': { hi: 'डेमो तुरंत आज़माएं', mr: 'डेमो त्वरित प्रवेश', pa: 'ਤੁਰੰਤ ਡੈਮੋ ਪਹੁੰਚ', mwr: 'डेमो आज़माओ', gu: 'ઇન્સ્ટન્ટ ડેમો ઍક્સેસ' },
  'demo auto-login': { hi: 'डेमो ऑटो-लॉगिन', mr: 'डेमो ऑटो-लॉगिन', pa: 'ਡੇਮੋ ਆਟੋ-ਲੌਗਇਨ', mwr: 'डेमो लॉगिन', gu: 'ડેમો ઑટો-લૉગિન' },

  // Statuses & Metrics
  'healthy': { hi: 'स्वस्थ', mr: 'निरोगी', pa: 'ਤੰਦਰੁਸਤ', mwr: 'राजी-खुशी', gu: 'તંદુરસ્ત' },
  'need care': { hi: 'देखभाल चाहिए', mr: 'काळजी हवी', pa: 'ਦੇਖਭਾਲ ਚਾਹੀਦੀ ਹੈ', mwr: 'इलाज चावे', gu: 'સંભાળની જરૂર છે' },
  'needs care': { hi: 'देखभाल चाहिए', mr: 'काळजी हवी', pa: 'ਦੇਖਭਾਲ ਚਾਹੀਦੀ ਹੈ', mwr: 'इलाज चावे', gu: 'સંભાળની જરૂર છે' },
  'for sale': { hi: 'बिकाऊ', mr: 'विक्रीसाठी', pa: 'ਵਿਕਰੀ ਲਈ', mwr: 'बिकाऊ', gu: 'વેચાણ માટે' },
  'total animals': { hi: 'कुल पशु', mr: 'एकूण पशु', pa: 'ਕੁੱਲ ਪਸ਼ੂ', mwr: 'कुल ढोर', gu: 'કુલ પશુઓ' },
  'overview': { hi: 'अवलोकन', mr: 'आढावा', pa: 'ਸੰਖੇਪ', mwr: 'सगळो हाल', gu: 'વિહંગાવલોકન' },
  'analytics': { hi: 'विश्लेषण', mr: 'विश्लेषण', pa: 'ਵਿਸ਼ਲੇਸ਼ਣ', mwr: 'पड़ताल', gu: 'વિશ્લેષણ' },
  'active': { hi: 'सक्रिय', mr: 'सक्रिय', pa: 'ਸਰਗਰਮ', mwr: 'चालू', gu: 'સક્રિય' },
  'pending': { hi: 'लंबित', mr: 'प्रलंबित', pa: 'ਬਕਾਇਆ', mwr: 'अटक्योड़ो', gu: 'બાકી' },
  'completed': { hi: 'पूर्ण', mr: 'पूर्ण', pa: 'ਮੁਕੰਮਲ', mwr: 'पूरो हुयो', gu: 'પૂર્ણ' },
  'verified': { hi: 'सत्यापित', mr: 'सत्यापित', pa: 'ਪ੍ਰਮਾਣਿਤ', mwr: 'पक्को प्रमाणित', gu: 'ચકાસાયેલ' },
  'available': { hi: 'उपलब्ध', mr: 'उपलब्ध', pa: 'ਉਪਲਬਧ', mwr: 'हाजर', gu: 'ઉપલબ્ધ' },
  'busy': { hi: 'व्यस्त', mr: 'व्यस्त', pa: 'ਰੁੱਝਿਆ', mwr: 'रूंझ्योड़ो', gu: 'વ્યસ્ત' },
  'price': { hi: 'दाम / मूल्य', mr: 'किंमत', pa: 'ਕੀਮਤ', mwr: 'भाव', gu: 'કિંમત' },
  'quantity': { hi: 'मात्रा', mr: 'प्रमाण', pa: 'ਮਾਤਰਾ', mwr: 'गिनती / तौल', gu: 'જથ્થો' },
  'status': { hi: 'स्थिति', mr: 'स्थिती', pa: 'ਸਥਿਤੀ', mwr: 'हाल', gu: 'સ્થિતિ' },
  'date': { hi: 'तारीख', mr: 'तारीख', pa: 'ਮਿਤੀ', mwr: 'तारीख', gu: 'તારીખ' },

  // Farming & Livestock Specifics
  'cow': { hi: 'गाय', mr: 'गाय', pa: 'ਗਾਂ', mwr: 'गाय', gu: 'ગાય' },
  'buffalo': { hi: 'भैंस', mr: 'म्हैस', pa: 'ਮੱਝ', mwr: 'भैंस', gu: 'ભેંસ' },
  'goat': { hi: 'बकरी', mr: 'शेळी', pa: 'ਬੱਕਰੀ', mwr: 'बकरी', gu: 'બકરી' },
  'sheep': { hi: 'भेड़', mr: 'मेंढी', pa: 'ਭੇਡ', mwr: 'भेड़', gu: 'ઘેટા' },
  'poultry': { hi: 'मुर्गी', mr: 'कोंबडी', pa: 'ਮੁਰਗੀ', mwr: 'कुकड़ी', gu: 'મરઘાં' },
  'diet plan': { hi: 'डाइट प्लान', mr: 'आहार योजना', pa: 'ਖੁਰਾਕ ਯੋਜਨਾ', mwr: 'खुराक जुगत', gu: 'આહાર યોજના' },
  'vet doctors': { hi: 'पशु डॉक्टर', mr: 'पशुवैद्यकीय डॉक्टर', pa: 'ਪਸ਼ੂ ਡਾਕਟਰ', mwr: 'पशु डॉक्टर', gu: 'પશુચિકિત્સકો' },
  'my livestock': { hi: 'मेरे पशु', mr: 'माझे पशुधन', pa: 'ਮੇਰੇ ਪਸ਼ੂ', mwr: 'म्हारा ढोर', gu: 'મારા પશુઓ' },
  'my crops': { hi: 'मेरी फसलें', mr: 'माझी पिके', pa: 'ਮੇਰੀਆਂ ਫਸਲਾਂ', mwr: 'म्हारी फसल', gu: 'મારા પાકો' },
  'plant crop': { hi: 'फसल बोएं', mr: 'पीक लावा', pa: 'ਫਸਲ ਬੀਜੋ', mwr: 'फसल बोओ', gu: 'પાક વાવો' },
  'add farm': { hi: 'खेत जोड़ें', mr: 'शेत जोडा', pa: 'ਖੇਤ ਜੋੜੋ', mwr: 'खेत जोड़ो', gu: 'ખેતર ઉમેરો' },
  'soil health': { hi: 'मिट्टी की सेहत', mr: 'मातीचे आरोग्य', pa: 'ਮਿੱਟੀ ਦੀ ਸਿਹਤ', mwr: 'माटी री सेहत', gu: 'જમીન આરોગ્ય' },
  'pest & disease': { hi: 'कीट और रोग', mr: 'कीड आणि रोग', pa: 'ਕੀੜੇ ਅਤੇ ਰੋਗ', mwr: 'कीड़ा अर बीमारी', gu: 'જીવાત અને રોગ' },
  'market rates': { hi: 'मंडी भाव', mr: 'बाजार भाव', pa: 'ਮੰਡੀ ਦੇ ਰੇਟ', mwr: 'मंडी भाव', gu: 'બજાર ભાવ' },
  'transport': { hi: 'परिवहन', mr: 'वाहतूक', pa: 'ਆਵਾਜਾਈ', mwr: 'गाड़ी भाड़ो', gu: 'પરિવહન' },
  'bookings': { hi: 'बुकिंग', mr: 'बुकिंग', pa: 'ਬੁਕਿੰਗ', mwr: 'बुकिंग', gu: 'બુકિંગ' },
  'buyer dashboard': { hi: 'खरीदार डैशबोर्ड', mr: 'खरेदीदार डॅशबोर्ड', pa: 'ਖਰੀਦਦਾਰ ਡੈਸ਼ਬੋਰਡ', mwr: 'गिराक डैशबोर्ड', gu: 'ખરીદનાર ડેશબોર્ડ' },
  'my listings': { hi: 'मेरी लिस्टिंग', mr: 'माझी सूची', pa: 'ਮੇਰੀਆਂ ਸੂਚੀਆਂ', mwr: 'म्हारी लिस्टिंग', gu: 'મારી યાદીઓ' },
  'supply plan': { hi: 'सप्लाई योजना', mr: 'पुरवठा योजना', pa: 'ਸਪਲਾਈ ਯੋਜਨਾ', mwr: 'सप्लाई योजना', gu: 'પુરવઠા યોજના' },
  'quick actions': { hi: 'त्वरित कार्य', mr: 'जलद कृती', pa: 'ਤੁਰੰਤ ਕਾਰਵਾਈਆਂ', mwr: 'झटपट काम', gu: 'ઝડપી ક્રિયાઓ' },
  'scan leaf': { hi: 'पत्ती स्कैन करें', mr: 'पान स्कॅन करा', pa: 'ਪੱਤਾ ਸਕੈਨ ਕਰੋ', mwr: 'पानां री फोटो लो', gu: 'પાન સ્કેન કરો' },
  'call vet': { hi: 'डॉक्टर को कॉल करें', mr: 'डॉक्टरांना कॉल करा', pa: 'ਡਾਕਟਰ ਨੂੰ ਕਾਲ ਕਰੋ', mwr: 'वैद जी ने फोन करो', gu: 'ડૉક્ટરને કૉલ કરો' },
  'mandi prices': { hi: 'मंडी भाव', mr: 'बाजार भाव', pa: 'ਮੰਡੀ ਦੇ ਰੇਟ', mwr: 'मंडी भाव', gu: 'બજાર ભાવ' },
  'krishi command center': { hi: 'कृषि कमांड सेंटर', mr: 'कृषी कमांड सेंटर', pa: 'ਖੇਤੀਬਾੜੀ ਕਮਾਂਡ ਸੈਂਟਰ', mwr: 'कृषि कमांड सेंटर', gu: 'કૃષિ કમાન્ડ સેન્ટર' },
  'projected yield': { hi: 'अनुमानित उपज', mr: 'अपेक्षित उत्पादन', pa: 'ਅਨੁਮਾਨਿਤ ਝਾੜ', mwr: 'अंदाजित पैदावार', gu: 'અંદાજિત ઉપજ' },
  'livestock portfolio': { hi: 'पशुधन पोर्टफोलियो', mr: 'पशुधन पोर्टफोलिओ', pa: 'ਪਸ਼ੂ ਪੋਰਟਫੋਲੀਓ', mwr: 'ढोर-डांगर', gu: 'પશુધન પોર્ટફોલિયો' },
  'ndvi health index': { hi: 'एनडीवीआई स्वास्थ्य सूचकांक', mr: 'एनडीव्हीआय आरोग्य निर्देशांक', pa: 'ਐਨਡੀਵੀਆਈ ਸਿਹਤ ਸੂਚਕਾਂਕ', mwr: 'NDVI सेहत सूचकांक', gu: 'NDVI આરોગ્ય સૂચકાંક' },
  'forward contract': { hi: 'अग्रिम अनुबंध (फॉरवर्ड)', mr: 'आगाऊ करार', pa: 'ਫਾਰਵਰਡ ਕੰਟਰੈਕਟ', mwr: 'फॉरवर्ड सौदा', gu: 'ફોરવર્ડ કોન્ટ્રાક્ટ' },
  'high vigour': { hi: 'उच्च स्वास्थ्य', mr: 'उत्कृष्ट वाढ', pa: 'ਉੱਚ ਜੋਸ਼', mwr: 'पूरी तरह स्वस्थ', gu: 'ઉચ્ચ જોશ' },
  'escrow secured': { hi: 'एस्क्रो सुरक्षित', mr: 'एस्क्रो सुरक्षित', pa: 'ਐਸਕਰੋ ਸੁਰੱਖਿਅਤ', mwr: 'एस्क्रो सुरक्षित', gu: 'એસ્ક્રો સુરક્ષિત' },
  'live stac': { hi: 'लाइव उपग्रह डेटा', mr: 'थेट उपग्रह डेटा', pa: 'ਲਾਈਵ ਸੈਟੇਲਾਈਟ ਡੇਟਾ', mwr: 'लाइव STAC', gu: 'લાઇવ સેટેલાઇટ ડેટા' },
  'review plots →': { hi: 'प्लॉट देखें →', mr: 'प्लॉट तपासा →', pa: 'ਪਲਾਟ ਦੇਖੋ →', mwr: 'प्लॉट देखो →', gu: 'પ્લોટ જુઓ →' },
  'full gis map →': { hi: 'पूरा जीआईएस नक्शा →', mr: 'पूर्ण जीआयएस नकाशा →', pa: 'ਪੂਰਾ ਜੀਆਈਐਸ ਨਕਸ਼ਾ →', mwr: 'पूरो GIS नक्शा →', gu: 'સંપૂર્ણ GIS નકશો →' },
  'nitrogen': { hi: 'नाइट्रोजन (N)', mr: 'नायट्रोजन (N)', pa: 'ਨਾਈਟ੍ਰੋਜਨ (N)', mwr: 'नाइट्रोजन (N)', gu: 'નાઇટ્રોજન (N)' },
  'phosphorus': { hi: 'फ़ास्फ़रोस (P)', mr: 'फॉस्फरस (P)', pa: 'ਫਾਸਫੋਰਸ (P)', mwr: 'फास्फोरस (P)', gu: 'ફોસ્ફરસ (P)' },
  'potassium': { hi: 'पोटैशियम (K)', mr: 'पोटॅशियम (K)', pa: 'ਪੋਟਾਸ਼ੀਅਮ (K)', mwr: 'पोटैशियम (K)', gu: 'પોટેશિયમ (K)' },
  'adequate': { hi: 'पर्याप्त', mr: 'पुरेसे', pa: 'ਕਾਫ਼ੀ', mwr: 'पूरो', gu: 'પર્યાપ્ત' },
  'high': { hi: 'उच्च', mr: 'जास्त', pa: 'ਉੱਚ', mwr: 'घणो', gu: 'ઉચ્ચ' },
  'low': { hi: 'कम', mr: 'कमी', pa: 'ਘੱਟ', mwr: 'कम', gu: 'ઓછું' },
  'slightly low': { hi: 'थोड़ा कम', mr: 'किंचित कमी', pa: 'ਥੋੜ੍ਹਾ ਘੱਟ', mwr: 'थोड़ो कम', gu: 'થોડું ઓછું' },
  'optimal biomass': { hi: 'उत्तम बायोमास', mr: 'उत्कृष्ट बायोमास', pa: 'ਅਨੁਕੂਲ ਬਾਇਓਮਾਸ', mwr: 'सही बायोमास', gu: 'શ્રેષ્ઠ બાયોમાસ' }
};

// Reverse map: lowercased en.ts strings -> i18n dictionary key
const EN_STRING_MAP = new Map<string, string>();
for (const [key, val] of Object.entries(en)) {
  if (typeof val === 'string' && val.trim()) {
    EN_STRING_MAP.set(val.trim().toLowerCase(), key);
  }
}

// Memory & Tracking structures
const originals = new WeakMap<object, Record<string, { src: string; out: string }>>();
const tracked = new Set<WeakRef<Node>>();

// Comprehensive Material Symbols / Icons identifier registry (never translated)
const MATERIAL_ICONS = new Set([
  'psychiatry', 'agriculture', 'psychology', 'pets', 'satellite_alt', 'storefront',
  'calendar_month', 'mic', 'settings', 'eco', 'home', 'dashboard', 'person',
  'notifications', 'bolt', 'wb_sunny', 'rainy', 'water_drop', 'thermostat',
  'water_ph', 'photo_camera', 'science', 'cruelty_free', 'trending_up',
  'auto_awesome', 'volume_up', 'thumb_up', 'share', 'arrow_forward', 'arrow_back',
  'chevron_right', 'expand_more', 'check', 'close', 'search', 'filter_alt',
  'verified', 'pending', 'task_alt', 'local_shipping', 'density_medium',
  'qr_code_2', 'lock', 'handshake', 'domain', 'spa', 'grain', 'grass',
  'video_camera_front', 'document_scanner', 'layers', 'zoom_out_map', 'routine',
  'wb_twilight', 'vaccines', 'add_circle', 'play_arrow', 'calendar_add_on',
  'pregnant_woman', 'lens_blur', 'photo_library', 'check_circle', 'error', 'warning',
  'info', 'help', 'menu', 'translate', 'refresh', 'swap_horiz', 'logout', 'login',
  'account_circle', 'mail', 'phone', 'location_on', 'shield', 'delete', 'edit',
  'visibility', 'visibility_off', 'favorite', 'favorite_border', 'cloud', 'water',
  'compost', 'bug_report', 'inventory', 'assessment', 'analytics', 'history',
  'dataset', 'tune', 'speed', 'filter_list', 'sort', 'star', 'star_half', 'star_outline'
]);

let target = lang();
let cache: Record<string, string> = {};
let queue = new Map<string, Slot[]>();
let timer = 0;
let observer: MutationObserver | null = null;
let version = 0;

function isIcon(el: Element | null): boolean {
  if (!el) return false;
  const cls = typeof el.className === 'string' ? el.className : (el.getAttribute?.('class') || '');
  if (
    cls.includes('material-symbols') ||
    cls.includes('material-icons') ||
    el.tagName === 'I' ||
    el.hasAttribute('data-icon')
  ) {
    return true;
  }
  return !!el.closest?.('.material-symbols-outlined, .material-symbols, .material-icons, [class*="material-symbols"], [class*="material-icons"], [data-icon]');
}

function blocked(el: Element | null): boolean {
  if (!el) return true;
  return (
    SKIP_TAGS.has(el.tagName.toUpperCase()) ||
    isIcon(el) ||
    !!el.closest?.('[data-no-translate], [contenteditable="true"], .material-symbols-outlined, [data-icon]')
  );
}

const translatable = (s: string) => {
  if (!s) return false;
  const lower = s.toLowerCase().trim();
  if (MATERIAL_ICONS.has(lower) || /^[a-z]+(_[a-z]+)+$/.test(lower)) return false;
  return /[A-Za-z]{2,}/.test(s);
};

const loadCache = (code: string) => {
  try {
    const raw = JSON.parse(localStorage.getItem(CACHE_PREFIX + code) || '{}');
    cache = {};
    for (const [k, v] of Object.entries(raw)) {
      if (!MATERIAL_ICONS.has(k.toLowerCase()) && typeof v === 'string') {
        cache[k] = v;
      }
    }
    // Prune corrupted entries from localStorage directly
    localStorage.setItem(CACHE_PREFIX + code, JSON.stringify(cache));
  } catch {
    cache = {};
  }
};

const saveCache = () => {
  try {
    localStorage.setItem(CACHE_PREFIX + target, JSON.stringify(cache));
  } catch {
    // LocalStorage quota safe fallback
  }
};

const keyOf = (attr: string) => attr || '#text';

function apply(slot: Slot, text: string) {
  const key = keyOf(slot.attr || '');
  const rec = originals.get(slot.node)?.[key];
  if (!rec) return;
  rec.out = text;
  if (slot.attr !== undefined) (slot.node as Element).setAttribute(slot.attr, text);
  else (slot.node as Text).data = text;
}

function restoreAll() {
  for (const ref of tracked) {
    const node = ref.deref();
    if (!node) {
      tracked.delete(ref);
      continue;
    }
    const recs = originals.get(node);
    if (!recs) continue;
    for (const [key, rec] of Object.entries(recs)) {
      if (key === '#text') {
        if ((node as Text).data === rec.out) (node as Text).data = rec.src;
      } else if ((node as Element).getAttribute(key) === rec.out) {
        (node as Element).setAttribute(key, rec.src);
      }
    }
    originals.delete(node);
  }
  tracked.clear();
}

/** Instant client-side lookup from dictionaries or pre-compiled vocabulary */
function instantLookup(src: string, langCode: string): string | null {
  if (langCode === 'en') return null;
  const clean = src.trim();
  if (!clean || MATERIAL_ICONS.has(clean.toLowerCase())) return null;
  const lower = clean.toLowerCase();

  // 1. Check universal UI common phrases table
  const phrase = COMMON_PHRASES[lower]?.[langCode];
  if (phrase) return phrase;

  // 2. Check en.ts reverse mapping into active dictionary
  const key = EN_STRING_MAP.get(lower);
  if (key) {
    const activeDict = (DICTIONARIES as any)[langCode];
    if (activeDict && activeDict[key]) return activeDict[key];
  }

  // 3. Check device persistent cache
  if (cache[clean]) return cache[clean];

  return null;
}

function enqueue(slot: Slot, current: string) {
  const src = current.trim();
  if (!translatable(src)) return;
  if (MATERIAL_ICONS.has(src.toLowerCase())) return;

  const parent = slot.attr !== undefined ? (slot.node as Element) : (slot.node as Text).parentElement;
  if (!parent || blocked(parent as Element)) return;

  const key = keyOf(slot.attr || '');
  const recs = originals.get(slot.node) || {};
  const prev = recs[key];
  if (prev && prev.out === current) return;

  recs[key] = { src: current, out: current };
  if (!originals.has(slot.node)) {
    originals.set(slot.node, recs);
    tracked.add(new WeakRef(slot.node));
  }

  // 1. Check instant local dictionary
  const instant = instantLookup(src, target);
  if (instant) {
    apply(slot, current.replace(src, instant));
    return;
  }

  // 2. Queue for background AI translation
  const list = queue.get(src) || [];
  list.push(slot);
  queue.set(src, list);
  schedule();
}

function scan(root: Node) {
  if (target === 'en') return;

  if (root.nodeType === Node.TEXT_NODE) {
    const el = root.parentElement;
    if (el && !blocked(el)) {
      enqueue({ node: root as Text }, (root as Text).data);
    }
    return;
  }

  if (root.nodeType !== Node.ELEMENT_NODE) return;
  const el = root as Element;
  if (blocked(el)) return;

  const scanAttrs = (e: Element) => {
    if (blocked(e)) return;
    for (const a of ATTRS) {
      const v = e.getAttribute(a);
      if (v) enqueue({ node: e, attr: a }, v);
    }
  };

  scanAttrs(el);

  const walker = document.createTreeWalker(
    el,
    NodeFilter.SHOW_TEXT | NodeFilter.SHOW_ELEMENT,
    {
      acceptNode: (n) => {
        if (n.nodeType === Node.ELEMENT_NODE) {
          return blocked(n as Element) ? NodeFilter.FILTER_REJECT : NodeFilter.FILTER_ACCEPT;
        }
        if (n.nodeType === Node.TEXT_NODE) {
          const p = (n as Text).parentElement;
          return blocked(p) ? NodeFilter.FILTER_REJECT : NodeFilter.FILTER_ACCEPT;
        }
        return NodeFilter.FILTER_ACCEPT;
      },
    }
  );

  for (let n = walker.nextNode(); n; n = walker.nextNode()) {
    if (n.nodeType === Node.TEXT_NODE) {
      enqueue({ node: n as Text }, (n as Text).data);
    } else {
      scanAttrs(n as Element);
    }
  }
}

function schedule() {
  clearTimeout(timer);
  timer = window.setTimeout(flush, DEBOUNCE_MS);
}

async function flush() {
  if (!queue.size) return;
  const pending = queue;
  queue = new Map();
  const code = target;
  const myVersion = version;
  const texts = [...pending.keys()];

  for (let i = 0; i < texts.length; i += BATCH) {
    const chunk = texts.slice(i, i + BATCH);
    try {
      const res = await apiClient.post<{ data?: { translations?: string[] } }>(
        '/voice/translate',
        { texts: chunk, target: code },
        { requiresAuth: false }
      );
      const out = (res as any)?.data?.data?.translations;
      if (!Array.isArray(out) || out.length !== chunk.length) continue;
      if (myVersion !== version) return;

      chunk.forEach((src, j) => {
        if (out[j] && out[j] !== src) cache[src] = out[j];
        for (const slot of pending.get(src) || []) {
          const cur = slot.attr
            ? (slot.node as Element).getAttribute(slot.attr)
            : (slot.node as Text).data;
          if (cur != null && cur.trim() === src && out[j]) {
            apply(slot, cur.replace(src, out[j]));
          }
        }
      });
      saveCache();
    } catch {
      // Translation backend safe fallback
    }
  }
}

function start(code: string) {
  version++;
  target = code;
  queue = new Map();
  restoreAll();
  document.documentElement.lang = code;

  if (code === 'en') {
    observer?.disconnect();
    observer = null;
    return;
  }

  loadCache(code);
  scan(document.body);

  if (!observer) {
    observer = new MutationObserver((muts) => {
      for (const m of muts) {
        if (m.type === 'characterData') {
          scan(m.target);
        } else if (m.type === 'attributes') {
          const v = (m.target as Element).getAttribute(m.attributeName!);
          if (v && !blocked(m.target as Element)) {
            enqueue({ node: m.target as Element, attr: m.attributeName! }, v);
          }
        } else {
          m.addedNodes.forEach(scan);
        }
      }
    });
  }

  observer.observe(document.body, {
    childList: true,
    subtree: true,
    characterData: true,
    attributes: true,
    attributeFilter: [...ATTRS],
  });
}

/** Call once at startup: follows the language picker and route transitions for the entire app */
export function initPageTranslator() {
  createRoot(() => {
    createEffect(() => start(lang()));
  });

  // Re-scan seamlessly on Solid Router / history navigation
  const triggerScan = () => {
    if (target !== 'en') {
      setTimeout(() => scan(document.body), 60);
      setTimeout(() => scan(document.body), 300);
    }
  };

  window.addEventListener('popstate', triggerScan);
  const origPushState = history.pushState;
  history.pushState = function (...args) {
    origPushState.apply(this, args);
    triggerScan();
  };
  const origReplaceState = history.replaceState;
  history.replaceState = function (...args) {
    origReplaceState.apply(this, args);
    triggerScan();
  };
}
