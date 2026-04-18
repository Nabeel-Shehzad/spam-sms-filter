import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'providers/auth_provider.dart';
import 'screens/auth_screen.dart';
import 'screens/dashboard_screen.dart';

void main() {
  runApp(
    ChangeNotifierProvider(
      create: (_) => AuthProvider(),
      child: const SpamFilterApp(),
    ),
  );
}

class SpamFilterApp extends StatelessWidget {
  const SpamFilterApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Spam SMS Filter',
      debugShowCheckedModeBanner: false,
      theme: ThemeData.dark().copyWith(
        scaffoldBackgroundColor: const Color(0xFF0D1117),
        colorScheme: const ColorScheme.dark(
          primary: Color(0xFF58A6FF),
          secondary: Color(0xFF238636),
        ),
      ),
      home: const _Root(),
      routes: {
        '/': (_) => const AuthScreen(),
        '/home': (_) => const DashboardScreen(),
      },
    );
  }
}

class _Root extends StatefulWidget {
  const _Root();

  @override
  State<_Root> createState() => _RootState();
}

class _RootState extends State<_Root> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) async {
      final auth = context.read<AuthProvider>();
      await auth.checkAuth();
      if (!mounted) return;
      Navigator.pushReplacementNamed(context, auth.isLoggedIn ? '/home' : '/');
    });
  }

  @override
  Widget build(BuildContext context) {
    return const Scaffold(
      backgroundColor: Color(0xFF0D1117),
      body: Center(child: CircularProgressIndicator(color: Color(0xFF58A6FF))),
    );
  }
}
