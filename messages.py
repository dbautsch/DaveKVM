#!/usr/bin/env python3
# Copyright (c) 2026 Dawid Bautsch
# SPDX-License-Identifier: MIT
"""Stable user-facing error codes and translations for the server and CLI."""

import os


# Each entry contains English, Polish, German and Czech, in that order.
MESSAGES = {
    'NO_KEYBOARD_MAPPING': ('No keyboard is assigned to this device', 'Do tego grabbera nie przypisano klawiatury', 'Diesem Gerät ist keine Tastatur zugeordnet', 'K tomuto zařízení není přiřazena klávesnice'),
    'KEYBOARD_BUSY': ('Keyboard is in use by another user', 'Klawiatura jest zajęta przez innego użytkownika', 'Tastatur wird von einem anderen Benutzer verwendet', 'Klávesnici používá jiný uživatel'),
    'KEYBOARD_CONNECT_FAILED': ('Could not connect to CH9329', 'Nie można połączyć się z CH9329', 'Verbindung zu CH9329 fehlgeschlagen', 'Nelze se připojit k CH9329'),
    'CONTROL_EXPIRED_OR_BUSY': ('Control has expired or is busy', 'Sterowanie wygasło lub jest zajęte', 'Steuerung ist abgelaufen oder belegt', 'Ovládání vypršelo nebo je obsazené'),
    'CONTROL_EXPIRED': ('Control has expired', 'Sterowanie wygasło', 'Steuerung ist abgelaufen', 'Ovládání vypršelo'),
    'KEYBOARD_DISCONNECTED': ('Connection to CH9329 was interrupted', 'Połączenie z CH9329 zostało przerwane', 'Verbindung zu CH9329 wurde unterbrochen', 'Spojení s CH9329 bylo přerušeno'),
    'BRIDGE_TIMEOUT': ('No response from the SSH bridge', 'Brak odpowiedzi z mostu SSH', 'Keine Antwort von der SSH-Brücke', 'Most SSH neodpovídá'),
    'BRIDGE_INVALID_RESPONSE': ('Invalid response from the SSH bridge', 'Błędna odpowiedź z mostu SSH', 'Ungültige Antwort der SSH-Brücke', 'Neplatná odpověď mostu SSH'),
    'REMOTE_KEYBOARD_ERROR': ('Remote keyboard error', 'Błąd klawiatury zdalnej', 'Fehler der entfernten Tastatur', 'Chyba vzdálené klávesnice'),
    'UNSUPPORTED_COMMAND': ('Unsupported command', 'Nieobsługiwana komenda', 'Nicht unterstützter Befehl', 'Nepodporovaný příkaz'),
    'CH9329_INVALID_ACK': ('Invalid acknowledgement from CH9329', 'Brak poprawnego potwierdzenia z CH9329', 'Ungültige Bestätigung von CH9329', 'Neplatné potvrzení od CH9329'),
    'CH340_NOT_FOUND': ('CH340 adapter not found', 'Nie znaleziono adaptera CH340G', 'CH340-Adapter nicht gefunden', 'Adaptér CH340 nebyl nalezen'),
    'INVALID_REQUEST': ('Invalid request', 'Nieprawidłowe żądanie', 'Ungültige Anfrage', 'Neplatný požadavek'),
    'HTTP_ERROR': ('HTTP request failed', 'Błąd żądania HTTP', 'HTTP-Anfrage fehlgeschlagen', 'Požadavek HTTP selhal'),
    'PANEL_CONNECT_FAILED': ('Could not connect to the DaveKVM panel', 'Nie można połączyć się z panelem DaveKVM', 'Verbindung zum DaveKVM-Panel fehlgeschlagen', 'Nelze se připojit k panelu DaveKVM'),
    'UNKNOWN_MODIFIERS': ('Unknown modifiers', 'Nieznane modyfikatory', 'Unbekannte Modifikatortasten', 'Neznámé modifikační klávesy'),
    'INVALID_KEYS': ('Unknown keys or more than six keys', 'Nieznane klawisze lub więcej niż 6 klawiszy', 'Unbekannte Tasten oder mehr als sechs Tasten', 'Neznámé klávesy nebo více než šest kláves'),
    'DUPLICATE_KEY': ('Duplicate key', 'Powtórzony klawisz', 'Doppelte Taste', 'Duplicitní klávesa'),
    'UNSUPPORTED_TEXT': ('Text supports US-layout ASCII only', 'Tekst obsługuje tylko ASCII w układzie US', 'Text unterstützt nur ASCII mit US-Tastaturlayout', 'Text podporuje pouze ASCII s rozložením US'),
    'EXPECTED_OBJECT': ('Expected a JSON object', 'Oczekiwano obiektu JSON', 'JSON-Objekt erwartet', 'Očekáván objekt JSON'),
    'INVALID_TEXT': ('Text must contain at most 1000 characters', 'Tekst musi mieć najwyżej 1000 znaków', 'Text darf höchstens 1000 Zeichen enthalten', 'Text smí obsahovat nejvýše 1000 znaků'),
    'INVALID_MOUSE': ('Invalid mouse coordinates or buttons', 'Nieprawidłowe współrzędne lub przyciski myszy', 'Ungültige Mauskoordinaten oder Maustasten', 'Neplatné souřadnice nebo tlačítka myši'),
    'UNKNOWN_ACTION': ('Unknown action', 'Nieznana akcja', 'Unbekannte Aktion', 'Neznámá akce'),
    'COMMAND_TOO_LONG': ('Command is too long', 'Polecenie jest zbyt długie', 'Befehl ist zu lang', 'Příkaz je příliš dlouhý'),
    'CLI_USAGE_CONTROL': ('Usage: davekvm-control [--device DEVICE] [--help]', 'Użycie: davekvm-control [--device URZĄDZENIE] [--help]', 'Aufruf: davekvm-control [--device GERÄT] [--help]', 'Použití: davekvm-control [--device ZAŘÍZENÍ] [--help]'),
    'CLI_USAGE_GRABBER': ('Usage: davekvm-grabber list | snapshot DEVICE | stream DEVICE', 'Użycie: davekvm-grabber list | snapshot URZĄDZENIE | stream URZĄDZENIE', 'Aufruf: davekvm-grabber list | snapshot GERÄT | stream GERÄT', 'Použití: davekvm-grabber list | snapshot ZAŘÍZENÍ | stream ZAŘÍZENÍ'),
    'CAPTURE_FAILED': ('Could not capture the image', 'Nie udało się pobrać obrazu', 'Bild konnte nicht aufgenommen werden', 'Obraz se nepodařilo získat'),
    'PASSWORD_FILE_ERROR': ('Could not read the password file', 'Nie można odczytać pliku hasła', 'Passwortdatei konnte nicht gelesen werden', 'Soubor s heslem nelze přečíst'),
    'UNEXPECTED_ERROR': ('Unexpected error', 'Nieoczekiwany błąd', 'Unerwarteter Fehler', 'Neočekávaná chyba'),
    'INVALID_CAPTURE_DIMENSIONS': ('Invalid capture dimensions', 'Nieprawidłowa rozdzielczość przechwytywania', 'Ungültige Aufnahmeauflösung', 'Neplatné rozlišení snímání'),
    'INVALID_CAPTURE_RATE': ('Capture rates must be between 1 and 120 fps', 'Liczba klatek musi wynosić od 1 do 120 fps', 'Bildrate muss zwischen 1 und 120 fps liegen', 'Snímková frekvence musí být mezi 1 a 120 fps'),
    'INVALID_PORT': ('Port must be between 1 and 65535', 'Port musi być liczbą od 1 do 65535', 'Port muss zwischen 1 und 65535 liegen', 'Port musí být mezi 1 a 65535'),
    'INVALID_SSH_ALIAS': ('Invalid SSH host alias', 'Nieprawidłowy alias SSH', 'Ungültiger SSH-Hostalias', 'Neplatný alias SSH'),
    'INVALID_SERIAL_MAP': ('Serial mapping must be a JSON object', 'Mapa portów szeregowych musi być obiektem JSON', 'Serielle Zuordnung muss ein JSON-Objekt sein', 'Mapování sériových portů musí být objektem JSON'),
    'INVALID_DEVICE_MAPPING': ('Invalid capture device mapping', 'Nieprawidłowe przypisanie grabbera', 'Ungültige Aufnahmegerätezuordnung', 'Neplatné mapování snímacího zařízení'),
    'INVALID_KEYBOARD_TARGET': ('Invalid keyboard target', 'Nieprawidłowy cel klawiatury', 'Ungültiges Tastaturziel', 'Neplatný cíl klávesnice'),
    'REMOTE_MAPPING_INVALID': ('Remote keyboard requires an SSH alias and video ID', 'Zdalna klawiatura wymaga aliasu SSH i identyfikatora obrazu', 'Entfernte Tastatur benötigt SSH-Alias und Video-ID', 'Vzdálená klávesnice vyžaduje alias SSH a ID obrazu'),
    'SERIAL_PATH_INVALID': ('Keyboard must use a stable serial path', 'Klawiatura wymaga stałej ścieżki portu szeregowego', 'Tastatur benötigt einen stabilen seriellen Pfad', 'Klávesnice vyžaduje stabilní cestu sériového portu'),
    'INVALID_ORIGIN': ('Origin must be an HTTP(S) origin without path or credentials', 'Origin musi być adresem HTTP(S) bez ścieżki i danych logowania', 'Origin muss HTTP(S) ohne Pfad oder Zugangsdaten sein', 'Origin musí být adresa HTTP(S) bez cesty a přihlašovacích údajů'),
    'INVALID_CREDENTIALS_CONFIG': ('Set a username and a password of at least 16 characters', 'Ustaw nazwę użytkownika i hasło o długości co najmniej 16 znaków', 'Benutzernamen und Passwort mit mindestens 16 Zeichen festlegen', 'Nastavte uživatelské jméno a heslo dlouhé alespoň 16 znaků'),
    'INSECURE_BIND': ('Non-loopback HTTP requires explicit opt-in; prefer a TLS proxy', 'HTTP poza loopback wymaga jawnej zgody; użyj proxy TLS', 'HTTP außerhalb von Loopback erfordert eine Freigabe; TLS-Proxy bevorzugen', 'HTTP mimo loopback vyžaduje výslovný souhlas; použijte TLS proxy'),
    'INVALID_ENCODER_SETTINGS': ('Invalid encoder settings', 'Nieprawidłowe ustawienia kodera', 'Ungültige Encoder-Einstellungen', 'Neplatné nastavení kodéru'),
    'INVALID_ENCODER': ('Invalid encoder', 'Nieprawidłowy koder', 'Ungültiger Encoder', 'Neplatný kodér'),
    'INVALID_PRESET': ('Invalid preset', 'Nieprawidłowy preset', 'Ungültiges Preset', 'Neplatná předvolba'),
    'INVALID_CRF': ('CRF must be between 1 and 30', 'CRF musi być liczbą od 1 do 30', 'CRF muss zwischen 1 und 30 liegen', 'CRF musí být mezi 1 a 30'),
    'INVALID_BITRATE': ('Bitrate must be between 1000 and 30000 kb/s', 'Bitrate musi wynosić od 1000 do 30000 kb/s', 'Bitrate muss zwischen 1000 und 30000 kb/s liegen', 'Datový tok musí být mezi 1000 a 30000 kb/s'),
    'INVALID_QSV_PRESET': ('Invalid Quick Sync preset', 'Nieprawidłowy preset Quick Sync', 'Ungültiges Quick-Sync-Preset', 'Neplatná předvolba Quick Sync'),
    'INVALID_QSV_PROFILE': ('Invalid Quick Sync profile', 'Nieprawidłowy profil Quick Sync', 'Ungültiges Quick-Sync-Profil', 'Neplatný profil Quick Sync'),
    'INVALID_QSV_MODE': ('Invalid Quick Sync mode', 'Nieprawidłowy tryb Quick Sync', 'Ungültiger Quick-Sync-Modus', 'Neplatný režim Quick Sync'),
    'INVALID_QSV_QUALITY': ('Quick Sync quality must be between 1 and 51', 'Jakość Quick Sync musi wynosić od 1 do 51', 'Quick-Sync-Qualität muss zwischen 1 und 51 liegen', 'Kvalita Quick Sync musí být mezi 1 a 51'),
    'INVALID_KEYFRAME_INTERVAL': ('Keyframe interval must be between 15 and 300', 'Odstęp klatek kluczowych musi wynosić od 15 do 300', 'Keyframe-Abstand muss zwischen 15 und 300 liegen', 'Interval klíčových snímků musí být mezi 15 a 300'),
    'INVALID_VBR_BITRATE': ('VBR requires a bitrate below 30 Mb/s', 'VBR wymaga bitrate poniżej 30 Mb/s', 'VBR benötigt eine Bitrate unter 30 Mb/s', 'VBR vyžaduje datový tok nižší než 30 Mb/s'),
    'INVALID_HEVC_PROFILE': ('H.265 Quick Sync requires the main profile', 'H.265 Quick Sync obsługuje profil main', 'H.265 Quick Sync benötigt das Main-Profil', 'H.265 Quick Sync vyžaduje profil main'),
    'BRIDGE_SERIAL_REQUIRED': ('Configure the bridge serial path', 'Skonfiguruj ścieżkę portu szeregowego mostu', 'Seriellen Pfad der Brücke konfigurieren', 'Nastavte cestu sériového portu mostu'),
    'INVALID_REPORT': ('Invalid HID report', 'Nieprawidłowy raport HID', 'Ungültiger HID-Bericht', 'Neplatná zpráva HID'),
    'REPORT_TOO_LONG': ('HID report is too long', 'Raport HID jest zbyt długi', 'HID-Bericht ist zu lang', 'Zpráva HID je příliš dlouhá'),
    'INVALID_MULTIPART_BOUNDARY': ('Invalid multipart boundary', 'Nieprawidłowa granica strumienia multipart', 'Ungültige Multipart-Grenze', 'Neplatná hranice multipart streamu'),
    'INVALID_MULTIPART_HEADERS': ('Invalid multipart headers', 'Nieprawidłowe nagłówki strumienia multipart', 'Ungültige Multipart-Header', 'Neplatné hlavičky multipart streamu'),
    'INVALID_FRAME_LENGTH': ('Invalid frame length', 'Nieprawidłowa długość klatki', 'Ungültige Bildlänge', 'Neplatná délka snímku'),
    'INCOMPLETE_FRAME': ('Incomplete frame', 'Niepełna klatka obrazu', 'Unvollständiges Bild', 'Neúplný snímek'),
    'INVALID_FRAME_TERMINATOR': ('Invalid frame terminator', 'Nieprawidłowy koniec klatki', 'Ungültiges Bildende', 'Neplatné zakončení snímku'),
    'NO_VALID_FRAME': ('No valid JPEG frame', 'Brak poprawnej klatki JPEG', 'Kein gültiges JPEG-Bild', 'Žádný platný snímek JPEG'),
    'FRAME_TIMEOUT': ('Could not obtain a frame in time', 'Nie udało się pobrać klatki na czas', 'Bild konnte nicht rechtzeitig abgerufen werden', 'Snímek se nepodařilo získat včas'),
    'CAPTURE_STOPPED': ('Capture stopped', 'Przechwytywanie zostało zatrzymane', 'Aufnahme wurde beendet', 'Snímání bylo zastaveno'),
    'STREAM_UNAVAILABLE': ('Stream is unavailable', 'Strumień jest niedostępny', 'Stream ist nicht verfügbar', 'Stream není dostupný'),
    'ENCODER_TIMEOUT': ('H.264 encoder startup timed out', 'Przekroczono czas uruchamiania kodera H.264', 'Zeitüberschreitung beim Start des H.264-Encoders', 'Vypršel čas spuštění kodéru H.264'),
    'ENCODER_START_FAILED': ('Could not start the H.264 encoder', 'Nie udało się uruchomić kodera H.264', 'H.264-Encoder konnte nicht gestartet werden', 'Kodér H.264 se nepodařilo spustit'),
    'FORBIDDEN': ('Access denied', 'Dostęp zabroniony', 'Zugriff verweigert', 'Přístup odepřen'),
    'NOT_FOUND': ('Resource not found', 'Nie znaleziono zasobu', 'Ressource nicht gefunden', 'Zdroj nebyl nalezen'),
    'ENCODER_BUSY': ('Video encoder is busy', 'Koder obrazu jest zajęty', 'Video-Encoder ist belegt', 'Videokodér je obsazený'),
    'ENCODER_UNAVAILABLE': ('Video encoder is unavailable', 'Koder obrazu jest niedostępny', 'Video-Encoder ist nicht verfügbar', 'Videokodér není dostupný'),
    'CAPTURE_UNAVAILABLE': ('Capture device is unavailable', 'Urządzenie przechwytujące jest niedostępne', 'Aufnahmegerät ist nicht verfügbar', 'Snímací zařízení není dostupné'),
    'HEVC_REQUIRES_WEB_VIDEO': ('HEVC requires the web-video endpoint', 'HEVC wymaga punktu web-video', 'HEVC benötigt den web-video-Endpunkt', 'HEVC vyžaduje koncový bod web-video'),
    'INVALID_TRANSLATION_MARKERS': ('Invalid translation markers', 'Nieprawidłowe znaczniki tłumaczenia', 'Ungültige Übersetzungsmarkierungen', 'Neplatné značky překladu'),
    'EXPECTED_HEADER': ('Expected exactly one HTML header', 'Oczekiwano dokładnie jednego nagłówka HTML', 'Genau ein HTML-Header erwartet', 'Očekávána právě jedna hlavička HTML'),
    'EXPECTED_SCRIPT': ('Expected exactly one inline panel script', 'Oczekiwano dokładnie jednego skryptu panelu', 'Genau ein eingebettetes Panel-Skript erwartet', 'Očekáván právě jeden vložený skript panelu'),
    'EMBED_USAGE': ('Usage: embed_i18n.py PANEL.html', 'Użycie: embed_i18n.py PANEL.html', 'Aufruf: embed_i18n.py PANEL.html', 'Použití: embed_i18n.py PANEL.html'),
    'UNKNOWN_DEMO': ('Unknown demo', 'Nieznany przykład', 'Unbekanntes Beispiel', 'Neznámá ukázka'),
    'INVALID_PANEL_STRUCTURE': ('Unexpected panel structure', 'Nieoczekiwana struktura panelu', 'Unerwartete Panelstruktur', 'Neočekávaná struktura panelu'),
    'DEMO_USAGE': ('Usage: make_demo.py EXISTING_OUTPUT_DIRECTORY', 'Użycie: make_demo.py ISTNIEJĄCY_KATALOG', 'Aufruf: make_demo.py VORHANDENES_VERZEICHNIS', 'Použití: make_demo.py EXISTUJÍCÍ_ADRESÁŘ'),
    'OUTPUT_DIRECTORY_REQUIRED': ('Output directory must already exist', 'Katalog wyjściowy musi istnieć', 'Ausgabeverzeichnis muss bereits existieren', 'Výstupní adresář již musí existovat'),
}


def normalize_language(value):
    """Return a supported language; unknown or malformed locales use English."""
    language = str(value or '').split('.', 1)[0].split('@', 1)[0].replace('-', '_').split('_', 1)[0].lower()
    return language if language in ('en', 'pl', 'de', 'cs') else 'en'


def configured_language():
    """CLI preference, then process locale, with a deterministic English fallback."""
    return normalize_language(os.environ.get('DAVEKVM_LANG') or os.environ.get('LC_ALL')
                              or os.environ.get('LC_MESSAGES') or os.environ.get('LANG'))


def message(code, language=None):
    """Translate a stable code without exposing arbitrary exception details."""
    row = MESSAGES.get(code, MESSAGES['UNEXPECTED_ERROR']) if isinstance(code, str) else MESSAGES['UNEXPECTED_ERROR']
    return row[{'en': 0, 'pl': 1, 'de': 2, 'cs': 3}[normalize_language(language or configured_language())]]


class UserError(ValueError):
    """A CLI input or operation failure with a stable machine-readable code."""
    def __init__(self, code):
        self.code = code if isinstance(code, str) and code in MESSAGES else 'UNEXPECTED_ERROR'
        super().__init__(message(self.code))
