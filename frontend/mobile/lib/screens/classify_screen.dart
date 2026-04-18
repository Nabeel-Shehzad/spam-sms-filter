import 'package:flutter/material.dart';
import '../services/api_service.dart';

class ClassifyScreen extends StatefulWidget {
  const ClassifyScreen({super.key});

  @override
  State<ClassifyScreen> createState() => _ClassifyScreenState();
}

class _ClassifyScreenState extends State<ClassifyScreen> {
  final _ctrl = TextEditingController();
  bool _loading = false;
  Map<String, dynamic>? _result;
  String? _error;

  Future<void> _classify() async {
    final text = _ctrl.text.trim();
    if (text.isEmpty) return;
    setState(() {
      _loading = true;
      _result = null;
      _error = null;
    });
    try {
      final res = await ApiService.classify(text);
      if (res['status'] == 200) {
        setState(() => _result = res);
      } else {
        setState(() => _error = 'Classification failed. Try again.');
      }
    } catch (e) {
      setState(() => _error = 'Network error. Is the server running?');
    }
    setState(() => _loading = false);
  }

  Future<void> _submitFeedback(String correctLabel) async {
    if (_result == null) return;
    final logId = _result!['log_id'] as int;
    await ApiService.submitFeedback(logId, correctLabel);
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Thanks! Marked as $correctLabel.'),
          backgroundColor: const Color(0xFF238636),
          behavior: SnackBarBehavior.floating,
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final isSpam = _result?['label'] == 'spam';
    final confidence = (_result?['confidence'] as double? ?? 0.0);

    return Scaffold(
      backgroundColor: const Color(0xFF0D1117),
      appBar: AppBar(
        backgroundColor: const Color(0xFF161B22),
        title: const Text('Classify Message', style: TextStyle(color: Colors.white)),
        iconTheme: const IconThemeData(color: Colors.white),
        elevation: 0,
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('Paste an SMS message below',
                style: TextStyle(color: Colors.white70, fontSize: 14)),
            const SizedBox(height: 10),
            TextField(
              controller: _ctrl,
              maxLines: 5,
              style: const TextStyle(color: Colors.white, fontSize: 14),
              decoration: InputDecoration(
                hintText: 'e.g. "Win a free iPhone now! Click here..."',
                hintStyle: TextStyle(color: Colors.grey[600]),
                filled: true,
                fillColor: const Color(0xFF161B22),
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(10),
                  borderSide: const BorderSide(color: Color(0xFF30363D)),
                ),
                enabledBorder: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(10),
                  borderSide: const BorderSide(color: Color(0xFF30363D)),
                ),
                focusedBorder: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(10),
                  borderSide: const BorderSide(color: Color(0xFF58A6FF)),
                ),
              ),
            ),
            const SizedBox(height: 12),
            SizedBox(
              width: double.infinity,
              height: 48,
              child: ElevatedButton.icon(
                onPressed: _loading ? null : _classify,
                icon: _loading
                    ? const SizedBox(
                        width: 18,
                        height: 18,
                        child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2),
                      )
                    : const Icon(Icons.search, color: Colors.white),
                label: Text(_loading ? 'Analysing...' : 'Classify',
                    style: const TextStyle(color: Colors.white, fontSize: 16)),
                style: ElevatedButton.styleFrom(
                  backgroundColor: const Color(0xFF1F6FEB),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                ),
              ),
            ),
            if (_error != null) ...[
              const SizedBox(height: 16),
              _ErrorCard(message: _error!),
            ],
            if (_result != null) ...[
              const SizedBox(height: 24),
              _ResultCard(
                isSpam: isSpam,
                confidence: confidence,
                modelUsed: _result!['model_used'] ?? '',
                language: _result!['language'] ?? 'en',
                onFeedback: _submitFeedback,
              ),
            ],
          ],
        ),
      ),
    );
  }
}

class _ResultCard extends StatelessWidget {
  final bool isSpam;
  final double confidence;
  final String modelUsed;
  final String language;
  final void Function(String) onFeedback;

