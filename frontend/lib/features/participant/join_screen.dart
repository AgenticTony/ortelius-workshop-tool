import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:google_fonts/google_fonts.dart';

import '../../core/theme/app_colors.dart';
import '../../widgets/screen_scaffold.dart';
import 'participant_session_controller.dart';

/// Participant join screen: enter a session's 6-char access code + a display
/// name, then join and navigate to the workshop room.
class JoinScreen extends ConsumerStatefulWidget {
  const JoinScreen({super.key, this.initialCode});

  /// Access code pre-filled from the URL (the QR-code join path), if any.
  final String? initialCode;

  @override
  ConsumerState<JoinScreen> createState() => _JoinScreenState();
}

class _JoinScreenState extends ConsumerState<JoinScreen> {
  final _formKey = GlobalKey<FormState>();
  final _codeController = TextEditingController();
  final _nameController = TextEditingController();

  @override
  void initState() {
    super.initState();
    // Pre-fill the access code if the QR-code join URL provided one (passed in
    // from the router, which reads the fragment's query param — see app_router).
    final code = widget.initialCode;
    if (code != null && code.isNotEmpty) {
      _codeController.text = code;
    }
  }

  @override
  void dispose() {
    _codeController.dispose();
    _nameController.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;
    final controller = ref.read(participantSessionProvider.notifier);
    final ok = await controller.joinByCode(
      _codeController.text,
      _nameController.text,
    );
    if (!mounted) return;
    if (ok) {
      context.go('/workshop');
    } else {
      // The controller surfaces an error in state; show it as a snackbar.
      final err = ref.read(participantSessionProvider).error ?? 'Join failed';
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(err)),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final state = ref.watch(participantSessionProvider);
    return Scaffold(
      appBar: AppBar(title: const Text('Join a workshop')),
      body: SafeArea(
        child: ScreenScaffold(
          child: Form(
            key: _formKey,
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              crossAxisAlignment: CrossAxisAlignment.center,
              children: [
                // ── Hero ────────────────────────────────────────────────
                Container(
                  width: 56,
                  height: 56,
                  decoration: BoxDecoration(
                    color: AppColors.accent.withValues(alpha: 0.12),
                    borderRadius: BorderRadius.circular(16),
                  ),
                  child: const Icon(
                    Icons.vpn_key_rounded,
                    size: 28,
                    color: AppColors.accent,
                  ),
                ),
                const SizedBox(height: 20),
                Text(
                  'Enter the code your\nfacilitator shared',
                  textAlign: TextAlign.center,
                  style: theme.textTheme.titleLarge?.copyWith(
                    color: theme.colorScheme.onSurface,
                    height: 1.4,
                  ),
                ),
                const SizedBox(height: 28),

                // ── Access code — big, mono, letter-spaced ─────────────
                // The code is a credential people read char-by-char; the
                // mono face + wide tracking makes it scannable + matchable.
                TextFormField(
                  controller: _codeController,
                  decoration: const InputDecoration(
                    labelText: 'Access code',
                    hintText: 'MNJ36M',
                    prefixIcon: Icon(Icons.tag_rounded),
                  ),
                  style: GoogleFonts.jetBrainsMono(
                    fontSize: 20,
                    fontWeight: FontWeight.w600,
                    letterSpacing: 6,
                    color: AppColors.textPrimary,
                  ),
                  textCapitalization: TextCapitalization.characters,
                  textInputAction: TextInputAction.next,
                  validator: (v) =>
                      (v == null || v.trim().isEmpty) ? 'Enter the code' : null,
                ),
                const SizedBox(height: 14),
                TextFormField(
                  controller: _nameController,
                  decoration: const InputDecoration(
                    labelText: 'Your name',
                    prefixIcon: Icon(Icons.person_outline_rounded),
                  ),
                  textInputAction: TextInputAction.done,
                  onFieldSubmitted: (_) => _submit(),
                  validator: (v) => (v == null || v.trim().isEmpty)
                      ? 'Enter your name'
                      : null,
                ),
                const SizedBox(height: 28),

                // ── Join button — centered, natural width ──────────────
                // NOT stretched: sized to its content via a fixed width, so
                // it doesn't span the whole column edge-to-edge.
                SizedBox(
                  width: double.infinity,
                  child: FilledButton.icon(
                    onPressed: state.loading ? null : _submit,
                    icon: state.loading
                        ? const SizedBox(
                            height: 18,
                            width: 18,
                            child: CircularProgressIndicator(strokeWidth: 2),
                          )
                        : const Icon(Icons.arrow_forward_rounded),
                    label: const Text('Join workshop'),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
