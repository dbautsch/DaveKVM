// Copyright (c) 2026 Dawid Bautsch
// SPDX-License-Identifier: MIT
// Source for the inline translation block in index.html.
const translations = {
  'Language / Język': ['Language', 'Sprache', 'Jazyk'],
  'LOKALNY PODGLĄD': ['LOCAL PREVIEW', 'LOKALE VORSCHAU', 'MÍSTNÍ NÁHLED'],
  'Podgląd na żywo': ['Live preview', 'Live-Vorschau', 'Živý náhled'],
  'Wybierz urządzenie, aby zobaczyć obraz z wejścia HDMI.': ['Select a device to view its HDMI input.', 'Wähle ein Gerät für das HDMI-Bild.', 'Vyberte zařízení pro zobrazení vstupu HDMI.'],
  'Podłączone urządzenia': ['Connected devices', 'Verbundene Geräte', 'Připojená zařízení'],
  'Wyszukiwanie…': ['Searching…', 'Suche…', 'Vyhledávání…'],
  'Wybierz grabber z listy': ['Select a capture device', 'Aufnahmegerät auswählen', 'Vyberte snímací zařízení'],
  'Włącz sterowanie': ['Enable control', 'Steuerung aktivieren', 'Zapnout ovládání'],
  'Wyłącz sterowanie': ['Disable control', 'Steuerung deaktivieren', 'Vypnout ovládání'],
  'Przechwyć mysz': ['Capture mouse', 'Maus erfassen', 'Zachytit myš'],
  'Zwolnij mysz (Ctrl+Alt)': ['Release mouse (Ctrl+Alt)', 'Maus freigeben (Strg+Alt)', 'Uvolnit myš (Ctrl+Alt)'],
  'Pełny ekran ⛶': ['Fullscreen ⛶', 'Vollbild ⛶', 'Celá obrazovka ⛶'],
  'Obraz': ['Video', 'Bild', 'Obraz'],
  'Oryginalny grabber (MJPEG)': ['Original capture (MJPEG)', 'Originalaufnahme (MJPEG)', 'Původní záznam (MJPEG)'],
  'Profil QSV': ['QSV profile', 'QSV-Profil', 'Profil QSV'],
  'Tryb QSV': ['QSV mode', 'QSV-Modus', 'Režim QSV'],
  'ICQ (bez limitu Mb/s)': ['ICQ (unlimited Mb/s)', 'ICQ (ohne Mb/s-Limit)', 'ICQ (bez omezení Mb/s)'],
  'Jakość QSV (1 najlepsza)': ['QSV quality (1 is best)', 'QSV-Qualität (1 ist am besten)', 'Kvalita QSV (1 je nejlepší)'],
  'Klatka kluczowa co (kl.)': ['Keyframe interval (frames)', 'Keyframe-Abstand (Bilder)', 'Interval klíčových snímků'],
  'W VBR maksimum wynosi dwukrotność wartości, najwyżej 30 Mb/s': ['VBR maximum is twice the target, up to 30 Mb/s', 'VBR-Maximum: doppelter Zielwert, höchstens 30 Mb/s', 'Maximum VBR je dvojnásobek cíle, nejvýše 30 Mb/s'],
  'Zastosuj': ['Apply', 'Anwenden', 'Použít'],
  'Sterowanie': ['Control', 'Steuerung', 'Ovládání'],
  'Zamknij pełny ekran': ['Exit fullscreen', 'Vollbild verlassen', 'Ukončit celou obrazovku'],
  'Tutaj pojawi się obraz': ['Video appears here', 'Hier erscheint das Bild', 'Zde se zobrazí obraz'],
  'Obraz na żywo z grabbera': ['Live capture video', 'Live-Bild des Aufnahmegeräts', 'Živý obraz ze zařízení'],
  'Oryginalny obraz z grabbera': ['Original capture video', 'Originalbild des Aufnahmegeräts', 'Původní obraz ze zařízení'],
  'Wybierz grabber, aby sterować przypisaną klawiaturą.': ['Select a device to control its keyboard.', 'Wähle ein Gerät zur Tastatursteuerung.', 'Vyberte zařízení pro ovládání jeho klávesnice.'],
  'Nie udało się połączyć z klawiaturą.': ['Could not connect to the keyboard.', 'Verbindung zur Tastatur fehlgeschlagen.', 'Nelze připojit klávesnici.'],
  'Do tego grabbera nie przypisano klawiatury': ['No keyboard is assigned to this device', 'Diesem Gerät ist keine Tastatur zugeordnet', 'K tomuto zařízení není přiřazena klávesnice'],
  'Klawiatura jest zajęta przez innego użytkownika': ['Keyboard is in use by another user', 'Tastatur wird von einem anderen Benutzer verwendet', 'Klávesnici používá jiný uživatel'],
  'Nie można połączyć się z CH9329': ['Could not connect to CH9329', 'Verbindung zu CH9329 fehlgeschlagen', 'Nelze se připojit k CH9329'],
  'Sterowanie wygasło lub jest zajęte': ['Control has expired or is busy', 'Steuerung ist abgelaufen oder belegt', 'Ovládání vypršelo nebo je obsazené'],
  'Sterowanie wygasło': ['Control has expired', 'Steuerung ist abgelaufen', 'Ovládání vypršelo'],
  'Połączenie z CH9329 zostało przerwane': ['Connection to CH9329 was interrupted', 'Verbindung zu CH9329 wurde unterbrochen', 'Spojení s CH9329 bylo přerušeno'],
  'Sterowanie wyłączone.': ['Control disabled.', 'Steuerung deaktiviert.', 'Ovládání vypnuto.'],
  'Łączenie z klawiaturą…': ['Connecting to keyboard…', 'Verbindung zur Tastatur…', 'Připojování klávesnice…'],
  'Nie udało się przechwycić myszy.': ['Could not capture the mouse.', 'Maus konnte nicht erfasst werden.', 'Myš nelze zachytit.'],
  'Mysz zwolniona. Włącz sterowanie ponownie, aby wrócić.': ['Mouse released. Enable control again to resume.', 'Maus freigegeben. Aktiviere die Steuerung erneut.', 'Myš uvolněna. Pro pokračování znovu zapněte ovládání.'],
  'Mysz przechwycona. Ctrl+Alt zwalnia mysz i klawiaturę.': ['Mouse captured. Ctrl+Alt releases mouse and keyboard.', 'Maus erfasst. Strg+Alt gibt Maus und Tastatur frei.', 'Myš zachycena. Ctrl+Alt uvolní myš a klávesnici.'],
  'Sterowanie wyłączone po przerwaniu wskaźnika.': ['Control disabled after pointer cancellation.', 'Steuerung nach Zeigerabbruch deaktiviert.', 'Ovládání vypnuto po přerušení ukazatele.'],
  'Mysz i klawiatura zwolnione skrótem Ctrl+Alt.': ['Mouse and keyboard released with Ctrl+Alt.', 'Maus und Tastatur mit Strg+Alt freigegeben.', 'Myš a klávesnice uvolněny pomocí Ctrl+Alt.'],
  'Sterowanie wyłączone po utracie aktywnego okna.': ['Control disabled after window lost focus.', 'Steuerung nach Fokusverlust deaktiviert.', 'Ovládání vypnuto po ztrátě zaměření okna.'],
  'Sterowanie wyłączone po zmianie karty.': ['Control disabled after tab switch.', 'Steuerung nach Tabwechsel deaktiviert.', 'Ovládání vypnuto po změně karty.'],
  'Nieprawidłowy nagłówek MP4.': ['Invalid MP4 header.', 'Ungültiger MP4-Header.', 'Neplatná hlavička MP4.'],
  'Brak konfiguracji kodeka w MP4.': ['MP4 codec configuration is missing.', 'MP4-Codec-Konfiguration fehlt.', 'Chybí konfigurace kodeku MP4.'],
  'Obraz zatrzymany. Wybierz urządzenie ponownie.': ['Video stopped. Select the device again.', 'Bild angehalten. Wähle das Gerät erneut.', 'Obraz zastaven. Znovu vyberte zařízení.'],
  'Obraz zatrzymany. Sterowanie wyłączone.': ['Video stopped. Control disabled.', 'Bild angehalten. Steuerung deaktiviert.', 'Obraz zastaven. Ovládání vypnuto.'],
  'Błąd odtwarzania obrazu H.264.': ['H.264 playback error.', 'H.264-Wiedergabefehler.', 'Chyba přehrávání H.264.'],
  'Błąd dekodowania obrazu.': ['Video decoding error.', 'Fehler beim Dekodieren des Bildes.', 'Chyba dekódování obrazu.'],
  'Podgląd niedostępny. Sterowanie wyłączone.': ['Preview unavailable. Control disabled.', 'Vorschau nicht verfügbar. Steuerung deaktiviert.', 'Náhled není dostupný. Ovládání vypnuto.'],
  'Przeglądarka nie obsługuje strumieni MP4.': ['Browser does not support MP4 streaming.', 'Browser unterstützt kein MP4-Streaming.', 'Prohlížeč nepodporuje streamování MP4.'],
  'Podgląd H.264 jest niedostępny.': ['H.264 preview unavailable.', 'H.264-Vorschau nicht verfügbar.', 'Náhled H.264 není dostupný.'],
  'Strumień obrazu został przerwany.': ['Video stream interrupted.', 'Videostream unterbrochen.', 'Stream obrazu byl přerušen.'],
  'Zbyt duży nagłówek MP4.': ['MP4 header is too large.', 'MP4-Header ist zu groß.', 'Hlavička MP4 je příliš velká.'],
  'Nie można uruchomić podglądu.': ['Could not start preview.', 'Vorschau konnte nicht gestartet werden.', 'Náhled nelze spustit.'],
  'Oryginalny obraz jest niedostępny.': ['Original capture is unavailable.', 'Originalbild nicht verfügbar.', 'Původní obraz není dostupný.'],
  'Nieprawidłowy nagłówek obrazu.': ['Invalid image header.', 'Ungültiger Bild-Header.', 'Neplatná hlavička obrazu.'],
  'Nieprawidłowy rozmiar obrazu.': ['Invalid image size.', 'Ungültige Bildgröße.', 'Neplatná velikost obrazu.'],
  'Nieprawidłowa klatka obrazu.': ['Invalid video frame.', 'Ungültiges Videobild.', 'Neplatný snímek obrazu.'],
  'Nieprawidłowe ustawienia obrazu.': ['Invalid video settings.', 'Ungültige Bildeinstellungen.', 'Neplatné nastavení obrazu.'],
  'Sterowanie wyłączone podczas zmiany obrazu.': ['Control disabled while changing video.', 'Steuerung beim Bildwechsel deaktiviert.', 'Ovládání vypnuto při změně obrazu.'],
  'Łączenie obrazu...': ['Connecting video...', 'Bild wird verbunden...', 'Připojování obrazu...'],
  'Nie wykryto urządzeń.': ['No devices detected.', 'Keine Geräte gefunden.', 'Nebyla nalezena žádná zařízení.'],
  'Urządzenie zostało odłączone.': ['Device disconnected.', 'Gerät getrennt.', 'Zařízení bylo odpojeno.'],
  'Nie udało się pobrać listy urządzeń.': ['Could not load the device list.', 'Geräteliste konnte nicht geladen werden.', 'Nelze načíst seznam zařízení.'],
  'Podgląd · ': ['Preview · ', 'Vorschau · ', 'Náhled · '],
  'Klawiatura → ': ['Keyboard → ', 'Tastatur → ', 'Klávesnice → '],
  'Klawiatura steruje ': ['Keyboard controls ', 'Tastatur steuert ', 'Klávesnice ovládá '],
  '. Kliknij „Wyłącz sterowanie”, aby wrócić do pisania na tym komputerze.': ['. Select “Disable control” to type locally.', '. Wähle „Steuerung deaktivieren“ für lokale Eingaben.', '. Pro místní psaní zvolte „Vypnout ovládání“.'],
  'Przeglądarka nie obsługuje wybranego kodeka: ': ['Browser does not support the selected codec: ', 'Browser unterstützt den ausgewählten Codec nicht: ', 'Prohlížeč nepodporuje vybraný kodek: '],
  'Bufor: ': ['Buffer: ', 'Puffer: ', 'Vyrovnávací paměť: '],
};

