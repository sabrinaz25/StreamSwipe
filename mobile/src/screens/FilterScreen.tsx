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

  const [contentTypes, setContentTypes] = React.useState<ContentType[]>(["movie"]);

  const filters: Filters = React.useMemo(
    () => ({ content_types: contentTypes, genre_ids: [], mood: null }),
    [contentTypes]
  );

  return (
    <SafeAreaView style={styles.safe}>
      <View style={styles.container}>
        <Text style={styles.h1}>StreamSwipe</Text>
        <Text style={styles.p}>Pick a lane, swipe fast, get one great match.</Text>

        <View style={styles.section}>
          <Text style={styles.label}>Content</Text>
          <View style={styles.row}>
            <Choice
              label="Movies"
              active={contentTypes.includes("movie")}
              onPress={() =>
                setContentTypes((prev) =>
                  prev.includes("movie") ? prev.filter((t) => t !== "movie") : [...prev, "movie"]
                )
              }
            />
            <View style={{ width: 10 }} />
            <Choice
              label="TV"
              active={contentTypes.includes("tv")}
              onPress={() =>
                setContentTypes((prev) => (prev.includes("tv") ? prev.filter((t) => t !== "tv") : [...prev, "tv"]))
              }
            />
            <View style={{ width: 10 }} />
            <Choice
              label="Anime"
              active={contentTypes.includes("anime")}
              onPress={() =>
                setContentTypes((prev) =>
                  prev.includes("anime") ? prev.filter((t) => t !== "anime") : [...prev, "anime"]
                )
              }
            />
          </View>
        </View>

        {!!error && <Text style={styles.error}>{error}</Text>}

        <Button
          label={isLoading ? "Starting..." : "Start swiping"}
          onPress={async () => {
            if (filters.content_types.length === 0) return;
            await startSession(filters);
            navigation.navigate("Swipe");
          }}
          disabled={isLoading || filters.content_types.length === 0}
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

