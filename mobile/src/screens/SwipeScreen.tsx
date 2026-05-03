import * as React from "react";
import { SafeAreaView, StyleSheet, Text, View } from "react-native";

import { Button } from "../components/Button";
import { SwipeDeck } from "../components/SwipeDeck";
import { colors } from "../theme/colors";
import { useSessionStore } from "../state/sessionStore";

export function SwipeScreen({ navigation }: { navigation: any }) {
  const feed = useSessionStore((s) => s.feed);
  const isLoading = useSessionStore((s) => s.isLoading);
  const error = useSessionStore((s) => s.error);
  const swipe = useSessionStore((s) => s.swipe);
  const loadMore = useSessionStore((s) => s.loadMore);
  const sessionId = useSessionStore((s) => s.sessionId);
  const swiped = useSessionStore((s) => s.swiped);

  const current = feed[0] ?? null;
  const rightCount = Object.values(swiped).filter((d) => d === "right").length;
  const lastAutoMatchRef = useSessionStore((s) => s.autoMatchCount);;

  React.useEffect(() => {
    if (rightCount > 0 && rightCount % 10 === 0 && rightCount !== lastAutoMatchRef) {
      useSessionStore.setState({ autoMatchCount: rightCount });
      navigation.navigate("Match");
    }
  }, [rightCount, navigation]);

  React.useEffect(() => {
    if (sessionId && feed.length < 5 && !isLoading) void loadMore();
  }, [sessionId, feed.length, isLoading, loadMore]);

  return (
    <SafeAreaView style={styles.safe}>
      <View style={styles.container}>
        <View style={styles.header}>
          <Text style={styles.h1}>Swipe</Text>
          <Button label="Match" onPress={() => navigation.navigate("Match")} variant="ghost" />
        </View>

        {!!error && <Text style={styles.error}>{error}</Text>}

        <View style={styles.deck}>
          {current ? (
            <SwipeDeck
              item={current}
              onSwipe={async (direction, item) => {
                await swipe(item.item_id, direction);
              }}
            />
          ) : (
            <View style={styles.empty}>
              <Text style={styles.emptyTitle}>{isLoading ? "Loading..." : "No more items"}</Text>
              <Text style={styles.emptyText}>Try starting a new session or loosening filters.</Text>
            </View>
          )}
        </View>

        <View style={styles.actions}>
          <Button
            label="Nope"
            variant="danger"
            onPress={async () => {
              if (!current) return;
              await swipe(current.item_id, "left");
            }}
            disabled={!current}
            style={{ flex: 1 }}
          />
          <View style={{ width: 12 }} />
          <Button
            label="Like"
            onPress={async () => {
              if (!current) return;
              await swipe(current.item_id, "right");
            }}
            disabled={!current}
            style={{ flex: 1 }}
          />
        </View>

        <Button
          label={isLoading ? "Loading..." : "Load more"}
          onPress={() => loadMore()}
          variant="ghost"
          disabled={!sessionId || isLoading}
        />
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: colors.bg },
  container: { flex: 1, padding: 16, gap: 12 },
  header: { flexDirection: "row", justifyContent: "space-between", alignItems: "center" },
  h1: { color: colors.text, fontSize: 28, fontWeight: "900" },
  deck: { flex: 1, justifyContent: "center" },
  actions: { flexDirection: "row" },
  empty: {
    borderWidth: 1,
    borderColor: colors.border,
    backgroundColor: colors.card,
    borderRadius: 18,
    padding: 18,
    gap: 8,
  },
  emptyTitle: { color: colors.text, fontWeight: "900", fontSize: 18 },
  emptyText: { color: colors.muted, lineHeight: 18 },
  error: { color: colors.danger, fontWeight: "700" },
});

