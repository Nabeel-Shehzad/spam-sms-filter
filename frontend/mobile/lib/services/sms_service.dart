import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:telephony/telephony.dart';
import 'api_service.dart';

// ─────────────────────────────────────────────────────────────────────────────
// Background handler — must be a top-level function
// ─────────────────────────────────────────────────────────────────────────────
@pragma('vm:entry-point')
void backgroundSmsHandler(SmsMessage message) async {
  final text = message.body ?? '';
  if (text.isEmpty) return;
  try {
    final result = await ApiService.classify(text);
    final label = result['label'] ?? 'ham';
    final confidence = ((result['confidence'] ?? 0.0) * 100).toInt();
    final sender = message.address ?? 'Unknown';
    if (label == 'spam') {
      await SmsService._showSpamNotification(sender, text, confidence);
    }
  } catch (_) {}
}

// ─────────────────────────────────────────────────────────────────────────────
// SmsService
// ─────────────────────────────────────────────────────────────────────────────
class SmsService {
  static final Telephony _telephony = Telephony.instance;
  static final FlutterLocalNotificationsPlugin _notifs =
      FlutterLocalNotificationsPlugin();
  static bool _initialised = false;

  // ── Init ───────────────────────────────────────────────────────────────────

  static Future<void> init() async {
    if (_initialised) return;
    _initialised = true;

    const android = AndroidInitializationSettings('@mipmap/ic_launcher');
    await _notifs.initialize(
      settings: const InitializationSettings(android: android),
    );

    const channel = AndroidNotificationChannel(
      'spam_alerts',
      'Spam Alerts',
      description: 'Notifies when a spam SMS is detected',
      importance: Importance.high,
    );
    await _notifs
        .resolvePlatformSpecificImplementation<
            AndroidFlutterLocalNotificationsPlugin>()
        ?.createNotificationChannel(channel);
  }

  // ── Permissions ────────────────────────────────────────────────────────────

  static Future<bool> requestPermissions() async {
    return await _telephony.requestSmsPermissions ?? false;
  }

  // ── Inbox scan ─────────────────────────────────────────────────────────────

  static Future<List<Map<String, dynamic>>> classifyInbox({
    void Function(int done, int total)? onProgress,
  }) async {
    final msgs = await _telephony.getInboxSms(
      columns: [SmsColumn.ADDRESS, SmsColumn.BODY, SmsColumn.DATE],
      sortOrder: [OrderBy(SmsColumn.DATE, sort: Sort.DESC)],
    );
    final results = <Map<String, dynamic>>[];

    for (int i = 0; i < msgs.length; i++) {
      final msg = msgs[i];
      final body = msg.body ?? '';
      if (body.isEmpty) continue;
      try {
        final res = await ApiService.classify(body);
        results.add({
          'address': msg.address ?? 'Unknown',
          'body': body,
          'date': msg.date,
          'label': res['label'] ?? 'ham',
          'confidence': (res['confidence'] ?? 0.0) as double,
          'model_used': res['model_used'] ?? '',
          'log_id': res['log_id'],
        });
      } catch (_) {
        results.add({
          'address': msg.address ?? 'Unknown',
          'body': body,
          'date': msg.date,
          'label': 'ham',
          'confidence': 0.0,
          'model_used': '',
          'log_id': null,
        });
      }
      onProgress?.call(i + 1, msgs.length);
    }
    return results;
  }

  // ── Real-time listener ─────────────────────────────────────────────────────

  static void startListening({
    required void Function(SmsMessage msg, String label, double confidence)
        onMessage,
  }) {
    _telephony.listenIncomingSms(
      onNewMessage: (SmsMessage message) async {
        final text = message.body ?? '';
        if (text.isEmpty) return;
        try {
          final res = await ApiService.classify(text);
          final label = res['label'] ?? 'ham';
          final confidence = (res['confidence'] ?? 0.0) as double;
          onMessage(message, label, confidence);
          if (label == 'spam') {
            await _showSpamNotification(
              message.address ?? 'Unknown',
              text,
              (confidence * 100).toInt(),
            );
          }
        } catch (_) {}
      },
      onBackgroundMessage: backgroundSmsHandler,
      listenInBackground: true,
    );
  }

  // ── Notifications ──────────────────────────────────────────────────────────

  static Future<void> _showSpamNotification(
      String sender, String body, int pct) async {
    await _notifs.show(
      id: DateTime.now().millisecondsSinceEpoch ~/ 1000,
      title: '⚠️ Spam detected from $sender',
      body:
          '$pct% confidence — "${body.length > 60 ? body.substring(0, 60) : body}..."',
      notificationDetails: const NotificationDetails(
        android: AndroidNotificationDetails(
          'spam_alerts',
          'Spam Alerts',
          channelDescription: 'Notifies when a spam SMS is detected',
          importance: Importance.high,
          priority: Priority.high,
          icon: '@mipmap/ic_launcher',
        ),
      ),
    );
  }
}