function translateText(value, language) {
  if (language === 'pl') return value;
  const index = {en: 0, de: 1, cs: 2}[language];
  if (index === undefined) return value;
  if (Object.prototype.hasOwnProperty.call(translations, value)) return translations[value][index];
  let translated = value;
  for (const key of Object.keys(translations).filter(k => k.startsWith(' ') || k.endsWith(' '))) {
    translated = translated.split(key).join(translations[key][index]);
  }
  return translated;
}

function initializeLanguage() {
  const selector = document.querySelector('#language');
  if (!selector || !document.createTreeWalker || typeof MutationObserver === 'undefined') return;
  const stored = document.cookie.split(';').map(x => x.trim()).find(x => x.startsWith('davekvm_language='));
  const storedLanguage = stored ? stored.slice('davekvm_language='.length) : 'pl';
  let language = ['pl', 'en', 'de', 'cs'].includes(storedLanguage) ? storedLanguage : 'pl';
  const originals = new WeakMap();
  const originalAttributes = new WeakMap();
  const attributes = ['title', 'aria-label', 'alt'];
  function visit(root) {
    if (!root) return;
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT | NodeFilter.SHOW_ELEMENT);
    function update(node) {
      if (node.nodeType === Node.TEXT_NODE && !['SCRIPT', 'STYLE'].includes(node.parentElement?.tagName)) {
        const previous = originals.get(node);
        const original = previous && node.data === previous.rendered ? previous.original : node.data;
        const leading = original.match(/^\s*/)[0], trailing = original.match(/\s*$/)[0];
        const core = original.trim();
        const result = core ? leading + translateText(core, language) + trailing : original;
        originals.set(node, {original, rendered: result});
        if (node.data !== result) node.data = result;
      } else if (node.nodeType === Node.ELEMENT_NODE) {
        let saved = originalAttributes.get(node);
        if (!saved) {
          saved = {};
          originalAttributes.set(node, saved);
        }
        for (const name of attributes) {
          if (!node.hasAttribute(name)) continue;
          if (!(name in saved)) saved[name] = node.getAttribute(name);
          const result = translateText(saved[name], language);
          if (node.getAttribute(name) !== result) node.setAttribute(name, result);
        }
      }
    }
    update(root);
    while (walker.nextNode()) update(walker.currentNode);
  }
  selector.value = language;
  document.documentElement.lang = language;
  visit(document.body);
  const observer = new MutationObserver(records => {
    for (const record of records) {
      if (record.type === 'characterData') visit(record.target);
      else for (const node of record.addedNodes) visit(node);
    }
  });
  observer.observe(document.body, {subtree: true, childList: true, characterData: true});
  selector.addEventListener('change', () => {
    language = ['pl', 'en', 'de', 'cs'].includes(selector.value) ? selector.value : 'pl';
    document.documentElement.lang = language;
    document.cookie = 'davekvm_language=' + language + '; Max-Age=31536000; Path=/grabber/; SameSite=Lax';
    visit(document.body);
  });
}
document.addEventListener('DOMContentLoaded', initializeLanguage);
