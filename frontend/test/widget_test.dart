// Smoke test for the Workshop Tool scaffold.
//
// Verifies the health screen builds and renders its chrome without throwing.
// autoCheck is disabled so no live network call (or its timer) lingers past
// the test. Real feature coverage arrives with participant/facilitator tests.

import 'package:flutter/material.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:workshop_tool/features/health/health_screen.dart';

void main() {
  testWidgets('Health screen renders its shell', (tester) async {
    dotenv.testLoad(fileInput: 'API_BASE_URL=http://localhost:8000');

    await tester.pumpWidget(
      const ProviderScope(
        child: MaterialApp(home: HealthScreen(autoCheck: false)),
      ),
    );
    await tester.pump();

    expect(find.textContaining('Workshop Tool'), findsOneWidget);
    expect(find.text('Ready'), findsOneWidget);
  });
}
