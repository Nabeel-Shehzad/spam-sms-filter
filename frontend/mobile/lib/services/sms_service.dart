import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:telephony/telephony.dart';
import 'api_service.dart';

// ─────────────────────────────────────────────────────────────────────────────
// Background handler — called by telephony when a new SMS arrives
// MUST be a top-level function (not inside a class)
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

  /// Call once from main() before runApp
  static Future<void> init() async {
    if (_initialised) return;
    _initialised = true;

    // Notifications setup
    const android = AndroidInitializationSettings('@mipmap/ic_launcher');
    const ios = DarwinInitializationSettings();
    await _notifs.initialize(
      settings: const InitializationSettings(android: android, iOS: ios),
    );

    // Create notification channel for spam alerts
    const channel = AndroidNotificationChannel(
      'spam_alerts',
      'Spam Alerts',
      description: 'Notifies you when a spam SMS is detected',
      importance: Importance.high,
    );
    await _notifs
        .resolvePlatformSpecificImplementation<
            AndroidFlutterLocalNotificationsPlugin>()
        ?.createNotificationChannel(channel);
  }

  /// Request READ_SMS + RECEIVE_SMS permissions
  static Future<bool> requestPermissions() async {
    final granted = await _telephony.requestSmsPermissions ?? false;
    return granted;
  }

  static Future<bool> hasPermissions() async {
    return await _telephony.requestSmsPermissions ?? false;
  }

  // ── Inbox scan ─────────────────────────────────────────────────────────────

  /// Returns all SMS from the inbox (newest first)
  static Future<List<SmsMessage>> getInbox() async {
    try {
      return await _telephony.getInboxSms(
        columns: [
          SmsColumn.ADDRESS,
          SmsColumn.BODY,
          SmsColumn.DATE,
          SmsColumn.READ,
        ],
        sortOrder: [
          OrderBy(SmsColumn.DATE, sort: Sort.DESC),
        ],
      );
    } catch (_) {
      return [];
    }
  }

  /// Classify a batch of inbox messages via the API and return results
  static Future<List<Map<String, dynamic>>> classifyInbox({
    void Function(int done, int total)? onProgress,
  }) async {
    final messages = await getInbox();
    final results = <Map<String, dynamic>>[];

    for (int i = 0; i < messages.length; i++) {
      final msg = messages[i];
      final text = msg.body ?? '';
      if (text.isEmpty) continue;

      try {
        final res = await ApiService.classify(text);
        results.add({
          'address': msg.address ?? 'Unknown',
          'body': text,
          'date': msg.date,
          'label': res['label'] ?? 'ham',
          'confidence': res['confidence'] ?? 0.0,
          'model_used': res['model_used'] ?? '',
          'log_id': res['log_id'],
        });
      } catch (_) {
        results.add({
          'address': msg.address ?? 'Unknown',
          'body': text,
          'date': msg.date,
          'label': 'ham',
          'confidence': 0.0,
          'model_used': '',
          'log_id': null,
        });
      }

      onProgress?.call(i + 1, messages.length);
    }
    return results;
  }

  // ── Real-time listener ─────────────────────────────────────────────────────

  /// Start listening for new incoming SMS
  static void startListening({
    required void Function(SmsMessage msg, String label, double confidence) onMessage,
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
    String sender, String body, int confidencePct) async {
    await _notifs.show(
      id: DateTime.now().millisecondsSinceEpoch ~/ 1000,
      title: '⚠️ Spam detected from $sender',
      body: '$confidencePct% confidence — "${body.length > 60 ? body.substring(0, 60) : body}..."',
      notificationDetails: const NotificationDetails(
        android: AndroidNotificationDetails(
          'spam_alerts',
          'Spam Alerts',
          channelDescription: 'Notifies you when a spam SMS is detected',
          importance: Importance.high,
          priority: Priority.high,
          icon: '@mipmap/ic_launcher',
        ),
      ),
    );
  }
}
