import 'package:flutter/material.dart';
import 'package:fl_chart/fl_chart.dart';
import 'package:provider/provider.dart';
import '../services/api_service.dart';
import '../providers/auth_provider.dart';
import 'classify_screen.dart';
import 'history_screen.dart';

class DashboardScreen extends StatefulWidget {
  const DashboardScreen({super.key});

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  int _navIndex = 0;

  final List<Widget> _pages = const [
    _HomeTab(),
    ClassifyScreen(),
    HistoryScreen(),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0D1117),
      body: IndexedStack(index: _navIndex, children: _pages),
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: _navIndex,
        onTap: (i) => setState(() => _navIndex = i),
        backgroundColor: const Color(0xFF161B22),
        selectedItemColor: const Color(0xFF58A6FF),
        unselectedItemColor: Colors.grey[600],
        type: BottomNavigationBarType.fixed,
        items: const [
          BottomNavigationBarItem(icon: Icon(Icons.dashboard_outlined), label: 'Dashboard'),
          BottomNavigationBarItem(icon: Icon(Icons.search), label: 'Classify'),
          BottomNavigationBarItem(icon: Icon(Icons.history), label: 'History'),
        ],
      ),
    );
  }
}

class _HomeTab extends StatefulWidget {
  const _HomeTab();

  @override
  State<_HomeTab> createState() => _HomeTabState();
}

class _HomeTabState extends State<_HomeTab> {
  Map<String, dynamic>? _stats;
  bool _loading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() => _loading = true);
    try {
      final data = await ApiService.getStats();
      if (data['status'] == 200) {
        setState(() { _stats = data; _error = null; });
      } else {
        setState(() => _error = 'Failed to load stats');
      }
    } catch (_) {
      setState(() => _error = 'Network error');
    }
    setState(() => _loading = false);
  }

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthProvider>();
    return Scaffold(
      backgroundColor: const Color(0xFF0D1117),
      appBar: AppBar(
        backgroundColor: const Color(0xFF161B22),
        title: const Text('Spam Filter', style: TextStyle(color: Colors.white)),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh, color: Colors.white),
            onPressed: _load,
          ),
          PopupMenuButton<String>(
            icon: const Icon(Icons.account_circle_outlined, color: Colors.white),
            color: const Color(0xFF161B22),
            onSelected: (v) async {
              if (v == 'logout') {
                await auth.logout();
                if (context.mounted) Navigator.pushReplacementNamed(context, '/');
              }
            },
            itemBuilder: (_) => [
              PopupMenuItem(
                value: 'email',
                enabled: false,
                child: Text(auth.email ?? '', style: const TextStyle(color: Colors.white70)),
              ),
              const PopupMenuItem(
                value: 'logout',
                child: Row(children: [
                  Icon(Icons.logout, color: Color(0xFFDA3633), size: 18),
                  SizedBox(width: 8),
                  Text('Logout', style: TextStyle(color: Color(0xFFDA3633))),
                ]),
              ),
            ],
          ),
        ],
        elevation: 0,
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator(color: Color(0xFF58A6FF)))
          : _error != null
              ? _ErrorState(message: _error!, onRetry: _load)
              : RefreshIndicator(
                  onRefresh: _load,
                  child: SingleChildScrollView(
                    physics: const AlwaysScrollableScrollPhysics(),
                    padding: const EdgeInsets.all(16),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text('Overview',
                            style: TextStyle(
                                color: Colors.white,
                                fontSize: 20,
                                fontWeight: FontWeight.bold)),
                        const SizedBox(height: 16),
                        _StatsGrid(stats: _stats!),
                        const SizedBox(height: 24),
                        if (_stats!['total'] > 0) ...[
                          const Text('Spam vs Legitimate',
                              style: TextStyle(
                                  color: Colors.white,
                                  fontSize: 16,
                                  fontWeight: FontWeight.w600)),
                          const SizedBox(height: 16),
                          _PieSection(stats: _stats!),
                          const SizedBox(height: 24),
                        ],
                        if (_stats!['feedback_accuracy'] != null) ...[
                          _AccuracyCard(accuracy: (_stats!['feedback_accuracy'] as num).toDouble()),
                          const SizedBox(height: 24),
                        ],
                        _InfoCard(
                          icon: Icons.info_outline,
                          title: 'How it works',
                          body:
                              'Messages are classified using an SVM model trained on 5,000+ SMS samples. '
                              'Your feedback helps improve accuracy over time.',
                        ),
                      ],
                    ),
                  ),
                ),
    );
  }
}

class _StatsGrid extends StatelessWidget {
  final Map<String, dynamic> stats;
  const _StatsGrid({required this.stats});

  @override
  Widget build(BuildContext context) {
    final total = stats['total'] as int;
    final spam = stats['spam_count'] as int;
    final ham = stats['ham_count'] as int;
    final fb = stats['feedback_count'] as int;
    final spamPct = total > 0 ? (spam / total * 100).toStringAsFixed(1) : '0';

    return GridView.count(
      crossAxisCount: 2,
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      crossAxisSpacing: 12,
      mainAxisSpacing: 12,
      childAspectRatio: 1.5,
      children: [
        _StatCard(label: 'Total Classified', value: '$total', icon: Icons.message_outlined,
            color: const Color(0xFF58A6FF)),
        _StatCard(label: 'Spam Detected', value: '$spam', icon: Icons.warning_amber_rounded,
            color: const Color(0xFFDA3633)),
        _StatCard(label: 'Legitimate', value: '$ham', icon: Icons.check_circle_outline,
            color: const Color(0xFF238636)),
        _StatCard(label: 'Spam Rate', value: '$spamPct%', icon: Icons.percent,
            color: const Color(0xFFE3B341),
            subtitle: '$fb feedback${fb == 1 ? '' : 's'}'),
      ],
    );
  }
}

