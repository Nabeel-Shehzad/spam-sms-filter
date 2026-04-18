import 'package:flutter/material.dart';
import '../services/api_service.dart';

class AuthProvider extends ChangeNotifier {
  bool _isLoggedIn = false;
  String? _email;
  String? _error;

  bool get isLoggedIn => _isLoggedIn;
  String? get email => _email;
  String? get error => _error;

  Future<void> checkAuth() async {
    _isLoggedIn = await ApiService.isLoggedIn();
    if (_isLoggedIn) _email = await ApiService.getUserEmail();
    notifyListeners();
  }

  Future<bool> login(String email, String password) async {
    _error = null;
    try {
      final res = await ApiService.login(email, password);
      if (res['status'] == 200) {
        _isLoggedIn = true;
        _email = email;
        notifyListeners();
        return true;
      }
      _error = res['detail'] ?? 'Invalid credentials';
    } catch (e) {
      _error = 'Network error. Is the server running?';
    }
    notifyListeners();
    return false;
  }

  Future<bool> register(String email, String password) async {
    _error = null;
    try {
      final res = await ApiService.register(email, password);
      if (res['status'] == 201) {
        _isLoggedIn = true;
        _email = email;
        notifyListeners();
        return true;
      }
      _error = res['detail'] ?? 'Registration failed';
    } catch (e) {
      _error = 'Network error. Is the server running?';
    }
    notifyListeners();
    return false;
  }

  Future<void> logout() async {
    await ApiService.logout();
    _isLoggedIn = false;
    _email = null;
    notifyListeners();
  }
}
