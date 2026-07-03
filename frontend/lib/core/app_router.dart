import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../features/health/health_screen.dart';

/// App routing. Minimal for the scaffold — just the connection check as the
/// home route. Participant and facilitator routes arrive in Milestones 3–4.
final appRouter = GoRouter(
  initialLocation: '/',
  routes: [
    GoRoute(
      path: '/',
      name: 'home',
      builder: (context, state) => const HealthScreen(),
    ),
  ],
  errorBuilder: (context, state) => Scaffold(
    appBar: AppBar(title: const Text('Not found')),
    body: Center(child: Text('No route for ${state.uri}')),
  ),
);
