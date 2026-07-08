import 'package:flutter/material.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'core/theme/app_theme.dart';
import 'core/app_router.dart';

/// Entry point. Loads .env (backend URL) before running the app so config is
/// available synchronously once the widget tree builds.
Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await dotenv.load(fileName: '.env');
  runApp(const ProviderScope(child: WorkshopToolApp()));
}

class WorkshopToolApp extends StatelessWidget {
  const WorkshopToolApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp.router(
      title: 'Workshop Tool',
      theme: AppTheme.build(),
      routerConfig: appRouter,
      debugShowCheckedModeBanner: false,
    );
  }
}
