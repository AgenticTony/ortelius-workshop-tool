import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

/// App entry screen: pick facilitator or participant.
class HomeScreen extends StatelessWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Scaffold(
      body: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 420),
          child: Padding(
            padding: const EdgeInsets.all(32),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                Icon(Icons.groups_outlined,
                    size: 72, color: theme.colorScheme.primary),
                const SizedBox(height: 12),
                Text('Workshop Tool',
                    textAlign: TextAlign.center,
                    style: theme.textTheme.headlineMedium),
                const SizedBox(height: 8),
                Text(
                  'Capture, cluster, and report workshop ideas.',
                  textAlign: TextAlign.center,
                  style: theme.textTheme.bodyMedium,
                ),
                const SizedBox(height: 32),
                FilledButton.icon(
                  onPressed: () => context.go('/facilitate/new'),
                  icon: const Icon(Icons.manage_accounts_outlined),
                  label: const Text('I\'m the facilitator'),
                ),
                const SizedBox(height: 12),
                OutlinedButton.icon(
                  onPressed: () => context.go('/join'),
                  icon: const Icon(Icons.login),
                  label: const Text('I\'m a participant'),
                ),
                const SizedBox(height: 24),
                TextButton(
                  onPressed: () => context.go('/health'),
                  child: const Text('Check backend connection'),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
