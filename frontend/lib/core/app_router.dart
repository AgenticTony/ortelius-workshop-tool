import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../features/health/health_screen.dart';
import '../features/home/home_screen.dart';
import '../features/participant/join_screen.dart';
import '../features/participant/workshop_screen.dart';
import '../features/facilitator/create_session_screen.dart';
import '../features/facilitator/facilitator_dashboard_screen.dart';
import '../features/facilitator/report_screen.dart';

/// App routing. Entry is the role-picker home; from there the facilitator
/// path is /facilitate/new -> /facilitate -> /facilitate/report, and the
/// participant path is /join -> /workshop.
final appRouter = GoRouter(
  initialLocation: '/',
  routes: [
    GoRoute(
      path: '/',
      name: 'home',
      builder: (context, state) => const HomeScreen(),
    ),
    // ── Facilitator ──────────────────────────────────────────
    GoRoute(
      path: '/facilitate/new',
      name: 'facilitateNew',
      builder: (context, state) => const CreateSessionScreen(),
    ),
    GoRoute(
      path: '/facilitate',
      name: 'facilitate',
      builder: (context, state) => const FacilitatorDashboardScreen(),
    ),
    GoRoute(
      path: '/facilitate/report',
      name: 'facilitateReport',
      builder: (context, state) => const ReportScreen(),
    ),
    // ── Participant ──────────────────────────────────────────
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
    // ── Dev ──────────────────────────────────────────────────
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
