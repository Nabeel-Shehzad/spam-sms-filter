import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../services/api_service.dart';

class HistoryScreen extends StatefulWidget {
  const HistoryScreen({super.key});

  @override
  State<HistoryScreen> createState() => _HistoryScreenState();
}

class _HistoryScreenState extends State<HistoryScreen> {
  List<dynamic> _logs = [];
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
      final data = await ApiService.getHistory(limit: 50);
      setState(() { _logs = data; _error = null; });
    } catch (_) {
      setState(() => _error = 'Network error');
    }
    setState(() => _loading = false);
  }

  Future<void> _submitFeedback(int logId, String currentLabel) async {
    final opposite = currentLabel == 'spam' ? 'ham' : 'spam';
    final confirm = await showDialog<bool>(
      context: context,
      builder: (_) => AlertDialog(
        backgroundColor: const Color(0xFF161B22),
        title: const Text('Report Misclassification',
            style: TextStyle(color: Colors.white, fontSize: 16)),
        content: Text(
          'Mark this message as "$opposite" instead of "$currentLabel"?',
          style: const TextStyle(color: Colors.white70),
        ),
        actions: [
          TextButton(
              onPressed: () => Navigator.pop(context, false),
              child: const Text('Cancel', style: TextStyle(color: Colors.grey))),
          ElevatedButton(
              onPressed: () => Navigator.pop(context, true),
              style: ElevatedButton.styleFrom(backgroundColor: const Color(0xFF1F6FEB)),
              child: const Text('Confirm', style: TextStyle(color: Colors.white))),
        ],
      ),
    );
    if (confirm == true) {
      await ApiService.submitFeedback(logId, opposite);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Feedback submitted: marked as $opposite'),
            backgroundColor: const Color(0xFF238636),
            behavior: SnackBarBehavior.floating,
          ),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0D1117),
      appBar: AppBar(
        backgroundColor: const Color(0xFF161B22),
        title: const Text('Classification History', style: TextStyle(color: Colors.white)),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh, color: Colors.white),
            onPressed: _load,
          ),
        ],
        elevation: 0,
        automaticallyImplyLeading: false,
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator(color: Color(0xFF58A6FF)))
          : _error != null
              ? Center(
                  child: Column(mainAxisAlignment: MainAxisAlignment.center, children: [
                    const Icon(Icons.cloud_off, color: Colors.grey, size: 40),
                    const SizedBox(height: 12),
                    Text(_error!, style: const TextStyle(color: Colors.white70)),
                    const SizedBox(height: 12),
                    ElevatedButton(
                      onPressed: _load,
                      style: ElevatedButton.styleFrom(backgroundColor: const Color(0xFF1F6FEB)),
                      child: const Text('Retry', style: TextStyle(color: Colors.white)),
                    ),
                  ]),
                )
              : _logs.isEmpty
                  ? const Center(
                      child: Column(mainAxisAlignment: MainAxisAlignment.center, children: [
                        Icon(Icons.inbox_outlined, color: Colors.grey, size: 48),
                        SizedBox(height: 12),
                        Text('No classifications yet',
                            style: TextStyle(color: Colors.white70)),
                        SizedBox(height: 4),
                        Text('Use Classify tab to get started',
                            style: TextStyle(color: Colors.grey, fontSize: 13)),
                      ]),
                    )
                  : RefreshIndicator(
                      onRefresh: _load,
                      child: ListView.separated(
                        padding: const EdgeInsets.all(12),
                        itemCount: _logs.length,
                        separatorBuilder: (context, index) => const SizedBox(height: 8),
                        itemBuilder: (_, i) {
                          final log = _logs[i] as Map<String, dynamic>;
                          return _LogTile(log: log, onFeedback: _submitFeedback);
                        },
                      ),
                    ),
    );
  }
}

class _LogTile extends StatelessWidget {
  final Map<String, dynamic> log;
  final Future<void> Function(int, String) onFeedback;

  const _LogTile({required this.log, required this.onFeedback});

  @override
  Widget build(BuildContext context) {
    final isSpam = log['predicted_label'] == 'spam';
    final color = isSpam ? const Color(0xFFDA3633) : const Color(0xFF238636);
    final pct = ((log['confidence'] as num) * 100).toStringAsFixed(0);
    final ts = DateTime.tryParse(log['created_at'] ?? '');
    final timeStr = ts != null
        ? DateFormat('MMM d, HH:mm').format(ts.toLocal())
        : '';
    final text = log['message_text'] as String;

    return Container(
      decoration: BoxDecoration(
        color: const Color(0xFF161B22),
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: const Color(0xFF30363D)),
      ),
      child: ListTile(
        contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 6),
        leading: Container(
          width: 40,
          height: 40,
          decoration: BoxDecoration(
            color: color.withAlpha(30),
            shape: BoxShape.circle,
          ),
          child: Icon(
            isSpam ? Icons.warning_amber_rounded : Icons.check_circle_outline,
            color: color,
            size: 22,
          ),
        ),
        title: Text(
          text.length > 70 ? '${text.substring(0, 70)}…' : text,
          style: const TextStyle(color: Colors.white, fontSize: 13),
          maxLines: 2,
        ),
        subtitle: Padding(
          padding: const EdgeInsets.only(top: 4),
          child: Row(children: [
            Text(
              isSpam ? 'SPAM' : 'LEGITIMATE',
              style: TextStyle(
                  color: color, fontSize: 11, fontWeight: FontWeight.bold),
            ),
            Text(' • $pct%', style: TextStyle(color: Colors.grey[600], fontSize: 11)),
            Text(' • $timeStr', style: TextStyle(color: Colors.grey[600], fontSize: 11)),
          ]),
        ),
        trailing: IconButton(
          icon: const Icon(Icons.flag_outlined, color: Colors.grey, size: 20),
          tooltip: 'Report misclassification',
          onPressed: () => onFeedback(log['id'] as int, log['predicted_label'] as String),
        ),
      ),
    );
  }
}
