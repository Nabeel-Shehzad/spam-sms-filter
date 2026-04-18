import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

class ApiService {
  static const String baseUrl = 'http://10.0.2.2:8000'; // Android emulator → host
  // static const String baseUrl = 'http://localhost:8000'; // iOS simulator

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
    final res = await http.post(
      Uri.parse('$baseUrl/api/v1/auth/register'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'email': email, 'password': password}),
    );
    final data = jsonDecode(res.body);
    if (res.statusCode == 201) {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString('access_token', data['access_token']);
      await prefs.setString('refresh_token', data['refresh_token']);
      await prefs.setString('user_email', email);
    }
    return {'status': res.statusCode, ...data};
  }

  static Future<Map<String, dynamic>> login(String email, String password) async {
    final res = await http.post(
      Uri.parse('$baseUrl/api/v1/auth/login'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'email': email, 'password': password}),
    );
    final data = jsonDecode(res.body);
    if (res.statusCode == 200) {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString('access_token', data['access_token']);
      await prefs.setString('refresh_token', data['refresh_token']);
      await prefs.setString('user_email', email);
    }
    return {'status': res.statusCode, ...data};
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
    final headers = await _authHeaders();
    final res = await http.post(
      Uri.parse('$baseUrl/api/v1/classify'),
      headers: headers,
      body: jsonEncode({'text': text}),
    );
    return {'status': res.statusCode, ...jsonDecode(res.body)};
  }

  // ---------------------------------------------------------------------------
  // Stats
  // ---------------------------------------------------------------------------

  static Future<Map<String, dynamic>> getStats() async {
    final headers = await _authHeaders();
    final res = await http.get(Uri.parse('$baseUrl/api/v1/stats'), headers: headers);
    return {'status': res.statusCode, ...jsonDecode(res.body)};
  }

  static Future<List<dynamic>> getHistory({int limit = 50}) async {
    final headers = await _authHeaders();
    final res = await http.get(
      Uri.parse('$baseUrl/api/v1/stats/history?limit=$limit'),
      headers: headers,
    );
    if (res.statusCode == 200) return jsonDecode(res.body) as List;
    return [];
  }

  // ---------------------------------------------------------------------------
  // Feedback
  // ---------------------------------------------------------------------------

  static Future<Map<String, dynamic>> submitFeedback(int logId, String correctLabel) async {
    final headers = await _authHeaders();
    final res = await http.post(
      Uri.parse('$baseUrl/api/v1/feedback'),
      headers: headers,
      body: jsonEncode({'log_id': logId, 'correct_label': correctLabel}),
    );
    return {'status': res.statusCode, ...jsonDecode(res.body)};
  }
}