  const _ResultCard({
    required this.isSpam,
    required this.confidence,
    required this.modelUsed,
    required this.language,
    required this.onFeedback,
  });

  @override
  Widget build(BuildContext context) {
    final color = isSpam ? const Color(0xFFDA3633) : const Color(0xFF238636);
    final icon = isSpam ? Icons.warning_amber_rounded : Icons.check_circle_outline;
    final label = isSpam ? 'SPAM' : 'LEGITIMATE';
    final pct = (confidence * 100).toStringAsFixed(1);

    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: const Color(0xFF161B22),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: color.withAlpha(100)),
      ),
      child: Column(
        children: [
          Row(
            children: [
              Container(
                width: 48,
                height: 48,
                decoration: BoxDecoration(
                  color: color.withAlpha(30),
                  shape: BoxShape.circle,
                ),
                child: Icon(icon, color: color, size: 28),
              ),
              const SizedBox(width: 16),
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(label,
                      style: TextStyle(
                          color: color, fontSize: 22, fontWeight: FontWeight.bold)),
                  Text('Confidence: $pct%',
                      style: TextStyle(color: Colors.grey[400], fontSize: 13)),
                ],
              ),
            ],
          ),
          const SizedBox(height: 16),
          ClipRRect(
            borderRadius: BorderRadius.circular(4),
            child: LinearProgressIndicator(
              value: confidence,
              backgroundColor: Colors.grey[800],
              valueColor: AlwaysStoppedAnimation<Color>(color),
              minHeight: 8,
            ),
          ),
          const SizedBox(height: 16),
          Row(children: [
            _Tag(label: modelUsed, icon: Icons.memory),
            const SizedBox(width: 8),
            _Tag(label: language.toUpperCase(), icon: Icons.language),
          ]),
          const SizedBox(height: 16),
          const Divider(color: Color(0xFF30363D)),
          const SizedBox(height: 8),
          const Text('Is this correct?',
              style: TextStyle(color: Colors.white70, fontSize: 13)),
          const SizedBox(height: 10),
          Row(children: [
            Expanded(
              child: OutlinedButton.icon(
                onPressed: () => onFeedback('ham'),
                icon: const Icon(Icons.thumb_up_alt_outlined, size: 16),
                label: const Text('Legitimate'),
                style: OutlinedButton.styleFrom(
                  foregroundColor: const Color(0xFF238636),
                  side: const BorderSide(color: Color(0xFF238636)),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                ),
              ),
            ),
            const SizedBox(width: 10),
            Expanded(
              child: OutlinedButton.icon(
                onPressed: () => onFeedback('spam'),
                icon: const Icon(Icons.thumb_down_alt_outlined, size: 16),
                label: const Text('Spam'),
                style: OutlinedButton.styleFrom(
                  foregroundColor: const Color(0xFFDA3633),
                  side: const BorderSide(color: Color(0xFFDA3633)),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                ),
              ),
            ),
          ]),
        ],
      ),
    );
  }
}

class _Tag extends StatelessWidget {
  final String label;
  final IconData icon;
  const _Tag({required this.label, required this.icon});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: const Color(0xFF0D1117),
        borderRadius: BorderRadius.circular(6),
        border: Border.all(color: const Color(0xFF30363D)),
      ),
      child: Row(mainAxisSize: MainAxisSize.min, children: [
        Icon(icon, size: 13, color: Colors.grey[500]),
        const SizedBox(width: 4),
        Text(label, style: TextStyle(color: Colors.grey[400], fontSize: 12)),
      ]),
    );
  }
}

class _ErrorCard extends StatelessWidget {
  final String message;
  const _ErrorCard({required this.message});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Colors.red.withAlpha(20),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: Colors.red.withAlpha(60)),
      ),
      child: Row(children: [
        const Icon(Icons.error_outline, color: Colors.red, size: 18),
        const SizedBox(width: 8),
        Expanded(child: Text(message, style: const TextStyle(color: Colors.red, fontSize: 13))),
      ]),
    );
  }
}
