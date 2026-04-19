import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../services/sms_service.dart';
import '../utils/text_utils.dart';

class InboxScreen extends StatefulWidget {
  const InboxScreen({super.key});

  @override
  State<InboxScreen> createState() => _InboxScreenState();
}

class _InboxScreenState extends State<InboxScreen> {
  List<Map<String, dynamic>> _messages = [];
  bool _loading = false;
  bool _hasPermission = false;
  int _progress = 0;
  int _total = 0;
  String _filter = 'all'; // 'all' | 'spam' | 'ham'

  @override
  void initState() {
    super.initState();
    _checkAndLoad();
  }

  Future<void> _checkAndLoad() async {
    final granted = await SmsService.requestPermissions();
    setState(() => _hasPermission = granted);
    if (granted) _scanInbox();
  }

  Future<void> _scanInbox() async {
    setState(() {
      _loading = true;
      _progress = 0;
      _total = 0;
      _messages = [];
    });

    final results = await SmsService.classifyInbox(
      onProgress: (done, total) {
        if (mounted) setState(() { _progress = done; _total = total; });
      },
    );

    if (mounted) {
      setState(() {
        _messages = results;
        _loading = false;
      });
    }
  }

  List<Map<String, dynamic>> get _filtered {
    if (_filter == 'all') return _messages;
    return _messages.where((m) => m['label'] == _filter).toList();
  }

  int get _spamCount => _messages.where((m) => m['label'] == 'spam').length;
  int get _hamCount => _messages.where((m) => m['label'] == 'ham').length;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0D1117),
      appBar: AppBar(
        backgroundColor: const Color(0xFF161B22),
        title: const Text('SMS Inbox', style: TextStyle(color: Colors.white)),
        automaticallyImplyLeading: false,
        actions: [
          if (!_loading && _hasPermission)
            IconButton(
              icon: const Icon(Icons.refresh, color: Colors.white),
              onPressed: _scanInbox,
              tooltip: 'Re-scan inbox',
            ),
        ],
        elevation: 0,
      ),
      body: !_hasPermission
          ? _PermissionPrompt(onGrant: _checkAndLoad)
          : _loading
              ? _ScanningProgress(done: _progress, total: _total)
              : _messages.isEmpty
                  ? const _EmptyState()
                  : Column(
                      children: [
                        _SummaryBar(
                          total: _messages.length,
                          spam: _spamCount,
                          ham: _hamCount,
                          filter: _filter,
                          onFilter: (f) => setState(() => _filter = f),
                        ),
                        Expanded(
                          child: ListView.separated(
                            padding: const EdgeInsets.all(12),
                            itemCount: _filtered.length,
                            separatorBuilder: (_, _) => const SizedBox(height: 8),
                            itemBuilder: (_, i) => _MessageTile(msg: _filtered[i]),
                          ),
                        ),
                      ],
                    ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────

class _SummaryBar extends StatelessWidget {
  final int total, spam, ham;
  final String filter;
  final void Function(String) onFilter;

  const _SummaryBar({
    required this.total,
    required this.spam,
    required this.ham,
    required this.filter,
    required this.onFilter,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      color: const Color(0xFF161B22),
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
      child: Row(children: [
        _Chip(label: 'All $total', value: 'all', active: filter == 'all',
            color: const Color(0xFF58A6FF), onTap: onFilter),
        const SizedBox(width: 8),
        _Chip(label: '⚠️ Spam $spam', value: 'spam', active: filter == 'spam',
            color: const Color(0xFFDA3633), onTap: onFilter),
        const SizedBox(width: 8),
        _Chip(label: '✓ Ham $ham', value: 'ham', active: filter == 'ham',
            color: const Color(0xFF238636), onTap: onFilter),
      ]),
    );
  }
}

class _Chip extends StatelessWidget {
  final String label, value;
  final bool active;
  final Color color;
  final void Function(String) onTap;

  const _Chip({
    required this.label, required this.value, required this.active,
    required this.color, required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: () => onTap(value),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
        decoration: BoxDecoration(
          color: active ? color.withAlpha(40) : Colors.transparent,
          border: Border.all(color: active ? color : const Color(0xFF30363D)),
          borderRadius: BorderRadius.circular(20),
        ),
        child: Text(label,
            style: TextStyle(
                color: active ? color : Colors.grey,
                fontSize: 12,
                fontWeight: active ? FontWeight.bold : FontWeight.normal)),
      ),
    );
  }
}

class _MessageTile extends StatelessWidget {
  final Map<String, dynamic> msg;
  const _MessageTile({required this.msg});

