import * as React from "react";
import { SafeAreaView, ScrollView, StyleSheet, Text, View } from "react-native";

import { api } from "../api/client";
import type { RecommendationJustification } from "../api/types";
import { Card } from "../components/Card";
import { Button } from "../components/Button";
import { colors } from "../theme/colors";
import { useSessionStore } from "../state/sessionStore";

function Chip({ label, variant }: { label: string; variant: "primary" | "accent" | "neutral" }) {
  return (
    <View style={[styles.chip, variant === "primary" && styles.chipPrimary, variant === "accent" && styles.chipAccent]}>
      <Text style={styles.chipText} numberOfLines={2}>
        {label}
      </Text>
    </View>
  );
}

function JustificationVisual({ justification }: { justification: RecommendationJustification }) {
  const { liked_titles, matched_genres, matched_keywords } = justification;
  const hasLiked = liked_titles.length > 0;
  const hasGenres = matched_genres.length > 0;
  const hasKeywords = matched_keywords.length > 0;
  if (!hasLiked && !hasGenres && !hasKeywords) {
    return null;
  }
  return (
    <View style={styles.visualBlock}>
      {hasLiked ? (
        <View style={styles.visualSection}>
          <Text style={styles.visualLabel}>Because you liked</Text>
          <View style={styles.chipRow}>
            {liked_titles.map((t) => (
              <Chip key={t} label={t} variant="primary" />
            ))}
          </View>
        </View>
      ) : null}
      {hasGenres ? (
        <View style={styles.visualSection}>
          <Text style={styles.visualLabel}>Shared genres</Text>
          <View style={styles.chipRow}>
            {matched_genres.map((g) => (
              <Chip key={g} label={g} variant="accent" />
            ))}
          </View>
        </View>
      ) : null}
      {hasKeywords ? (
        <View style={styles.visualSection}>
          <Text style={styles.visualLabel}>Themes in common</Text>
          <View style={styles.chipRow}>
            {matched_keywords.map((k) => (
              <Chip key={k} label={k} variant="neutral" />
            ))}
          </View>
        </View>
      ) : null}
    </View>
  );
}

export function MatchScreen({ navigation }: { navigation: any }) {
  const sessionId = useSessionStore((s) => s.sessionId);
  const reset = useSessionStore((s) => s.reset);

  const [isLoading, setIsLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [data, setData] = React.useState<Awaited<ReturnType<typeof api.getRecommendation>> | null>(null);

  const load = React.useCallback(async () => {
    if (!sessionId) return;
    setIsLoading(true);
    setError(null);
    try {
      const r = await api.getRecommendation(sessionId);
      setData(r);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unknown error");
    } finally {
      setIsLoading(false);
    }
  }, [sessionId]);

  React.useEffect(() => {
    void load();
  }, [load]);

  return (
    <SafeAreaView style={styles.safe}>
      <ScrollView contentContainerStyle={styles.container}>
        <Text style={styles.h1}>Your match</Text>

        {!sessionId ? (
          <View style={styles.panel}>
            <Text style={styles.text}>No session yet.</Text>
            <Button label="Start over" onPress={() => navigation.navigate("Filters")} />
          </View>
        ) : isLoading ? (
          <View style={styles.panel}>
            <Text style={styles.text}>Computing recommendation...</Text>
          </View>
        ) : error ? (
          <View style={styles.panel}>
            <Text style={styles.error}>{error}</Text>
            <Button label="Try again" onPress={load} />
          </View>
        ) : data ? (
          <>
            <Card item={data.recommendation} />
            <View style={styles.panel}>
              <Text style={styles.sectionTitle}>Why this?</Text>
              <Text style={styles.text}>{data.justification.reason}</Text>
              <JustificationVisual justification={data.justification} />

              {!!data.where_to_watch?.length && (
                <>
                  <Text style={[styles.sectionTitle, { marginTop: 12 }]}>Where to watch</Text>
                  <Text style={styles.text}>{data.where_to_watch.join(", ")}</Text>
                </>
              )}

              <Text style={styles.small}>
                Similarity score: {Number.isFinite(data.score) ? data.score.toFixed(3) : "—"}
              </Text>
            </View>

            <View style={styles.row}>
              <Button
                label="Keep swiping"
                onPress={() => navigation.navigate("Swipe")}
                variant="ghost"
                style={{ flex: 1 }}
              />
              <View style={{ width: 12 }} />
              <Button
                label="New session"
                onPress={() => {
                  reset();
                  navigation.navigate("Filters");
                }}
                style={{ flex: 1 }}
              />
            </View>
          </>
        ) : (
          <View style={styles.panel}>
            <Text style={styles.text}>No recommendation yet.</Text>
            <Button label="Try again" onPress={load} />
          </View>
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: colors.bg },
  container: { padding: 16, gap: 12 },
  h1: { color: colors.text, fontSize: 28, fontWeight: "900" },
  panel: {
    backgroundColor: colors.card,
    borderRadius: 18,
    borderWidth: 1,
    borderColor: colors.border,
    padding: 16,
    gap: 10,
  },
  sectionTitle: { color: colors.text, fontSize: 14, fontWeight: "900", letterSpacing: 0.5 },
  text: { color: colors.text, opacity: 0.9, lineHeight: 20 },
  visualBlock: { marginTop: 14, gap: 14 },
  visualSection: { gap: 8 },
  visualLabel: { color: colors.muted, fontSize: 11, fontWeight: "800", letterSpacing: 0.8, textTransform: "uppercase" },
  chipRow: { flexDirection: "row", flexWrap: "wrap", gap: 8 },
  chip: {
    paddingVertical: 6,
    paddingHorizontal: 12,
    borderRadius: 999,
    backgroundColor: "rgba(255,255,255,0.06)",
    borderWidth: 1,
    borderColor: colors.border,
    maxWidth: "100%",
  },
  chipPrimary: {
    backgroundColor: "rgba(124, 92, 255, 0.2)",
    borderColor: "rgba(124, 92, 255, 0.45)",
  },
  chipAccent: {
    backgroundColor: "rgba(46, 229, 157, 0.12)",
    borderColor: "rgba(46, 229, 157, 0.35)",
  },
  chipText: { color: colors.text, fontSize: 13, fontWeight: "600" },
  small: { color: colors.muted, fontSize: 12, marginTop: 10 },
  error: { color: colors.danger, fontWeight: "700" },
  row: { flexDirection: "row" },
});

