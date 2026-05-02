import * as React from "react";
import { SafeAreaView, StyleSheet, Text, View } from "react-native";

import type { ContentType, Filters } from "../api/types";
import { Button } from "../components/Button";
import { colors } from "../theme/colors";
import { useSessionStore } from "../state/sessionStore";

function Choice({
  label,
  active,
  onPress,
}: {
  label: string;
  active: boolean;
  onPress: () => void;
}) {
  return (
    <Button
      label={label}
      onPress={onPress}
      variant={active ? "primary" : "ghost"}
      style={{ flex: 1 }}
    />
  );
}

export function FilterScreen({ navigation }: { navigation: any }) {
  const startSession = useSessionStore((s) => s.startSession);
  const isLoading = useSessionStore((s) => s.isLoading);
  const error = useSessionStore((s) => s.error);

  const [contentType, setContentType] = React.useState<ContentType>("movie");

  const filters: Filters = React.useMemo(
    () => ({ content_type: contentType, genre_ids: [], mood: null }),
    [contentType]
  );

  return (
    <SafeAreaView style={styles.safe}>
      <View style={styles.container}>
        <Text style={styles.h1}>StreamSwipe</Text>
        <Text style={styles.p}>Pick a lane, swipe fast, get one great match.</Text>

        <View style={styles.section}>
          <Text style={styles.label}>Content</Text>
          <View style={styles.row}>
            <Choice label="Movies" active={contentType === "movie"} onPress={() => setContentType("movie")} />
            <View style={{ width: 10 }} />
            <Choice label="TV" active={contentType === "tv"} onPress={() => setContentType("tv")} />
            <View style={{ width: 10 }} />
            <Choice label="Anime" active={contentType === "anime"} onPress={() => setContentType("anime")} />
          </View>
        </View>

        {!!error && <Text style={styles.error}>{error}</Text>}

        <Button
          label={isLoading ? "Starting..." : "Start swiping"}
          onPress={async () => {
            await startSession(filters);
            navigation.navigate("Swipe");
          }}
          disabled={isLoading}
        />
        <Text style={styles.footnote}>
          Tip: on phone, set `EXPO_PUBLIC_API_BASE_URL` to your computer’s LAN IP (e.g. http://192.168.x.x:8000).
        </Text>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: colors.bg },
  container: { flex: 1, padding: 18, gap: 14, justifyContent: "center" },
  h1: { color: colors.text, fontSize: 34, fontWeight: "900" },
  p: { color: colors.muted, fontSize: 15, lineHeight: 20 },
  section: { gap: 10, marginTop: 10 },
  label: { color: colors.text, fontSize: 14, fontWeight: "700" },
  row: { flexDirection: "row" },
  error: { color: colors.danger, fontWeight: "700" },
  footnote: { color: colors.muted, fontSize: 12, lineHeight: 16, marginTop: 8 },
});