  @override
  Widget build(BuildContext context) {
    final isSpam = msg['label'] == 'spam';
    final color = isSpam ? const Color(0xFFDA3633) : const Color(0xFF238636);
    final pct = ((msg['confidence'] as double) * 100).toStringAsFixed(0);
    final date = msg['date'] != null
        ? DateFormat('MMM d, HH:mm')
            .format(DateTime.fromMillisecondsSinceEpoch(msg['date'] as int))
        : '';

    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: const Color(0xFF161B22),
        borderRadius: BorderRadius.circular(10),
        border: Border.all(
          color: isSpam ? const Color(0xFFDA3633).withAlpha(60) : const Color(0xFF30363D),
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(children: [
            Icon(
              isSpam ? Icons.warning_amber_rounded : Icons.check_circle_outline,
              color: color,
              size: 16,
            ),
            const SizedBox(width: 6),
            Expanded(
              child: Text(
                msg['address'] as String,
                style: const TextStyle(
                    color: Colors.white, fontWeight: FontWeight.w600, fontSize: 13),
                overflow: TextOverflow.ellipsis,
              ),
            ),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
              decoration: BoxDecoration(
                color: color.withAlpha(25),
                borderRadius: BorderRadius.circular(10),
              ),
              child: Text(
                '${isSpam ? "SPAM" : "HAM"} $pct%',
                style: TextStyle(color: color, fontSize: 11, fontWeight: FontWeight.bold),
              ),
            ),
          ]),
          const SizedBox(height: 6),
          Text(
            msg['body'] as String,
            textDirection: directionOf(msg['body'] as String),
            textAlign: alignOf(msg['body'] as String),
            style: TextStyle(color: Colors.grey[400], fontSize: 13, height: 1.3),
            maxLines: 3,
            overflow: TextOverflow.ellipsis,
          ),
          if (date.isNotEmpty) ...[
            const SizedBox(height: 6),
            Text(date, style: TextStyle(color: Colors.grey[600], fontSize: 11)),
          ],
        ],
      ),
    );
  }
}

class _ScanningProgress extends StatelessWidget {
  final int done, total;
  const _ScanningProgress({required this.done, required this.total});

  @override
  Widget build(BuildContext context) {
    final pct = total > 0 ? done / total : 0.0;
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(40),
        child: Column(mainAxisAlignment: MainAxisAlignment.center, children: [
          const Icon(Icons.search, color: Color(0xFF58A6FF), size: 48),
          const SizedBox(height: 20),
          const Text('Scanning & classifying inbox…',
              style: TextStyle(color: Colors.white, fontSize: 16)),
          const SizedBox(height: 8),
          Text(
            total > 0 ? '$done / $total messages' : 'Reading inbox…',
            style: TextStyle(color: Colors.grey[500], fontSize: 13),
          ),
          const SizedBox(height: 20),
          ClipRRect(
            borderRadius: BorderRadius.circular(4),
            child: LinearProgressIndicator(
              value: total > 0 ? pct : null,
              backgroundColor: Colors.grey[800],
              valueColor: const AlwaysStoppedAnimation<Color>(Color(0xFF58A6FF)),
              minHeight: 6,
            ),
          ),
        ]),
      ),
    );
  }
}

class _PermissionPrompt extends StatelessWidget {
  final VoidCallback onGrant;
  const _PermissionPrompt({required this.onGrant});

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(mainAxisAlignment: MainAxisAlignment.center, children: [
          const Icon(Icons.sms_outlined, color: Color(0xFF58A6FF), size: 56),
          const SizedBox(height: 20),
          const Text('SMS Access Required',
              style: TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold)),
          const SizedBox(height: 10),
          Text(
            'Grant permission to read your SMS inbox so the app can classify all your messages automatically.',
            textAlign: TextAlign.center,
            style: TextStyle(color: Colors.grey[400], fontSize: 14, height: 1.5),
          ),
          const SizedBox(height: 24),
          ElevatedButton.icon(
            onPressed: onGrant,
            icon: const Icon(Icons.lock_open, color: Colors.white),
            label: const Text('Grant Permission', style: TextStyle(color: Colors.white)),
            style: ElevatedButton.styleFrom(
              backgroundColor: const Color(0xFF238636),
              padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
            ),
          ),
        ]),
      ),
    );
  }
}

class _EmptyState extends StatelessWidget {
  const _EmptyState();

  @override
  Widget build(BuildContext context) {
    return const Center(
      child: Column(mainAxisAlignment: MainAxisAlignment.center, children: [
        Icon(Icons.inbox_outlined, color: Colors.grey, size: 48),
        SizedBox(height: 12),
        Text('No messages found', style: TextStyle(color: Colors.white70)),
      ]),
    );
  }
}
