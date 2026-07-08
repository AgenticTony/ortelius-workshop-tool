import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../features/health/health_screen.dart';
import '../features/home/home_screen.dart';
import '../features/participant/join_screen.dart';
import '../features/participant/workshop_screen.dart';
import '../features/facilitator/create_session_screen.dart';
import '../features/facilitator/facilitator_dashboard_screen.dart';
import '../features/facilitator/report_screen.dart';
import '../widgets/page_slide_transition.dart';

/// App routing. Entry is the role-picker home; from there the facilitator
/// path is /facilitate/new -> /facilitate -> /facilitate/report, and the
/// participant path is /join -> /workshop.
///
/// Every route uses [pageSlide] so navigation feels alive instead of cutting
/// hard. Reduced-motion collapses it to a plain fade.
final appRouter = GoRouter(
  initialLocation: '/',
  routes: [
    GoRoute(
      path: '/',
      name: 'home',
      pageBuilder: (context, state) =>
          pageSlide(child: const HomeScreen(), state: state, name: 'home'),
    ),
    // ── Facilitator ──────────────────────────────────────────
    GoRoute(
      path: '/facilitate/new',
      name: 'facilitateNew',
      pageBuilder: (context, state) => pageSlide(
          child: const CreateSessionScreen(), state: state, name: 'facilitateNew'),
    ),
    GoRoute(
      path: '/facilitate',
      name: 'facilitate',
      pageBuilder: (context, state) => pageSlide(
          child: const FacilitatorDashboardScreen(),
          state: state,
          name: 'facilitate'),
    ),
    GoRoute(
      path: '/facilitate/report',
      name: 'facilitateReport',
      pageBuilder: (context, state) => pageSlide(
          child: const ReportScreen(), state: state, name: 'facilitateReport'),
    ),
    // ── Participant ──────────────────────────────────────────
    // The QR code encodes the join code as a query param inside the URL fragment
    // (https://origin/#/join?code=ABC123) under Flutter web's default hash
    // strategy. GoRouter parses that fragment into state.uri.queryParameters,
    // so we read the code here — Uri.base.queryParameters can't see fragment
    // params and would leave the field unpre-filled.
    GoRoute(
      path: '/join',
      name: 'join',
      pageBuilder: (context, state) => pageSlide(
        child: JoinScreen(initialCode: state.uri.queryParameters['code']),
        state: state,
        name: 'join',
      ),
    ),
    GoRoute(
      path: '/workshop',
      name: 'workshop',
      pageBuilder: (context, state) => pageSlide(
          child: const WorkshopScreen(), state: state, name: 'workshop'),
    ),
    // ── Dev ──────────────────────────────────────────────────
    GoRoute(
      path: '/health',
      name: 'health',
      pageBuilder: (context, state) => pageSlide(
          child: const HealthScreen(), state: state, name: 'health'),
    ),
  ],
  errorBuilder: (context, state) => Scaffold(
    appBar: AppBar(title: const Text('Not found')),
    body: Center(child: Text('No route for ${state.uri}')),
  ),
);
