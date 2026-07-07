import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/theme/layout.dart';
import '../../widgets/screen_scaffold.dart';
import 'facilitator_session_controller.dart';

// ignore_for_file: deprecated_member_use
// RadioListTile.groupValue/onChanged are deprecated in favor of RadioGroup in
// this Flutter version, but RadioGroup is itself brand-new and churning. We
// keep the stable RadioListTile API for the prototype; revisit in the polish
// milestone once the new API settles.

/// Facilitator: create a new workshop session. Pick a topic + framework, and
/// (for custom frameworks) author at least two category names — Christian's
/// "beskrivning av innehållet" requirement, surfaced as a UI.
class CreateSessionScreen extends ConsumerStatefulWidget {
  const CreateSessionScreen({super.key});

  @override
  ConsumerState<CreateSessionScreen> createState() =>
      _CreateSessionScreenState();
}

class _CreateSessionScreenState extends ConsumerState<CreateSessionScreen> {
  static const _frameworks = [
    ('swot', 'SWOT', 'Strengths, Weaknesses, Opportunities, Threats'),
    ('pestel', 'PESTEL',
        'Political, Economic, Social, Technological, Environmental, Legal'),
    ('custom', 'Custom', 'Define your own categories'),
  ];

  final _formKey = GlobalKey<FormState>();
  final _topicController = TextEditingController();
  String _framework = 'swot';

  /// Custom category name controllers. Start with two empty rows.
  final List<TextEditingController> _categoryControllers = [
    TextEditingController(),
    TextEditingController(),
  ];

  @override
  void dispose() {
    _topicController.dispose();
    for (final c in _categoryControllers) {
      c.dispose();
    }
    super.dispose();
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;
    List<String>? customCategories;
    if (_framework == 'custom') {
      customCategories = _categoryControllers
          .map((c) => c.text.trim())
          .where((s) => s.isNotEmpty)
          .toList();
    }
    final ok = await ref.read(facilitatorSessionProvider.notifier).createSession(
          topic: _topicController.text,
          framework: _framework,
          customCategories: customCategories,
        );
    if (!mounted) return;
    if (ok) {
      context.go('/facilitate');
    } else {
      final err =
          ref.read(facilitatorSessionProvider).error ?? 'Could not create session';
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(err)));
    }
  }

  @override
  Widget build(BuildContext context) {
    final state = ref.watch(facilitatorSessionProvider);
    final theme = Theme.of(context);
    return ScrollableScaffold(
      maxWidth: Layout.contentMaxWidth,
      appBar: AppBar(title: const Text('New workshop')),
      child: Form(
        key: _formKey,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const SizedBox(height: 8),
            Text('Set up your workshop', style: theme.textTheme.headlineSmall),
            const SizedBox(height: 6),
            Text(
              'Pick a topic and a framework for the AI to cluster ideas into.',
              style: theme.textTheme.bodyMedium?.copyWith(
                color: theme.colorScheme.onSurfaceVariant,
              ),
            ),
            const SizedBox(height: 24),
            TextFormField(
              controller: _topicController,
              decoration: const InputDecoration(
                labelText: 'Workshop topic',
                hintText: 'e.g. Q3 strategy review',
                prefixIcon: Icon(Icons.subject_rounded),
              ),
              textInputAction: TextInputAction.next,
              validator: (v) =>
                  (v == null || v.trim().isEmpty) ? 'Enter a topic' : null,
            ),
            const SizedBox(height: 24),
            Text('Framework', style: theme.textTheme.titleSmall),
            const SizedBox(height: 4),
            ..._frameworks.map((f) {
              final (id, label, desc) = f;
              return RadioListTile<String>(
                value: id,
                groupValue: _framework,
                onChanged: (v) => setState(() => _framework = v!),
                title: Text(label),
                subtitle: Text(desc),
                contentPadding: const EdgeInsets.symmetric(horizontal: 4),
                dense: true,
              );
            }),
            if (_framework == 'custom') ...[
              const SizedBox(height: 12),
              _customCategoriesEditor(theme),
            ],
            const SizedBox(height: 32),
            SizedBox(
              width: double.infinity,
              child: FilledButton.icon(
                onPressed: state.creating ? null : _submit,
                icon: state.creating
                    ? const SizedBox(
                        width: 18,
                        height: 18,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                    : const Icon(Icons.rocket_launch_outlined),
                label: Text(state.creating ? 'Creating…' : 'Create session'),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _customCategoriesEditor(ThemeData theme) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text('Categories (at least 2)', style: theme.textTheme.titleSmall),
            TextButton.icon(
              onPressed: () => setState(
                  () => _categoryControllers.add(TextEditingController())),
              icon: const Icon(Icons.add_rounded),
              label: const Text('Add'),
            ),
          ],
        ),
        ..._categoryControllers.asMap().entries.map((entry) {
          final i = entry.key;
          final c = entry.value;
          final canRemove = _categoryControllers.length > 2;
          return Padding(
            padding: const EdgeInsets.only(bottom: 8),
            child: Row(
              children: [
                Expanded(
                  child: TextFormField(
                    controller: c,
                    decoration: InputDecoration(
                      labelText: 'Category ${i + 1}',
                    ),
                    validator: (v) {
                      // Validate non-empty only for the first two; extras optional.
                      if (i < 2 && (v == null || v.trim().isEmpty)) {
                        return 'Required';
                      }
                      return null;
                    },
                  ),
                ),
                if (canRemove)
                  IconButton(
                    tooltip: 'Remove',
                    icon: const Icon(Icons.remove_circle_outline_rounded),
                    onPressed: () => setState(() {
                      c.dispose();
                      _categoryControllers.removeAt(i);
                    }),
                  ),
              ],
            ),
          );
        }),
        Text(
          'Participants\' ideas will be clustered into these. The AI uses the '
          'category names to understand intent.',
          style: theme.textTheme.bodySmall?.copyWith(
            color: theme.colorScheme.onSurfaceVariant,
          ),
        ),
      ],
    );
  }
}