class _StatCard extends StatelessWidget {
  final String label;
  final String value;
  final IconData icon;
  final Color color;
  final String? subtitle;

  const _StatCard({
    required this.label,
    required this.value,
    required this.icon,
    required this.color,
    this.subtitle,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: const Color(0xFF161B22),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: const Color(0xFF30363D)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Icon(icon, color: color, size: 22),
          Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text(value,
                style: TextStyle(
                    color: color, fontSize: 22, fontWeight: FontWeight.bold)),
            Text(label, style: TextStyle(color: Colors.grey[500], fontSize: 11)),
            if (subtitle != null)
              Text(subtitle!, style: TextStyle(color: Colors.grey[600], fontSize: 10)),
          ]),
        ],
      ),
    );
  }
}

class _PieSection extends StatelessWidget {
  final Map<String, dynamic> stats;
  const _PieSection({required this.stats});

  @override
  Widget build(BuildContext context) {
    final spam = (stats['spam_count'] as int).toDouble();
    final ham = (stats['ham_count'] as int).toDouble();
    return SizedBox(
      height: 180,
      child: Row(children: [
        Expanded(
          child: PieChart(PieChartData(
            sections: [
              PieChartSectionData(
                value: spam,
                color: const Color(0xFFDA3633),
                title: spam > 0 ? 'Spam' : '',
                radius: 60,
                titleStyle: const TextStyle(color: Colors.white, fontSize: 12),
              ),
              PieChartSectionData(
                value: ham,
                color: const Color(0xFF238636),
                title: ham > 0 ? 'Ham' : '',
                radius: 60,
                titleStyle: const TextStyle(color: Colors.white, fontSize: 12),
              ),
            ],
            sectionsSpace: 2,
            centerSpaceRadius: 30,
          )),
        ),
        const SizedBox(width: 16),
        Column(
          mainAxisAlignment: MainAxisAlignment.center,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _Legend(color: const Color(0xFFDA3633), label: 'Spam ($spam)'),
            const SizedBox(height: 8),
            _Legend(color: const Color(0xFF238636), label: 'Legitimate ($ham)'),
          ],
        ),
      ]),
    );
  }
}

class _Legend extends StatelessWidget {
  final Color color;
  final String label;
  const _Legend({required this.color, required this.label});

  @override
  Widget build(BuildContext context) {
    return Row(children: [
      Container(width: 12, height: 12, decoration: BoxDecoration(color: color, shape: BoxShape.circle)),
      const SizedBox(width: 6),
      Text(label, style: const TextStyle(color: Colors.white70, fontSize: 13)),
    ]);
  }
}

class _AccuracyCard extends StatelessWidget {
  final double accuracy;
  const _AccuracyCard({required this.accuracy});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: const Color(0xFF161B22),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: const Color(0xFF30363D)),
      ),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Row(children: [
          const Icon(Icons.analytics_outlined, color: Color(0xFF58A6FF), size: 18),
          const SizedBox(width: 8),
          const Text('Feedback Accuracy',
              style: TextStyle(color: Colors.white, fontWeight: FontWeight.w600)),
        ]),
        const SizedBox(height: 12),
        ClipRRect(
          borderRadius: BorderRadius.circular(4),
          child: LinearProgressIndicator(
            value: accuracy / 100,
            backgroundColor: Colors.grey[800],
            valueColor: const AlwaysStoppedAnimation<Color>(Color(0xFF238636)),
            minHeight: 8,
          ),
        ),
        const SizedBox(height: 8),
        Text('${accuracy.toStringAsFixed(1)}% of user-corrected classifications were already correct',
            style: TextStyle(color: Colors.grey[500], fontSize: 12)),
      ]),
    );
  }
}

class _InfoCard extends StatelessWidget {
  final IconData icon;
  final String title;
  final String body;
  const _InfoCard({required this.icon, required this.title, required this.body});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: const Color(0xFF161B22),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: const Color(0xFF30363D)),
      ),
      child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Icon(icon, color: const Color(0xFF58A6FF), size: 20),
        const SizedBox(width: 12),
        Expanded(
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text(title,
                style: const TextStyle(
                    color: Colors.white, fontWeight: FontWeight.w600, fontSize: 14)),
            const SizedBox(height: 4),
            Text(body, style: TextStyle(color: Colors.grey[500], fontSize: 13, height: 1.4)),
          ]),
        ),
      ]),
    );
  }
}

class _ErrorState extends StatelessWidget {
  final String message;
  final VoidCallback onRetry;
  const _ErrorState({required this.message, required this.onRetry});

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Column(mainAxisAlignment: MainAxisAlignment.center, children: [
        const Icon(Icons.cloud_off, color: Colors.grey, size: 48),
        const SizedBox(height: 12),
        Text(message, style: const TextStyle(color: Colors.white70)),
        const SizedBox(height: 16),
        ElevatedButton(
          onPressed: onRetry,
          style: ElevatedButton.styleFrom(backgroundColor: const Color(0xFF1F6FEB)),
          child: const Text('Retry', style: TextStyle(color: Colors.white)),
        ),
      ]),
    );
  }
}
