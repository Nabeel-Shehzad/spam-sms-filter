import 'package:flutter/widgets.dart';

/// Returns true if [text] contains Arabic characters (Unicode block U+0600–U+06FF).
bool isArabic(String text) =>
    text.runes.any((r) => r >= 0x0600 && r <= 0x06FF);

/// Returns [TextDirection.rtl] for Arabic text, [TextDirection.ltr] otherwise.
TextDirection directionOf(String text) =>
    isArabic(text) ? TextDirection.rtl : TextDirection.ltr;

/// Returns [TextAlign.right] for Arabic text, [TextAlign.start] otherwise.
TextAlign alignOf(String text) =>
    isArabic(text) ? TextAlign.right : TextAlign.start;

/// Human-readable language label from an ISO code.
String languageLabel(String code) {
  switch (code.toLowerCase()) {
    case 'ar':
      return 'Arabic';
    case 'en':
      return 'English';
    default:
      return code.toUpperCase();
  }
}
