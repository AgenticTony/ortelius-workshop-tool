import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../features/health/health_screen.dart';
import '../features/participant/join_screen.dart';
import '../features/participant/workshop_screen.dart';

/// App routing. The participant flow is /join -> /workshop.
/// Facilitator routes arrive in Milestone 4.
final appRouter = GoRouter(
  initialLocation: '/join',
  routes: [
    GoRoute(
      path: '/join',
      name: 'join',
      builder: (context, state) => const JoinScreen(),
    ),
    GoRoute(
      path: '/workshop',
      name: 'workshop',
      builder: (context, state) => const WorkshopScreen(),
    ),
    // Kept reachable for a quick connectivity check during dev.
    GoRoute(
      path: '/health',
      name: 'health',
      builder: (context, state) => const HealthScreen(),
    ),
  ],
  errorBuilder: (context, state) => Scaffold(
    appBar: AppBar(title: const Text('Not found')),
    body: Center(child: Text('No route for ${state.uri}')),
  ),
);
