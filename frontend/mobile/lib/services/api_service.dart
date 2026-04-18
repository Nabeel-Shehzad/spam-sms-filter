import 'dart:convert';
import 'dart:async';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

class ApiService {
  // iOS simulator  → localhost
  // Android emulator → 10.0.2.2
  // Real device     → your Mac's LAN IP e.g. 192.168.1.x
  static const String baseUrl = 'http://localhost:8000';

  static const _timeout = Duration(seconds: 10);

  static Future<String?> _getToken() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString('access_token');
  }

  static Future<Map<String, String>> _authHeaders() async {
    final token = await _getToken();
    return {
      'Content-Type': 'application/json',
      if (token != null) 'Authorization': 'Bearer $token',
    };
  }

  // ---------------------------------------------------------------------------
  // Auth
  // ---------------------------------------------------------------------------

  static Future<Map<String, dynamic>> register(String email, String password) async {
    try {
      final res = await http
          .post(
            Uri.parse('$baseUrl/api/v1/auth/register'),
            headers: {'Content-Type': 'application/json'},
            body: jsonEncode({'email': email, 'password': password}),
          )
          .timeout(_timeout);
      final data = jsonDecode(res.body);
      if (res.statusCode == 201) {
        final prefs = await SharedPreferences.getInstance();
        await prefs.setString('access_token', data['access_token']);
        await prefs.setString('refresh_token', data['refresh_token']);
        await prefs.setString('user_email', email);
      }
      return {'status': res.statusCode, ...data};
    } on TimeoutException {
      return {'status': 0, 'detail': 'Server timed out. Is it running on port 8000?'};
    } catch (e) {
      return {'status': 0, 'detail': 'Cannot reach server. Is it running?\n$e'};
    }
  }

  static Future<Map<String, dynamic>> login(String email, String password) async {
    try {
      final res = await http
          .post(
            Uri.parse('$baseUrl/api/v1/auth/login'),
            headers: {'Content-Type': 'application/json'},
            body: jsonEncode({'email': email, 'password': password}),
          )
          .timeout(_timeout);
      final data = jsonDecode(res.body);
      if (res.statusCode == 200) {
        final prefs = await SharedPreferences.getInstance();
        await prefs.setString('access_token', data['access_token']);
        await prefs.setString('refresh_token', data['refresh_token']);
        await prefs.setString('user_email', email);
      }
      return {'status': res.statusCode, ...data};
    } on TimeoutException {
      return {'status': 0, 'detail': 'Server timed out. Is it running on port 8000?'};
    } catch (e) {
      return {'status': 0, 'detail': 'Cannot reach server. Is it running?\n$e'};
    }
  }

  static Future<void> logout() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove('access_token');
    await prefs.remove('refresh_token');
    await prefs.remove('user_email');
  }

  static Future<bool> isLoggedIn() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.containsKey('access_token');
  }

  static Future<String?> getUserEmail() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString('user_email');
  }

  // ---------------------------------------------------------------------------
  // Classify
  // ---------------------------------------------------------------------------

  static Future<Map<String, dynamic>> classify(String text) async {
    try {
      final headers = await _authHeaders();
      final res = await http
          .post(
            Uri.parse('$baseUrl/api/v1/classify'),
            headers: headers,
            body: jsonEncode({'text': text}),
          )
          .timeout(_timeout);
      return {'status': res.statusCode, ...jsonDecode(res.body)};
    } on TimeoutException {
      return {'status': 0, 'detail': 'Request timed out'};
    } catch (e) {
      return {'status': 0, 'detail': 'Network error: $e'};
    }
  }

  // ---------------------------------------------------------------------------
  // Stats
  // ---------------------------------------------------------------------------

  static Future<Map<String, dynamic>> getStats() async {
    try {
      final headers = await _authHeaders();
      final res = await http
          .get(Uri.parse('$baseUrl/api/v1/stats'), headers: headers)
          .timeout(_timeout);
      return {'status': res.statusCode, ...jsonDecode(res.body)};
    } on TimeoutException {
      return {'status': 0, 'detail': 'Request timed out'};
    } catch (e) {
      return {'status': 0, 'detail': 'Network error: $e'};
    }
  }

  static Future<List<dynamic>> getHistory({int limit = 50}) async {
    try {
      final headers = await _authHeaders();
      final res = await http
          .get(
            Uri.parse('$baseUrl/api/v1/stats/history?limit=$limit'),
            headers: headers,
          )
          .timeout(_timeout);
      if (res.statusCode == 200) return jsonDecode(res.body) as List;
      return [];
    } catch (_) {
      return [];
    }
  }

  // ---------------------------------------------------------------------------
  // Feedback
  // ---------------------------------------------------------------------------

  static Future<Map<String, dynamic>> submitFeedback(int logId, String correctLabel) async {
    try {
      final headers = await _authHeaders();
      final res = await http
          .post(
            Uri.parse('$baseUrl/api/v1/feedback'),
            headers: headers,
            body: jsonEncode({'log_id': logId, 'correct_label': correctLabel}),
          )
          .timeout(_timeout);
      return {'status': res.statusCode, ...jsonDecode(res.body)};
    } on TimeoutException {
      return {'status': 0, 'detail': 'Request timed out'};
    } catch (e) {
      return {'status': 0, 'detail': 'Network error: $e'};
    }
  }
}
